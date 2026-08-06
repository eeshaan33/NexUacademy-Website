"""Teacher-side live class endpoints.

Extends the existing `classes` collection with Zoom + live-state fields:
  - zoom_meeting_id, zoom_meeting_password, zoom_join_url, zoom_start_url
  - is_live, live_started_at, live_ended_at
  - raised_hands: [{ student_id, student_name, raised_at }]
"""
from datetime import datetime, timezone
from typing import Optional, List
import logging
import uuid

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from config.database import get_database
from middleware.auth import get_current_teacher
from services.push_service import notify_students_about_class
from services.zoom_service import (
    create_meeting as zoom_create_meeting,
    delete_meeting as zoom_delete_meeting,
    get_live_participants as zoom_live_participants,
    get_host_zak,
)
from services.zoom_signature import generate_meeting_signature

router = APIRouter(prefix="/teacher/live-classes", tags=["teacher-live-classes"])
logger = logging.getLogger(__name__)


class LiveClassCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    subject: str
    chapter: Optional[str] = ""
    topic: Optional[str] = ""
    description: Optional[str] = ""
    scheduled_date: str  # YYYY-MM-DD
    scheduled_time: str  # HH:MM
    duration: int = Field(60, ge=15, le=480)
    assigned_batches: List[str]


@router.post("/create")
async def create_live_class(payload: LiveClassCreateRequest, user=Depends(get_current_teacher)):
    db = get_database()

    # Normalise batch IDs (trim + upper safe for codes; batch IDs may contain spaces)
    batches = [b.strip() for b in payload.assigned_batches if b and b.strip()]
    if not batches:
        raise HTTPException(status_code=400, detail="At least one batch must be assigned")

    try:
        scheduled_dt = datetime.fromisoformat(f"{payload.scheduled_date}T{payload.scheduled_time}:00")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid scheduled_date/scheduled_time")

    # Create Zoom meeting
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
        logger.error(f"Zoom create_meeting failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to create Zoom meeting")

    class_id = f"class_{uuid.uuid4().hex[:12]}"
    doc = {
        "class_id": class_id,
        "title": payload.title,
        "subject": payload.subject,
        "chapter": payload.chapter,
        "topic": payload.topic,
        "teacher_id": user["user_id"],
        "teacher_name": user["name"],
        "teacher_photo": user.get("profile_pic", ""),
        "meeting_platform": "Zoom",
        "meeting_link": zm.get("join_url", ""),  # backup web link
        "scheduled_date_time": scheduled_dt.isoformat(),
        "duration": payload.duration,
        "description": payload.description,
        "prerequisites": "",
        "assigned_batches": batches,
        "zoom_meeting_id": str(zm.get("id", "")),
        "zoom_meeting_password": zm.get("password", ""),
        "zoom_join_url": zm.get("join_url", ""),
        "zoom_start_url": zm.get("start_url", ""),  # host-only, never sent to students
        "is_live": False,
        "live_started_at": None,
        "live_ended_at": None,
        "raised_hands": [],
        "status": "upcoming",
        "attendance": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.classes.insert_one(doc)

    # Notify students of scheduled class
    try:
        await notify_students_about_class(doc)
    except Exception as e:
        logger.warning(f"notify_students_about_class failed: {e}")

    # Strip host-only fields before returning
    safe = {k: v for k, v in doc.items() if k not in ("_id", "zoom_start_url")}
    return {"success": True, "message": "Live class scheduled and Zoom meeting created", "class": safe}


@router.post("/{class_id}/start")
async def start_live_class(class_id: str, user=Depends(get_current_teacher)):
    """Teacher clicks 'Start Class' — marks live, returns SDK signature (host)."""
    db = get_database()
    cls = await db.classes.find_one({"class_id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls["teacher_id"] != user["user_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You are not the host of this class")
    if not cls.get("zoom_meeting_id"):
        raise HTTPException(status_code=400, detail="This class has no Zoom meeting attached")

    await db.classes.update_one(
        {"class_id": class_id},
        {"$set": {"is_live": True, "live_started_at": datetime.now(timezone.utc).isoformat(),
                  "status": "live"}},
    )

    signature = generate_meeting_signature(cls["zoom_meeting_id"], role=1)
    zak = await get_host_zak(user.get("email"))

    # Push a "class is LIVE" notification
    try:
        await notify_students_about_class({
            **cls,
            "title": f"🔴 LIVE: {cls['title']}",
            "class_id": class_id,
        })
    except Exception as e:
        logger.warning(f"live-notification failed: {e}")

    return {
        "success": True,
        "signature": signature,
        "sdk_key": (__import__("os").environ.get("ZOOM_SDK_CLIENT_ID", "")),
        "meeting_number": cls["zoom_meeting_id"],
        "password": cls.get("zoom_meeting_password", ""),
        "user_name": user["name"],
        "zak": zak,  # required for host-start via Web SDK
        "start_url": cls.get("zoom_start_url", ""),
    }


@router.post("/{class_id}/end")
async def end_live_class(class_id: str, user=Depends(get_current_teacher)):
    db = get_database()
    cls = await db.classes.find_one({"class_id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls["teacher_id"] != user["user_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not the host")

    await db.classes.update_one(
        {"class_id": class_id},
        {"$set": {"is_live": False, "live_ended_at": datetime.now(timezone.utc).isoformat(),
                  "raised_hands": [], "status": "completed"}},
    )
    return {"success": True, "message": "Class ended"}


@router.get("/{class_id}/participants")
async def get_participants(class_id: str, user=Depends(get_current_teacher)):
    """Poll every 5–10s from teacher UI. Returns Zoom live participants + raised hands."""
    db = get_database()
    cls = await db.classes.find_one({"class_id": class_id}, {"_id": 0})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls["teacher_id"] != user["user_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not the host")

    participants = []
    if cls.get("zoom_meeting_id"):
        participants = await zoom_live_participants(cls["zoom_meeting_id"])

    return {
        "success": True,
        "participants": participants,
        "raised_hands": cls.get("raised_hands", []),
        "is_live": cls.get("is_live", False),
    }


@router.post("/{class_id}/lower-hand/{student_id}")
async def teacher_lower_hand(class_id: str, student_id: str, user=Depends(get_current_teacher)):
    """Teacher acknowledges/lowers a student's raised hand."""
    db = get_database()
    cls = await db.classes.find_one({"class_id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls["teacher_id"] != user["user_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not the host")

    raised = [h for h in cls.get("raised_hands", []) if h.get("student_id") != student_id]
    await db.classes.update_one({"class_id": class_id}, {"$set": {"raised_hands": raised}})
    return {"success": True, "raised_hands": raised}


@router.delete("/{class_id}")
async def delete_live_class(class_id: str, user=Depends(get_current_teacher)):
    db = get_database()
    cls = await db.classes.find_one({"class_id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if cls["teacher_id"] != user["user_id"] and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not the host")

    # Best-effort: cancel the Zoom meeting
    if cls.get("zoom_meeting_id"):
        try:
            await zoom_delete_meeting(cls["zoom_meeting_id"])
        except Exception as e:
            logger.warning(f"Zoom delete failed for {cls['zoom_meeting_id']}: {e}")

    await db.classes.delete_one({"class_id": class_id})
    return {"success": True, "message": "Class deleted"}
