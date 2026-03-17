from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
from config.database import get_database
from middleware.auth import get_current_teacher
from services.push_service import notify_students_about_class
import uuid

router = APIRouter(prefix="/teacher/classes", tags=["teacher-classes"])


@router.get("/")
async def get_teacher_classes(user=Depends(get_current_teacher)):
    db = get_database()
    classes = await db.classes.find(
        {"teacher_id": user["user_id"]}, {"_id": 0}
    ).sort("scheduled_date_time", -1).to_list(length=None)
    return {"success": True, "classes": classes}


@router.post("/create")
async def create_class(request: Request, user=Depends(get_current_teacher)):
    db = get_database()
    body = await request.json()

    required = ["title", "subject", "meeting_link", "scheduled_date", "scheduled_time", "assigned_batches"]
    for field in required:
        if not body.get(field):
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    # Parse date and time
    date_str = body["scheduled_date"]
    time_str = body["scheduled_time"]
    scheduled_dt = datetime.fromisoformat(f"{date_str}T{time_str}:00")

    class_id = f"class_{uuid.uuid4().hex[:12]}"
    batches = body["assigned_batches"] if isinstance(body["assigned_batches"], list) else [body["assigned_batches"]]

    class_doc = {
        "class_id": class_id,
        "title": body["title"],
        "subject": body["subject"],
        "chapter": body.get("chapter", ""),
        "topic": body.get("topic", ""),
        "teacher_id": user["user_id"],
        "teacher_name": user["name"],
        "teacher_photo": user.get("profile_pic", ""),
        "meeting_link": body["meeting_link"],
        "meeting_platform": body.get("meeting_platform", "Zoom"),
        "scheduled_date_time": scheduled_dt.isoformat(),
        "duration": int(body.get("duration", 60)),
        "description": body.get("description", ""),
        "prerequisites": body.get("prerequisites", ""),
        "assigned_batches": batches,
        "recording_url": "",
        "notes_url": "",
        "slides_url": "",
        "status": "upcoming",
        "attendance": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.classes.insert_one(class_doc)

    # Send notifications
    notified = await notify_students_about_class(class_doc)

    return {
        "success": True,
        "message": f"Class scheduled! {notified} students notified.",
        "class": {k: v for k, v in class_doc.items() if k != "_id"},
    }


@router.put("/{class_id}")
async def update_class(class_id: str, request: Request, user=Depends(get_current_teacher)):
    db = get_database()
    existing = await db.classes.find_one({"class_id": class_id, "teacher_id": user["user_id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Class not found")

    body = await request.json()
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    body.pop("_id", None)
    body.pop("class_id", None)

    await db.classes.update_one({"class_id": class_id}, {"$set": body})
    updated = await db.classes.find_one({"class_id": class_id}, {"_id": 0})
    return {"success": True, "class": updated}


@router.delete("/{class_id}")
async def delete_class(class_id: str, user=Depends(get_current_teacher)):
    db = get_database()
    result = await db.classes.delete_one({"class_id": class_id, "teacher_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"success": True, "message": "Class deleted"}


@router.get("/stats")
async def get_class_stats(user=Depends(get_current_teacher)):
    db = get_database()
    total = await db.classes.count_documents({"teacher_id": user["user_id"]})
    upcoming = await db.classes.count_documents({"teacher_id": user["user_id"], "status": "upcoming"})
    completed = await db.classes.count_documents({"teacher_id": user["user_id"], "status": "completed"})
    return {"success": True, "total": total, "upcoming": upcoming, "completed": completed}
