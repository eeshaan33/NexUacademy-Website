"""Student-side live class endpoints: list, join (SDK signature), raise/lower hand."""
from datetime import datetime, timezone
import logging
import os

from fastapi import APIRouter, HTTPException, Depends

from config.database import get_database
from middleware.auth import get_current_user
from services.zoom_signature import generate_meeting_signature

router = APIRouter(prefix="/student/live-classes", tags=["student-live-classes"])
logger = logging.getLogger(__name__)


@router.get("/")
async def list_live_classes(user=Depends(get_current_user)):
    """Return classes assigned to student's batch (upcoming + live + recently ended).
    Excludes host-only fields like zoom_start_url."""
    db = get_database()
    batch = user.get("batch_id")
    if not batch:
        return {"success": True, "classes": []}
    classes = await db.classes.find(
        {"assigned_batches": batch, "status": {"$ne": "cancelled"}},
        {"_id": 0, "zoom_start_url": 0},
    ).sort("scheduled_date_time", 1).to_list(length=200)
    return {"success": True, "classes": classes}


@router.get("/{class_id}/join")
async def join_live_class(class_id: str, user=Depends(get_current_user)):
    """Student joins a live class — returns SDK signature (role=0)."""
    db = get_database()
    cls = await db.classes.find_one({"class_id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if user.get("batch_id") not in cls.get("assigned_batches", []):
        raise HTTPException(status_code=403, detail="This class is not assigned to your batch")
    if not cls.get("is_live"):
        raise HTTPException(status_code=400, detail="Class has not started yet. Please wait for the teacher to start.")
    if not cls.get("zoom_meeting_id"):
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
    db = get_database()
    cls = await db.classes.find_one({"class_id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    if user.get("batch_id") not in cls.get("assigned_batches", []):
        raise HTTPException(status_code=403, detail="Not assigned to your batch")

    raised = cls.get("raised_hands", [])
    if not any(h.get("student_id") == user["user_id"] for h in raised):
        raised.append({
            "student_id": user["user_id"],
            "student_name": user["name"],
            "raised_at": datetime.now(timezone.utc).isoformat(),
        })
        await db.classes.update_one({"class_id": class_id}, {"$set": {"raised_hands": raised}})
    return {"success": True, "raised_hands": raised}


@router.post("/{class_id}/lower-hand")
async def lower_hand(class_id: str, user=Depends(get_current_user)):
    db = get_database()
    cls = await db.classes.find_one({"class_id": class_id})
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    raised = [h for h in cls.get("raised_hands", []) if h.get("student_id") != user["user_id"]]
    await db.classes.update_one({"class_id": class_id}, {"$set": {"raised_hands": raised}})
    return {"success": True, "raised_hands": raised}
