from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
from config.database import get_database
from middleware.auth import get_current_user

router = APIRouter(prefix="/student/classes", tags=["student-classes"])


@router.get("/my-classes")
async def get_my_classes(user=Depends(get_current_user)):
    db = get_database()
    batch = user.get("batch_id")
    if not batch:
        return {"success": True, "classes": []}

    classes = await db.classes.find(
        {"assigned_batches": batch}, {"_id": 0}
    ).sort("scheduled_date_time", 1).to_list(length=None)

    return {"success": True, "classes": classes}


@router.post("/{class_id}/attendance")
async def mark_attendance(class_id: str, user=Depends(get_current_user)):
    db = get_database()
    class_doc = await db.classes.find_one({"class_id": class_id})
    if not class_doc:
        raise HTTPException(status_code=404, detail="Class not found")

    attendance = class_doc.get("attendance", [])
    already = any(a.get("student_id") == user["user_id"] for a in attendance)
    if already:
        return {"success": True, "message": "Attendance already marked"}

    attendance.append({
        "student_id": user["user_id"],
        "marked_at": datetime.now(timezone.utc).isoformat(),
    })
    await db.classes.update_one({"class_id": class_id}, {"$set": {"attendance": attendance}})
    return {"success": True, "message": "Attendance marked"}
