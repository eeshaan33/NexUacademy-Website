"""Student-side tests: list assigned, start attempt (resume), submit.

Scoring is SERVER-AUTHORITATIVE: the client's `is_correct` field on each
answer is ignored. Correctness is recomputed against `tests.questions`
via `services.scoring.score_attempt`.

Time integrity: submits are rejected when (now - started_at) exceeds the
test's `duration` minutes plus a 60-second grace window. The stale attempt
is auto-closed with status='expired' so it can never be re-submitted.
"""
import json
from datetime import datetime, timezone, timedelta
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config.database import get_pool
from middleware.auth import get_current_user
from services.pg_utils import short_id, json_safe
from services.scoring import score_attempt

# Grace window (seconds) added to `duration` before we hard-reject a submit.
# Absorbs client-timer / network jitter around the boundary.
SUBMIT_GRACE_SECONDS = 60

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


class AutoSaveBody(BaseModel):
    answers: List[Any]


@router.put("/attempts/{attempt_id}/autosave")
async def autosave(attempt_id: str, body: AutoSaveBody, user=Depends(get_current_user)):
    """Periodic in-progress save — mirrors the older `/save` route the JEE
    Main interface calls every 30 s."""
    pool = get_pool()
    async with pool.acquire() as conn:
        a = await conn.fetchrow("SELECT student_id, status FROM test_attempts WHERE attempt_id = $1", attempt_id)
        if not a or str(a["student_id"]) != str(user["user_id"]):
            raise HTTPException(status_code=403, detail="Not your attempt")
        if a["status"] != "in_progress":
            return {"success": True, "skipped": True, "reason": "already submitted"}
        await conn.execute(
            "UPDATE test_attempts SET saved_answers = $1::jsonb WHERE attempt_id = $2",
            json.dumps(body.answers), attempt_id,
        )
    return {"success": True}


class SubmitBody(BaseModel):
    answers: List[Any]
    time_spent: int = 0
    autoSubmitted: bool = False


@router.post("/attempts/{attempt_id}/submit")
async def submit(attempt_id: str, body: SubmitBody, user=Depends(get_current_user)):
    """Submit a test — score is recomputed server-side. `is_correct` from
    the client is DISCARDED. Idempotent: resubmitting a submitted attempt
    returns the already-scored result without re-writing.

    Time-integrity guard: if (now - started_at) > (test.duration + 60 s),
    the attempt is auto-closed with status='expired' and the submit is
    rejected with 400 so a student cannot open a test, wait days, then
    submit a full paper."""
    pool = get_pool()
    async with pool.acquire() as conn:
        a = await conn.fetchrow("SELECT * FROM test_attempts WHERE attempt_id = $1", attempt_id)
        if not a:
            raise HTTPException(status_code=404, detail="Attempt not found")
        if str(a["student_id"]) != str(user["user_id"]):
            raise HTTPException(status_code=403, detail="Not your attempt")
        if a["status"] == "submitted":
            return {"success": True, "attempt": json_safe(a), "resubmitted": False}
        if a["status"] == "expired":
            raise HTTPException(
                status_code=400,
                detail="Test time expired. This attempt was auto-closed and can no longer be submitted.",
            )

        test = await conn.fetchrow("SELECT questions, duration FROM tests WHERE test_id = $1", a["test_id"])
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")

        # --- Time-integrity guard ---
        started_at = a["started_at"]
        if started_at and started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        duration_min = int(test["duration"] or 0)
        if started_at and duration_min > 0:
            deadline = started_at + timedelta(minutes=duration_min, seconds=SUBMIT_GRACE_SECONDS)
            if datetime.now(timezone.utc) > deadline:
                # Auto-close so it can never be submitted again
                await conn.execute(
                    "UPDATE test_attempts SET status='expired', submitted_at=NOW() WHERE attempt_id=$1",
                    attempt_id,
                )
                raise HTTPException(
                    status_code=400,
                    detail="Test time expired. Your attempt has been auto-closed.",
                )

        raw_qs = test["questions"] or []
        if isinstance(raw_qs, str):
            try:
                raw_qs = json.loads(raw_qs)
            except json.JSONDecodeError:
                raw_qs = []
        questions = raw_qs if isinstance(raw_qs, list) else []

        result = score_attempt(questions, body.answers)

        await conn.execute(
            """UPDATE test_attempts
               SET answers = $1::jsonb,
                   time_spent = $2,
                   total_score = $3,
                   max_score = $4,
                   correct_answers = $5,
                   incorrect_answers = $6,
                   unattempted = $7,
                   accuracy = $8,
                   status = 'submitted',
                   submitted_at = NOW()
               WHERE attempt_id = $9""",
            json.dumps(result["authoritative_answers"]),
            body.time_spent,
            result["total_score"],
            result["max_score"],
            result["correct_answers"],
            result["incorrect_answers"],
            result["unattempted"],
            result["accuracy"],
            attempt_id,
        )
        row = await conn.fetchrow("SELECT * FROM test_attempts WHERE attempt_id = $1", attempt_id)
    return {"success": True, "attempt": json_safe(row), "auto_submitted": body.autoSubmitted}
