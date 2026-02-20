from fastapi import APIRouter, HTTPException, status, Request
from config.database import get_database
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from models.bookmark import BookmarkCreate, Bookmark
from middleware.auth import get_current_user

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])

db = get_database()

@router.post("/", response_model=Bookmark)
async def create_bookmark(
    bookmark_data: BookmarkCreate,
    request: Request
):
    """
    Create a bookmark.
    """
    user = await get_current_user(request)
    
    # Check if bookmark already exists
    existing = await db.bookmarks.find_one({
        "student_id": user["user_id"],
        "question_id": bookmark_data.question_id
    })
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question already bookmarked"
        )
    
    bookmark_id = f"bm_{uuid.uuid4().hex[:12]}"
    bookmark_doc = bookmark_data.model_dump()
    bookmark_doc.update({
        "bookmark_id": bookmark_id,
        "student_id": user["user_id"],
        "created_at": datetime.now(timezone.utc)
    })
    
    await db.bookmarks.insert_one(bookmark_doc)
    bookmark_doc.pop("_id", None)
    
    return bookmark_doc

@router.get("/")
async def get_bookmarks(request: Request):
    """
    Get all bookmarks for current user.
    """
    user = await get_current_user(request)
    
    bookmarks = await db.bookmarks.find(
        {"student_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(length=100)
    
    # Get question details for each bookmark
    question_ids = [b["question_id"] for b in bookmarks]
    questions = await db.questions.find(
        {"question_id": {"$in": question_ids}},
        {"_id": 0}
    ).to_list(length=None)
    
    question_map = {q["question_id"]: q for q in questions}
    
    for bookmark in bookmarks:
        bookmark["question_details"] = question_map.get(bookmark["question_id"])
    
    return {"bookmarks": bookmarks}

@router.delete("/{bookmark_id}")
async def delete_bookmark(bookmark_id: str, request: Request):
    """
    Delete a bookmark.
    """
    user = await get_current_user(request)
    
    result = await db.bookmarks.delete_one({
        "bookmark_id": bookmark_id,
        "student_id": user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    return {"message": "Bookmark deleted"}

@router.put("/{bookmark_id}")
async def update_bookmark(
    bookmark_id: str,
    notes: str,
    request: Request
):
    """
    Update bookmark notes.
    """
    user = await get_current_user(request)
    
    result = await db.bookmarks.update_one(
        {"bookmark_id": bookmark_id, "student_id": user["user_id"]},
        {"$set": {"notes": notes}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )
    
    return {"message": "Bookmark updated"}
