"""Teacher live class endpoints — Postgres + Zoom Meeting SDK."""
from datetime import datetime
from typing import Optional, List
import logging
import os

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from config.database import get_pool
from middleware.auth import get_current_teacher
from services.push_service import notify_students_about_class
from services.zoom_service import (
    create_meeting as zoom_create_meeting,
    delete_meeting as zoom_delete_meeting,
    get_live_participants as zoom_live_participants,
    get_host_zak,
)
from services.zoom_signature import generate_meeting_signature
from services.pg_utils import short_id, json_safe

router = APIRouter(prefix="/teacher/live-classes", tags=["teacher-live-classes"])
logger = logging.getLogger(__name__)


class LiveClassCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    subject: str
    chapter: Optional[str] = ""
    topic: Optional[str] = ""
    description: Optional[str] = ""
    scheduled_date: str
    scheduled_time: str
    duration: int = Field(60, ge=15, le=480)
    assigned_batches: List[str]


@router.post("/create")
async def create_live_class(payload: LiveClassCreateRequest, user=Depends(get_current_teacher)):
    batches = [b.strip().upper() for b in payload.assigned_batches if b.strip()]
    if not batches:
        raise HTTPException(status_code=400, detail="At least one batch must be assigned")
    try:
        scheduled_dt = datetime.fromisoformat(f"{payload.scheduled_date}T{payload.scheduled_time}:00")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scheduled_date/scheduled_time")

    try:
        zm = await zoom_create_meeting(
            topic=payload.title,
            start_time_iso=scheduled_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            duration_min=payload.duration,
            host_email=user.get("email"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Zoom create failed")
        raise HTTPException(status_code=502, detail="Failed to create Zoom meeting")

    class_id = short_id("class")
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO classes (class_id, title, subject, chapter, topic,
                teacher_id, teacher_name, teacher_photo,
                meeting_link, meeting_platform, scheduled_date_time, duration,
                description, prerequisites, assigned_batches,
                zoom_meeting_id, zoom_meeting_password, zoom_join_url, zoom_start_url,
                status, is_live)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,'Zoom',$10,$11,$12,'',$13,$14,$15,$16,$17,'upcoming',false)
            RETURNING *
            """,
            class_id, payload.title, payload.subject, payload.chapter, payload.topic,
            user["user_id"], user["name"], user.get("profile_pic"),
            zm.get("join_url", ""), scheduled_dt, payload.duration, payload.description,
            batches,
            str(zm.get("id", "")), zm.get("password", ""), zm.get("join_url", ""), zm.get("start_url", ""),
        )

    doc = json_safe(row)
    try:
        await notify_students_about_class(doc)
    except Exception:
        pass

    safe = {k: v for k, v in doc.items() if k != "zoom_start_url"}
    return {"success": True, "message": "Live class scheduled", "class": safe}


@router.post("/{class_id}/start")
async def start_live_class(class_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        cls = await conn.fetchrow("SELECT * FROM classes WHERE class_id = $1", class_id)
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        if str(cls["teacher_id"]) != str(user["user_id"]) and user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Not the host")
        if not cls["zoom_meeting_id"]:
            raise HTTPException(status_code=400, detail="This class has no Zoom meeting")
        await conn.execute(
            "UPDATE classes SET is_live = true, live_started_at = NOW(), status = 'live' WHERE class_id = $1",
            class_id,
        )

    signature = generate_meeting_signature(cls["zoom_meeting_id"], role=1)
    zak = await get_host_zak(user.get("email"))
    try:
        await notify_students_about_class({
            **json_safe(cls),
            "title": f"🔴 LIVE: {cls['title']}",
        })
    except Exception:
        pass

    return {
        "success": True,
        "signature": signature,
        "sdk_key": os.environ.get("ZOOM_SDK_CLIENT_ID", ""),
        "meeting_number": cls["zoom_meeting_id"],
        "password": cls.get("zoom_meeting_password", ""),
        "user_name": user["name"],
        "zak": zak,
        "start_url": cls.get("zoom_start_url", ""),
    }


@router.post("/{class_id}/end")
async def end_live_class(class_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        cls = await conn.fetchrow("SELECT teacher_id FROM classes WHERE class_id = $1", class_id)
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        if str(cls["teacher_id"]) != str(user["user_id"]) and user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Not the host")
        await conn.execute(
            "UPDATE classes SET is_live = false, live_ended_at = NOW(), status = 'completed' WHERE class_id = $1",
            class_id,
        )
        await conn.execute("DELETE FROM raised_hands WHERE class_id = $1", class_id)
    return {"success": True, "message": "Class ended"}


@router.get("/{class_id}/participants")
async def get_participants(class_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        cls = await conn.fetchrow("SELECT teacher_id, zoom_meeting_id, is_live FROM classes WHERE class_id = $1", class_id)
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        if str(cls["teacher_id"]) != str(user["user_id"]) and user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Not the host")
        raised = await conn.fetch(
            "SELECT student_id, student_name, raised_at FROM raised_hands WHERE class_id = $1 ORDER BY raised_at ASC",
            class_id,
        )
    participants = []
    if cls["zoom_meeting_id"]:
        participants = await zoom_live_participants(cls["zoom_meeting_id"])
    return {
        "success": True,
        "participants": participants,
        "raised_hands": [{"student_id": str(r["student_id"]), "student_name": r["student_name"],
                          "raised_at": r["raised_at"].isoformat()} for r in raised],
        "is_live": cls["is_live"],
    }


@router.post("/{class_id}/lower-hand/{student_id}")
async def teacher_lower_hand(class_id: str, student_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        cls = await conn.fetchrow("SELECT teacher_id FROM classes WHERE class_id = $1", class_id)
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        if str(cls["teacher_id"]) != str(user["user_id"]) and user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Not the host")
        await conn.execute(
            "DELETE FROM raised_hands WHERE class_id = $1 AND student_id = $2",
            class_id, student_id,
        )
    return {"success": True}


@router.delete("/{class_id}")
async def delete_live_class(class_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        cls = await conn.fetchrow("SELECT teacher_id, zoom_meeting_id FROM classes WHERE class_id = $1", class_id)
        if not cls:
            raise HTTPException(status_code=404, detail="Class not found")
        if str(cls["teacher_id"]) != str(user["user_id"]) and user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Not the host")
        if cls["zoom_meeting_id"]:
            try:
                await zoom_delete_meeting(cls["zoom_meeting_id"])
            except Exception:
                pass
        await conn.execute("DELETE FROM classes WHERE class_id = $1", class_id)
    return {"success": True, "message": "Class deleted"}
