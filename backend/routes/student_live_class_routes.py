"""Student live class endpoints — Postgres + Zoom SDK signature."""
import os
from fastapi import APIRouter, HTTPException, Depends

from config.database import get_pool
from middleware.auth import get_current_user
from services.zoom_signature import generate_meeting_signature
from services.pg_utils import json_safe

router = APIRouter(prefix="/student/live-classes", tags=["student-live-classes"])


@router.get("/")
async def list_live_classes(user=Depends(get_current_user)):
    batch = user.get("batch_id")
    if not batch:
        return {"success": True, "classes": []}
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT class_id, title, subject, chapter, topic, teacher_id, teacher_name,
                   meeting_link, meeting_platform, scheduled_date_time, duration,
                   description, assigned_batches,
                   zoom_meeting_id, is_live, live_started_at, live_ended_at, status
            FROM classes
            WHERE $1 = ANY(assigned_batches) AND status != 'cancelled'
            ORDER BY scheduled_date_time ASC
            """,
            batch,
        )
    return {"success": True, "classes": [json_safe(r) for r in rows]}


@router.get("/{class_id}/join")
async def join_live_class(class_id: str, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        cls = await conn.fetchrow("SELECT * FROM classes WHERE class_id = $1", class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if user.get("batch_id") not in (cls["assigned_batches"] or []):
        raise HTTPException(status_code=403, detail="This class is not assigned to your batch")
    if not cls["is_live"]:
        raise HTTPException(status_code=400, detail="Class has not started yet. Please wait for the teacher.")
    if not cls["zoom_meeting_id"]:
        raise HTTPException(status_code=400, detail="This class has no Zoom meeting")

    signature = generate_meeting_signature(cls["zoom_meeting_id"], role=0)
    return {
        "success": True,
        "signature": signature,
        "sdk_key": os.environ.get("ZOOM_SDK_CLIENT_ID", ""),
        "meeting_number": cls["zoom_meeting_id"],
        "password": cls.get("zoom_meeting_password", ""),
        "user_name": user["name"],
        "class_id": class_id,
    }


@router.post("/{class_id}/raise-hand")
async def raise_hand(class_id: str, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        cls = await conn.fetchrow("SELECT assigned_batches FROM classes WHERE class_id = $1", class_id)
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        if user.get("batch_id") not in (cls["assigned_batches"] or []):
            raise HTTPException(status_code=403, detail="Not in your batch")
        await conn.execute(
            """
            INSERT INTO raised_hands (class_id, student_id, student_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (class_id, student_id) DO NOTHING
            """,
            class_id, user["user_id"], user["name"],
        )
        rows = await conn.fetch(
            "SELECT student_id, student_name, raised_at FROM raised_hands WHERE class_id = $1 ORDER BY raised_at",
            class_id,
        )
    return {"success": True, "raised_hands": [
        {"student_id": str(r["student_id"]), "student_name": r["student_name"], "raised_at": r["raised_at"].isoformat()}
        for r in rows
    ]}


@router.post("/{class_id}/lower-hand")
async def lower_hand(class_id: str, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM raised_hands WHERE class_id = $1 AND student_id = $2",
            class_id, user["user_id"],
        )
    return {"success": True}
