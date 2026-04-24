from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid

from config.database import get_database
from middleware.auth import get_current_user

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


class BookmarkSnapshot(BaseModel):
    """Self-contained snapshot so a bookmark always renders, even if the source question changes."""
    question_text: Optional[str] = None
    question_image_url: Optional[str] = None
    question_type: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    correct_answers: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    numerical_answer: Optional[Any] = None
    subject: Optional[str] = None
    chapter: Optional[str] = None
    topic: Optional[str] = None
    year: Optional[int] = None
    difficulty: Optional[str] = None


class BookmarkCreateRequest(BaseModel):
    source: str = "pyq"  # "pyq" or "test_attempt"
    question_id: Optional[str] = None
    test_id: Optional[str] = None
    attempt_id: Optional[str] = None
    question_number: Optional[int] = None
    snapshot: Optional[BookmarkSnapshot] = None
    notes: Optional[str] = None


def _match_filter(payload: BookmarkCreateRequest, student_id: str) -> dict:
    """Dedupe filter — one bookmark per (student, question source)."""
    base = {"student_id": student_id}
    if payload.source == "test_attempt":
        base.update({
            "source": "test_attempt",
            "test_id": payload.test_id,
            "question_number": payload.question_number,
        })
    else:
        base.update({
            "source": "pyq",
            "question_id": payload.question_id,
        })
    return base


@router.post("/")
async def create_bookmark(payload: BookmarkCreateRequest, user=Depends(get_current_user)):
    db = get_database()

    if payload.source == "test_attempt":
        if not payload.test_id or payload.question_number is None:
            raise HTTPException(status_code=400, detail="test_id and question_number are required for test_attempt bookmarks")
    else:
        if not payload.question_id:
            raise HTTPException(status_code=400, detail="question_id is required for pyq bookmarks")

    existing = await db.bookmarks.find_one(_match_filter(payload, user["user_id"]))
    if existing:
        raise HTTPException(status_code=400, detail="Already bookmarked")

    doc = {
        "bookmark_id": f"bm_{uuid.uuid4().hex[:12]}",
        "student_id": user["user_id"],
        "source": payload.source,
        "question_id": payload.question_id,
        "test_id": payload.test_id,
        "attempt_id": payload.attempt_id,
        "question_number": payload.question_number,
        "snapshot": payload.snapshot.model_dump() if payload.snapshot else None,
        "notes": payload.notes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.bookmarks.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "bookmark": doc}


@router.delete("/by-question")
async def delete_bookmark_by_question(
    source: str,
    question_id: Optional[str] = None,
    test_id: Optional[str] = None,
    question_number: Optional[int] = None,
    user=Depends(get_current_user),
):
    """Delete via question reference — lets the UI toggle without tracking bookmark_id."""
    db = get_database()
    q = {"student_id": user["user_id"], "source": source}
    if source == "test_attempt":
        q.update({"test_id": test_id, "question_number": question_number})
    else:
        q.update({"question_id": question_id})

    res = await db.bookmarks.delete_one(q)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"success": True, "message": "Bookmark removed"}


@router.get("/")
async def list_bookmarks(user=Depends(get_current_user)):
    db = get_database()
    bookmarks = await db.bookmarks.find(
        {"student_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=500)

    # Enrich "pyq" bookmarks that don't have a snapshot by looking up db.questions
    pyq_ids = [b["question_id"] for b in bookmarks if b.get("source") == "pyq" and not b.get("snapshot") and b.get("question_id")]
    q_map = {}
    if pyq_ids:
        qs = await db.questions.find(
            {"question_id": {"$in": pyq_ids}}, {"_id": 0}
        ).to_list(length=None)
        q_map = {q["question_id"]: q for q in qs}

    for b in bookmarks:
        if not b.get("snapshot"):
            if b.get("source") == "pyq":
                q = q_map.get(b.get("question_id"))
                b["snapshot"] = q if q else None

    return {"bookmarks": bookmarks}


@router.get("/ids")
async def my_bookmarked_ids(user=Depends(get_current_user)):
    """Return compact lookup sets for the current user — used by FE to render toggle states."""
    db = get_database()
    cursor = db.bookmarks.find(
        {"student_id": user["user_id"]},
        {"_id": 0, "source": 1, "question_id": 1, "test_id": 1, "question_number": 1},
    )
    pyq_ids = []
    test_keys = []
    async for b in cursor:
        if b.get("source") == "test_attempt":
            test_keys.append(f"{b.get('test_id')}::{b.get('question_number')}")
        elif b.get("question_id"):
            pyq_ids.append(b["question_id"])
    return {"pyq_question_ids": pyq_ids, "test_question_keys": test_keys}


@router.delete("/{bookmark_id}")
async def delete_bookmark(bookmark_id: str, user=Depends(get_current_user)):
    db = get_database()
    res = await db.bookmarks.delete_one({"bookmark_id": bookmark_id, "student_id": user["user_id"]})
    if res.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bookmark not found")
    return {"success": True, "message": "Bookmark deleted"}
