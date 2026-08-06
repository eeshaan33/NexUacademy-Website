"""Student-side tests: list assigned, start attempt (resume), submit."""
import json
from datetime import datetime, timezone
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config.database import get_pool
from middleware.auth import get_current_user
from services.pg_utils import short_id, json_safe

router = APIRouter(prefix="/student/tests", tags=["student-tests"])


@router.get("/assigned")
async def assigned_tests(user=Depends(get_current_user)):
    batch = user.get("batch_id")
    if not batch:
        return {"success": True, "tests": []}
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT t.*,
                   a.attempt_id AS attempt_id,
                   a.status AS attempt_status
            FROM tests t
            LEFT JOIN LATERAL (
                SELECT attempt_id, status FROM test_attempts
                WHERE test_id = t.test_id AND student_id = $2
                ORDER BY started_at DESC LIMIT 1
            ) a ON true
            WHERE $1 = ANY(t.assigned_batches)
            ORDER BY t.scheduled_date_time NULLS LAST, t.created_at DESC
            """,
            batch, user["user_id"],
        )
    return {"success": True, "tests": [json_safe(r) for r in rows]}


class StartTestBody(BaseModel):
    pass  # nothing needed


@router.post("/{test_id}/start")
async def start_test(test_id: str, user=Depends(get_current_user)):
    """Return existing in-progress attempt if any; otherwise create a new one."""
    pool = get_pool()
    async with pool.acquire() as conn:
        test = await conn.fetchrow("SELECT * FROM tests WHERE test_id = $1", test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        if user.get("batch_id") not in (test["assigned_batches"] or []):
            raise HTTPException(status_code=403, detail="Not assigned to your batch")

        existing = await conn.fetchrow(
            """SELECT * FROM test_attempts
               WHERE test_id = $1 AND student_id = $2 AND status = 'in_progress'
               ORDER BY started_at DESC LIMIT 1""",
            test_id, user["user_id"],
        )
        if existing:
            return {"success": True, "attempt": json_safe(existing), "test": json_safe(test), "resumed": True}

        attempt_id = short_id("att")
        row = await conn.fetchrow(
            """
            INSERT INTO test_attempts (attempt_id, test_id, student_id, student_name, status, max_score)
            VALUES ($1, $2, $3, $4, 'in_progress', $5)
            RETURNING *
            """,
            attempt_id, test_id, user["user_id"], user["name"], test["total_marks"] or 0,
        )
    return {"success": True, "attempt": json_safe(row), "test": json_safe(test), "resumed": False}


class SaveAnswersBody(BaseModel):
    saved_answers: List[Any]


@router.post("/attempts/{attempt_id}/save")
async def save_progress(attempt_id: str, body: SaveAnswersBody, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        a = await conn.fetchrow("SELECT student_id FROM test_attempts WHERE attempt_id = $1", attempt_id)
        if not a or str(a["student_id"]) != str(user["user_id"]):
            raise HTTPException(status_code=403, detail="Not your attempt")
        await conn.execute(
            "UPDATE test_attempts SET saved_answers = $1::jsonb WHERE attempt_id = $2",
            json.dumps(body.saved_answers), attempt_id,
        )
    return {"success": True}


class SubmitBody(BaseModel):
    answers: List[Any]
    time_spent: int = 0


@router.post("/attempts/{attempt_id}/submit")
async def submit(attempt_id: str, body: SubmitBody, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        a = await conn.fetchrow("SELECT * FROM test_attempts WHERE attempt_id = $1", attempt_id)
        if not a or str(a["student_id"]) != str(user["user_id"]):
            raise HTTPException(status_code=403, detail="Not your attempt")
        # Score computation (simple: correct answers count)
        correct = sum(1 for ans in body.answers if ans.get("is_correct"))
        total = len(body.answers)
        incorrect = total - correct
        accuracy = round((correct / total) * 100, 2) if total else 0
        await conn.execute(
            """UPDATE test_attempts SET answers = $1::jsonb, time_spent = $2,
               correct_answers = $3, incorrect_answers = $4, accuracy = $5,
               status = 'submitted', submitted_at = NOW()
               WHERE attempt_id = $6""",
            json.dumps(body.answers), body.time_spent, correct, incorrect, accuracy, attempt_id,
        )
        row = await conn.fetchrow("SELECT * FROM test_attempts WHERE attempt_id = $1", attempt_id)
    return {"success": True, "attempt": json_safe(row)}
