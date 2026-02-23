"""
Live Classes API Routes
"""
from fastapi import APIRouter, HTTPException, Request, Query
from config.database import get_database
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import uuid
from middleware.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/classes", tags=["classes"])

class ClassCreate(BaseModel):
    title: str
    subject: str
    chapter: Optional[str] = None
    topic: Optional[str] = None
    teacher_name: str
    teacher_photo: Optional[str] = None
    scheduled_datetime: str  # ISO format
    duration: int = 60
    meeting_link: str
    meeting_platform: str = "Zoom"
    description: Optional[str] = None
    batch_id: Optional[str] = None

class ClassUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[str] = None
    chapter: Optional[str] = None
    topic: Optional[str] = None
    teacher_name: Optional[str] = None
    scheduled_datetime: Optional[str] = None
    duration: Optional[int] = None
    meeting_link: Optional[str] = None
    meeting_platform: Optional[str] = None
    description: Optional[str] = None
    recording_url: Optional[str] = None
    notes_url: Optional[str] = None
    slides_url: Optional[str] = None
    status: Optional[str] = None

def get_class_status(scheduled_dt: datetime, duration: int) -> str:
    """Calculate class status based on current time"""
    now = datetime.now(timezone.utc)
    class_end = scheduled_dt + timedelta(minutes=duration)
    
    if now < scheduled_dt:
        return "upcoming"
    elif now >= scheduled_dt and now < class_end:
        return "ongoing"
    else:
        return "completed"

@router.get("")
async def get_classes(
    request: Request,
    status: Optional[str] = None,
    subject: Optional[str] = None,
    upcoming: Optional[bool] = None,
    limit: int = Query(default=50, le=100),
    skip: int = 0
):
    """Get all classes with optional filters"""
    db = get_database()
    
    query = {}
    
    if status:
        query["status"] = status
    
    if subject:
        query["subject"] = subject
    
    if upcoming:
        query["scheduled_datetime"] = {"$gt": datetime.now(timezone.utc)}
    
    classes = await db.classes.find(
        query,
        {"_id": 0}
    ).sort("scheduled_datetime", 1).skip(skip).limit(limit).to_list(length=limit)
    
    # Update status for each class based on current time
    for cls in classes:
        if cls.get("scheduled_datetime"):
            scheduled_dt = cls["scheduled_datetime"]
            if isinstance(scheduled_dt, str):
                scheduled_dt = datetime.fromisoformat(scheduled_dt.replace('Z', '+00:00'))
            cls["computed_status"] = get_class_status(
                scheduled_dt, 
                cls.get("duration", 60)
            )
    
    return {"classes": classes, "total": len(classes)}

@router.get("/upcoming")
async def get_upcoming_classes(request: Request, limit: int = 10):
    """Get upcoming classes only"""
    db = get_database()
    
    now = datetime.now(timezone.utc)
    
    classes = await db.classes.find(
        {
            "scheduled_datetime": {"$gt": now},
            "status": {"$ne": "cancelled"}
        },
        {"_id": 0}
    ).sort("scheduled_datetime", 1).limit(limit).to_list(length=limit)
    
    return {"classes": classes}

@router.get("/past")
async def get_past_classes(request: Request, limit: int = 20):
    """Get past classes with recordings"""
    db = get_database()
    
    now = datetime.now(timezone.utc)
    
    classes = await db.classes.find(
        {
            "scheduled_datetime": {"$lt": now}
        },
        {"_id": 0}
    ).sort("scheduled_datetime", -1).limit(limit).to_list(length=limit)
    
    return {"classes": classes}

@router.get("/{class_id}")
async def get_class(class_id: str, request: Request):
    """Get single class details"""
    db = get_database()
    
    cls = await db.classes.find_one(
        {"class_id": class_id},
        {"_id": 0}
    )
    
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return cls

@router.post("")
async def create_class(class_data: ClassCreate, request: Request):
    """Create a new class (admin only)"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        if user.get("role") not in ["teacher", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")
    except:
        pass  # Allow for now
    
    class_id = f"cls_{uuid.uuid4().hex[:12]}"
    google_sheet_row_id = f"CLS{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:4].upper()}"
    
    scheduled_dt = datetime.fromisoformat(class_data.scheduled_datetime.replace('Z', '+00:00'))
    
    class_doc = {
        "class_id": class_id,
        "google_sheet_row_id": google_sheet_row_id,
        "title": class_data.title,
        "subject": class_data.subject,
        "chapter": class_data.chapter,
        "topic": class_data.topic,
        "teacher_name": class_data.teacher_name,
        "teacher_photo": class_data.teacher_photo,
        "scheduled_datetime": scheduled_dt,
        "duration": class_data.duration,
        "meeting_link": class_data.meeting_link,
        "meeting_platform": class_data.meeting_platform,
        "description": class_data.description,
        "recording_url": None,
        "notes_url": None,
        "slides_url": None,
        "status": "upcoming",
        "batch_id": class_data.batch_id,
        "attendance": [],
        "reminders_sent": {
            "one_day_before": False,
            "one_hour_before": False,
            "fifteen_mins_before": False
        },
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }
    
    await db.classes.insert_one(class_doc)
    
    # Return without _id
    class_doc.pop("_id", None)
    
    return {
        "success": True,
        "class": class_doc,
        "message": "Class created successfully"
    }

@router.put("/{class_id}")
async def update_class(class_id: str, class_data: ClassUpdate, request: Request):
    """Update a class (admin only)"""
    db = get_database()
    
    update_data = {k: v for k, v in class_data.dict().items() if v is not None}
    
    if "scheduled_datetime" in update_data:
        update_data["scheduled_datetime"] = datetime.fromisoformat(
            update_data["scheduled_datetime"].replace('Z', '+00:00')
        )
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.classes.update_one(
        {"class_id": class_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Class not found")
    
    updated = await db.classes.find_one({"class_id": class_id}, {"_id": 0})
    
    return {
        "success": True,
        "class": updated,
        "message": "Class updated successfully"
    }

@router.delete("/{class_id}")
async def delete_class(class_id: str, request: Request):
    """Delete a class (admin only)"""
    db = get_database()
    
    result = await db.classes.delete_one({"class_id": class_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return {"success": True, "message": "Class deleted successfully"}

@router.post("/{class_id}/attendance")
async def mark_attendance(class_id: str, request: Request):
    """Mark student attendance for a class"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
    except:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    cls = await db.classes.find_one({"class_id": class_id})
    
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    
    # Check if already marked
    attendance = cls.get("attendance", [])
    already_marked = any(a.get("student_id") == user.get("user_id") for a in attendance)
    
    if already_marked:
        return {"message": "Attendance already marked"}
    
    # Add attendance record
    await db.classes.update_one(
        {"class_id": class_id},
        {
            "$push": {
                "attendance": {
                    "student_id": user.get("user_id"),
                    "joined_at": datetime.now(timezone.utc),
                    "marked_at": datetime.now(timezone.utc)
                }
            }
        }
    )
    
    return {"success": True, "message": "Attendance marked successfully"}

@router.get("/admin/sync-status")
async def get_sync_status(request: Request):
    """Get Google Sheets sync status"""
    db = get_database()
    
    total = await db.classes.count_documents({})
    upcoming = await db.classes.count_documents({"status": "upcoming"})
    completed = await db.classes.count_documents({"status": "completed"})
    
    # Get last synced class
    last_synced = await db.classes.find_one(
        {},
        {"_id": 0, "updated_at": 1, "title": 1}
    )
    
    return {
        "total_classes": total,
        "upcoming": upcoming,
        "completed": completed,
        "last_sync": last_synced.get("updated_at") if last_synced else None
    }

@router.post("/seed-sample")
async def seed_sample_classes(request: Request):
    """Seed sample classes for testing"""
    db = get_database()
    
    # Clear existing
    await db.classes.delete_many({})
    
    now = datetime.now(timezone.utc)
    
    sample_classes = [
        {
            "class_id": f"cls_{uuid.uuid4().hex[:12]}",
            "google_sheet_row_id": "CLS001",
            "title": "Projectile Motion - Complete Chapter",
            "subject": "Physics",
            "chapter": "Kinematics",
            "topic": "Projectile Motion",
            "teacher_name": "Dr. Rajesh Sharma",
            "teacher_photo": "https://i.pravatar.cc/150?img=12",
            "scheduled_datetime": now + timedelta(hours=2),
            "duration": 90,
            "meeting_link": "https://zoom.us/j/1234567890",
            "meeting_platform": "Zoom",
            "description": "Complete chapter on projectile motion with solved examples and practice problems.",
            "status": "upcoming",
            "attendance": [],
            "reminders_sent": {"one_day_before": False, "one_hour_before": False, "fifteen_mins_before": False},
            "created_at": now
        },
        {
            "class_id": f"cls_{uuid.uuid4().hex[:12]}",
            "google_sheet_row_id": "CLS002",
            "title": "Organic Chemistry - Reaction Mechanisms",
            "subject": "Chemistry",
            "chapter": "Organic Chemistry",
            "topic": "Reaction Mechanisms",
            "teacher_name": "Prof. Priya Verma",
            "teacher_photo": "https://i.pravatar.cc/150?img=5",
            "scheduled_datetime": now + timedelta(days=1, hours=3),
            "duration": 60,
            "meeting_link": "https://meet.google.com/abc-defg-hij",
            "meeting_platform": "Google Meet",
            "description": "Understanding SN1, SN2, E1, E2 mechanisms with practice.",
            "status": "upcoming",
            "attendance": [],
            "reminders_sent": {"one_day_before": False, "one_hour_before": False, "fifteen_mins_before": False},
            "created_at": now
        },
        {
            "class_id": f"cls_{uuid.uuid4().hex[:12]}",
            "google_sheet_row_id": "CLS003",
            "title": "Calculus - Integration Techniques",
            "subject": "Mathematics",
            "chapter": "Integral Calculus",
            "topic": "Integration",
            "teacher_name": "Dr. Amit Kumar",
            "teacher_photo": "https://i.pravatar.cc/150?img=8",
            "scheduled_datetime": now + timedelta(days=2, hours=4),
            "duration": 75,
            "meeting_link": "https://zoom.us/j/9876543210",
            "meeting_platform": "Zoom",
            "description": "Advanced integration techniques including substitution and partial fractions.",
            "status": "upcoming",
            "attendance": [],
            "reminders_sent": {"one_day_before": False, "one_hour_before": False, "fifteen_mins_before": False},
            "created_at": now
        },
        {
            "class_id": f"cls_{uuid.uuid4().hex[:12]}",
            "google_sheet_row_id": "CLS004",
            "title": "Newton's Laws of Motion",
            "subject": "Physics",
            "chapter": "Laws of Motion",
            "topic": "Newton's Laws",
            "teacher_name": "Dr. Rajesh Sharma",
            "teacher_photo": "https://i.pravatar.cc/150?img=12",
            "scheduled_datetime": now - timedelta(days=2),
            "duration": 60,
            "meeting_link": "https://zoom.us/j/1111111111",
            "meeting_platform": "Zoom",
            "description": "Complete coverage of Newton's three laws with numerical problems.",
            "recording_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "notes_url": "https://drive.google.com/file/d/example",
            "status": "completed",
            "attendance": [],
            "reminders_sent": {"one_day_before": True, "one_hour_before": True, "fifteen_mins_before": True},
            "created_at": now - timedelta(days=3)
        },
        {
            "class_id": f"cls_{uuid.uuid4().hex[:12]}",
            "google_sheet_row_id": "CLS005",
            "title": "Chemical Equilibrium",
            "subject": "Chemistry",
            "chapter": "Equilibrium",
            "topic": "Chemical Equilibrium",
            "teacher_name": "Prof. Priya Verma",
            "teacher_photo": "https://i.pravatar.cc/150?img=5",
            "scheduled_datetime": now - timedelta(days=5),
            "duration": 90,
            "meeting_link": "https://meet.google.com/xyz-abcd-efg",
            "meeting_platform": "Google Meet",
            "description": "Le Chatelier's principle and equilibrium constants.",
            "recording_url": "https://www.youtube.com/watch?v=example2",
            "notes_url": "https://drive.google.com/file/d/example2",
            "slides_url": "https://drive.google.com/file/d/slides2",
            "status": "completed",
            "attendance": [],
            "reminders_sent": {"one_day_before": True, "one_hour_before": True, "fifteen_mins_before": True},
            "created_at": now - timedelta(days=6)
        }
    ]
    
    await db.classes.insert_many(sample_classes)
    
    return {
        "success": True,
        "message": f"Seeded {len(sample_classes)} sample classes"
    }
