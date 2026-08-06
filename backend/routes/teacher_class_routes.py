"""Teacher-side classes CRUD (schedule + list + delete)."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config.database import get_pool
from middleware.auth import get_current_teacher
from services.pg_utils import short_id, json_safe, now_iso
from services.push_service import notify_students_about_class

router = APIRouter(prefix="/teacher/classes", tags=["teacher-classes"])


class ClassCreateRequest(BaseModel):
    title: str
    subject: str
    chapter: Optional[str] = ""
    topic: Optional[str] = ""
    description: Optional[str] = ""
    prerequisites: Optional[str] = ""
    scheduled_date: str
    scheduled_time: str
    duration: int = Field(60, ge=15, le=480)
    meeting_link: Optional[str] = ""
    meeting_platform: Optional[str] = "Zoom"
    assigned_batches: List[str]


@router.post("/create")
async def create_class(payload: ClassCreateRequest, user=Depends(get_current_teacher)):
    batches = [b.strip().upper() for b in payload.assigned_batches if b.strip()]
    if not batches:
        raise HTTPException(status_code=400, detail="At least one batch must be assigned")
    try:
        scheduled_dt = datetime.fromisoformat(f"{payload.scheduled_date}T{payload.scheduled_time}:00")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date/time")

    class_id = short_id("class")
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO classes (class_id, title, subject, chapter, topic, teacher_id, teacher_name, teacher_photo,
                meeting_link, meeting_platform, scheduled_date_time, duration, description, prerequisites,
                assigned_batches, status)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,'upcoming')
            RETURNING *
            """,
            class_id, payload.title, payload.subject, payload.chapter, payload.topic,
            user["user_id"], user["name"], user.get("profile_pic"),
            payload.meeting_link, payload.meeting_platform, scheduled_dt,
            payload.duration, payload.description, payload.prerequisites, batches,
        )

    # In-app notifications for batch students
    try:
        await notify_students_about_class(json_safe(row))
    except Exception:
        pass
    return {"success": True, "class": json_safe(row), "message": "Class scheduled"}


@router.get("/my-classes")
async def my_classes(user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM classes WHERE teacher_id = $1 ORDER BY scheduled_date_time DESC",
            user["user_id"],
        )
    return {"success": True, "classes": [json_safe(r) for r in rows]}


@router.delete("/{class_id}")
async def delete_class(class_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        cls = await conn.fetchrow("SELECT teacher_id FROM classes WHERE class_id = $1", class_id)
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        if str(cls["teacher_id"]) != str(user["user_id"]) and user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Not the teacher of this class")
        await conn.execute("DELETE FROM classes WHERE class_id = $1", class_id)
    return {"success": True, "message": "Class deleted"}


@router.get("/stats/summary")
async def stats(user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT count(*) FROM classes WHERE teacher_id = $1", user["user_id"])
        upcoming = await conn.fetchval(
            "SELECT count(*) FROM classes WHERE teacher_id = $1 AND scheduled_date_time > NOW()",
            user["user_id"],
        )
    return {"total": total or 0, "upcoming": upcoming or 0, "completed": (total or 0) - (upcoming or 0)}
