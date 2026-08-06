"""Teacher-side tests: create, list, delete, assign to batches."""
import json
from datetime import datetime
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config.database import get_pool
from middleware.auth import get_current_teacher
from services.push_service import notify_students_about_test
from services.pg_utils import short_id, json_safe

router = APIRouter(prefix="/teacher/tests", tags=["teacher-tests"])


class TestCreateRequest(BaseModel):
    test_name: str
    subject: str
    test_type: Optional[str] = "chapter"
    exam_type: Optional[str] = "JEE Main"
    test_pattern: Optional[str] = "custom"
    chapters: Optional[List[str]] = []
    topics: Optional[List[str]] = []
    scheduled_date: Optional[str] = None
    scheduled_time: Optional[str] = None
    duration: int = Field(60, ge=15, le=480)
    total_questions: int = 0
    total_marks: int = 0
    instructions: Optional[str] = ""
    assigned_batches: List[str]
    questions: List[Any] = []
    status: Optional[str] = "scheduled"


@router.post("/create")
async def create_test(payload: TestCreateRequest, user=Depends(get_current_teacher)):
    batches = [b.strip().upper() for b in payload.assigned_batches if b.strip()]
    if not batches:
        raise HTTPException(status_code=400, detail="At least one batch is required")
    scheduled_dt = None
    if payload.scheduled_date and payload.scheduled_time:
        try:
            scheduled_dt = datetime.fromisoformat(f"{payload.scheduled_date}T{payload.scheduled_time}:00")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid scheduled date/time")

    test_id = short_id("test")
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO tests (test_id, test_name, exam_type, test_pattern, subject, test_type,
                chapters, topics, scheduled_date_time, duration, total_questions, total_marks,
                instructions, assigned_batches, created_by_id, created_by, questions, status)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17::jsonb,$18)
            RETURNING *
            """,
            test_id, payload.test_name, payload.exam_type, payload.test_pattern,
            payload.subject, payload.test_type, payload.chapters, payload.topics,
            scheduled_dt, payload.duration, payload.total_questions, payload.total_marks,
            payload.instructions, batches, user["user_id"], user["name"],
            json.dumps(payload.questions), payload.status,
        )
    doc = json_safe(row)
    try:
        await notify_students_about_test(doc)
    except Exception:
        pass
    return {"success": True, "test": doc, "message": "Test created"}


@router.get("/my-tests")
async def my_tests(user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM tests WHERE created_by_id = $1 ORDER BY created_at DESC",
            user["user_id"],
        )
    return {"success": True, "tests": [json_safe(r) for r in rows]}


@router.delete("/{test_id}")
async def delete_test(test_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        t = await conn.fetchrow("SELECT created_by_id FROM tests WHERE test_id = $1", test_id)
        if not t:
            raise HTTPException(status_code=404, detail="Test not found")
        if user["role"] != "admin" and str(t["created_by_id"]) != str(user["user_id"]):
            raise HTTPException(status_code=403, detail="Not the creator")
        await conn.execute("DELETE FROM tests WHERE test_id = $1", test_id)
    return {"success": True}
