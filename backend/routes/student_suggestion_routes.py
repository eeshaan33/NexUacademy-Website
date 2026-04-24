"""Student-facing suggestion submission & history."""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

from config.database import get_database
from middleware.auth import get_current_user
from models.requests import SuggestionCreateRequest

router = APIRouter(prefix="/student/suggestions", tags=["student-suggestions"])


@router.post("/")
async def create_suggestion(payload: SuggestionCreateRequest, user=Depends(get_current_user)):
    db = get_database()
    suggestion_id = f"sug_{uuid.uuid4().hex[:12]}"
    doc = {
        "suggestion_id": suggestion_id,
        "student_id": user["user_id"],
        "student_name": user.get("name"),
        "student_email": user.get("email"),
        "suggestion_type": payload.suggestion_type,
        "subject": payload.subject,
        "message": payload.message,
        "category": payload.category,
        "tags": payload.tags,
        "screenshot": payload.screenshot,
        "priority": "Medium",
        "status": "New",
        "admin_notes": "",
        "is_read": False,
        "upvotes": 0,
        "upvoted_by": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.student_suggestions.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True,
            "message": "Suggestion submitted! We'll review it soon.",
            "suggestion": doc}


@router.get("/")
async def my_suggestions(user=Depends(get_current_user)):
    db = get_database()
    rows = await db.student_suggestions.find(
        {"student_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=100)
    return {"success": True, "suggestions": rows}


@router.post("/{suggestion_id}/upvote")
async def toggle_upvote(suggestion_id: str, user=Depends(get_current_user)):
    db = get_database()
    s = await db.student_suggestions.find_one({"suggestion_id": suggestion_id})
    if not s:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    uid = user["user_id"]
    upvoted_by = s.get("upvoted_by", [])
    if uid in upvoted_by:
        upvoted_by = [u for u in upvoted_by if u != uid]
        upvotes = max(0, s.get("upvotes", 0) - 1)
    else:
        upvoted_by.append(uid)
        upvotes = s.get("upvotes", 0) + 1

    await db.student_suggestions.update_one(
        {"suggestion_id": suggestion_id},
        {"$set": {"upvoted_by": upvoted_by, "upvotes": upvotes}},
    )
    return {"success": True, "upvotes": upvotes, "upvoted": uid in upvoted_by}
