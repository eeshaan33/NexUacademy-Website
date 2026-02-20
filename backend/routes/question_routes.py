from fastapi import APIRouter, HTTPException, status, Query, Request, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from models.question import QuestionCreate, Question
from middleware.auth import get_current_user, get_current_teacher
from config.syllabus import JEE_SYLLABUS
from config.database import get_database

router = APIRouter(prefix="/questions", tags=["questions"])

@router.post("/", response_model=Question)
async def create_question(
    question_data: QuestionCreate,
    request: Request
):
    """
    Create a new question (teacher only).
    """
    db = get_database()
    user = await get_current_teacher(request)
    db = get_database()
    
    question_id = f"q_{uuid.uuid4().hex[:12]}"
    question_doc = question_data.model_dump()
    question_doc.update({
        "question_id": question_id,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc)
    })
    
    await db.questions.insert_one(question_doc)
    question_doc.pop("_id", None)
    
    return question_doc

@router.get("/")
async def get_questions(
    exam_type: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    chapter: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    difficulty: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    request: Request = None
):
    """
    Get questions with filters.
    """
    # Build filter query
    filter_query = {}
    if exam_type:
        filter_query["exam_type"] = exam_type
    if subject:
        filter_query["subject"] = subject
    if chapter:
        filter_query["chapter"] = chapter
    if topic:
        filter_query["topic"] = topic
    if year:
        filter_query["year"] = year
    if difficulty:
        filter_query["difficulty"] = difficulty
    
    # Get total count
    total = await db.questions.count_documents(filter_query)
    
    # Get questions with pagination
    skip = (page - 1) * limit
    questions = await db.questions.find(
        filter_query,
        {"_id": 0}
    ).skip(skip).limit(limit).to_list(length=limit)
    
    return {
        "questions": questions,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }

@router.get("/syllabus")
async def get_syllabus():
    """
    Get complete JEE syllabus.
    """
    db = get_database()
    return JEE_SYLLABUS

@router.get("/syllabus/{subject}")
async def get_subject_syllabus(subject: str):
    """
    Get syllabus for a specific subject.
    """
    db = get_database()
    if subject not in JEE_SYLLABUS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return {subject: JEE_SYLLABUS[subject]}

@router.get("/chapters/{subject}")
async def get_chapters(subject: str, class_level: Optional[str] = Query(None)):
    """
    Get chapters for a subject.
    """
    if subject not in JEE_SYLLABUS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    if class_level:
        if class_level not in ["Class11", "Class12"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="class_level must be Class11 or Class12"
            )
        return {class_level: JEE_SYLLABUS[subject][class_level]}
    
    return JEE_SYLLABUS[subject]

@router.get("/{question_id}")
async def get_question(question_id: str):
    """
    Get a single question by ID.
    """
    db = get_database()
    question = await db.questions.find_one(
        {"question_id": question_id},
        {"_id": 0}
    )
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return question

@router.delete("/{question_id}")
async def delete_question(question_id: str, request: Request):
    """
    Delete a question (teacher only).
    """
    db = get_database()
    user = await get_current_teacher(request)
    
    result = await db.questions.delete_one({"question_id": question_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    return {"message": "Question deleted successfully"}
