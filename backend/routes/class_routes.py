from fastapi import APIRouter, HTTPException, status, Request
from typing import List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from models.class_model import ClassCreate, Class
from middleware.auth import get_current_user, get_current_teacher

router = APIRouter(prefix="/classes", tags=["classes"])

db = get_database()

@router.post("/", response_model=Class)
async def create_class(
    class_data: ClassCreate,
    request: Request
):
    """
    Create a new class (teacher only).
    """
    user = await get_current_teacher(request)
    
    class_id = f"class_{uuid.uuid4().hex[:12]}"
    class_doc = class_data.model_dump()
    class_doc.update({
        "class_id": class_id,
        "teacher_id": user["user_id"],
        "attendance": [],
        "created_at": datetime.now(timezone.utc)
    })
    
    await db.classes.insert_one(class_doc)
    class_doc.pop("_id", None)
    
    return class_doc

@router.get("/")
async def get_classes(request: Request):
    """
    Get classes for current user's batch.
    """
    user = await get_current_user(request)
    
    filter_query = {}
    if user["role"] == "teacher":
        filter_query["teacher_id"] = user["user_id"]
    elif user.get("batch_id"):
        filter_query["batch_id"] = user["batch_id"]
    else:
        # Student with no batch - return empty
        return {"classes": []}
    
    classes = await db.classes.find(
        filter_query,
        {"_id": 0}
    ).sort("scheduled_time", -1).to_list(length=100)
    
    return {"classes": classes}

@router.get("/upcoming")
async def get_upcoming_classes(request: Request):
    """
    Get upcoming classes.
    """
    user = await get_current_user(request)
    
    filter_query = {
        "scheduled_time": {"$gte": datetime.now(timezone.utc)},
        "status": {"$in": ["upcoming", "ongoing"]}
    }
    
    if user["role"] == "teacher":
        filter_query["teacher_id"] = user["user_id"]
    elif user.get("batch_id"):
        filter_query["batch_id"] = user["batch_id"]
    
    classes = await db.classes.find(
        filter_query,
        {"_id": 0}
    ).sort("scheduled_time", 1).to_list(length=10)
    
    return {"classes": classes}

@router.get("/{class_id}")
async def get_class(class_id: str, request: Request):
    """
    Get class details.
    """
    user = await get_current_user(request)
    
    class_doc = await db.classes.find_one(
        {"class_id": class_id},
        {"_id": 0}
    )
    
    if not class_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    return class_doc

@router.put("/{class_id}")
async def update_class(
    class_id: str,
    update_data: dict,
    request: Request
):
    """
    Update class details (teacher only).
    """
    user = await get_current_teacher(request)
    
    result = await db.classes.update_one(
        {"class_id": class_id, "teacher_id": user["user_id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or unauthorized"
        )
    
    return {"message": "Class updated successfully"}

@router.post("/{class_id}/attendance")
async def mark_attendance(class_id: str, request: Request):
    """
    Mark attendance for a class.
    """
    user = await get_current_user(request)
    
    # Add user to attendance list if not already present
    result = await db.classes.update_one(
        {"class_id": class_id},
        {"$addToSet": {"attendance": user["user_id"]}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    return {"message": "Attendance marked"}
