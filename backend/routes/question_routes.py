"""Question bank endpoints: samples (public), single-question creator (admin), option images (Part 6)."""
import json
from typing import Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config.database import get_pool
from middleware.auth import get_current_teacher
from services.pg_utils import short_id, json_safe

router = APIRouter(prefix="/questions", tags=["questions"])


class OptionData(BaseModel):
    text: Optional[str] = ""
    imageUrl: Optional[str] = ""


class SingleQuestionCreate(BaseModel):
    exam_type: str = "JEE Main"
    subject: str
    chapter: Optional[str] = ""
    topic: Optional[str] = ""
    year: Optional[int] = None
    difficulty: Optional[str] = "medium"
    question_text: str
    question_image_url: Optional[str] = ""
    question_type: Optional[str] = "MCQ_Single"
    # options: {"A":{"text":"..","imageUrl":".."}, "B":..., "C":..., "D":...}
    options: Dict[str, OptionData]
    correct_answers: list[str] = Field(default_factory=list)
    marks: int = 4
    negative_marks: int = -1
    explanation: Optional[str] = ""
    is_sample: bool = False


@router.get("/samples")
async def list_samples():
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM questions WHERE is_sample = true ORDER BY created_at DESC LIMIT 20"
        )
    return {"success": True, "questions": [json_safe(r) for r in rows]}


@router.post("/single")
async def create_single(payload: SingleQuestionCreate, user=Depends(get_current_teacher)):
    q_id = short_id("q")
    options_json = {k: v.dict() for k, v in payload.options.items()}
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO questions (question_id, exam_type, subject, chapter, topic, year, difficulty,
                question_text, question_image_url, question_type, options, correct_answers,
                marks, negative_marks, explanation, is_sample, created_by)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11::jsonb,$12,$13,$14,$15,$16,$17)
            RETURNING *
            """,
            q_id, payload.exam_type, payload.subject, payload.chapter, payload.topic,
            payload.year, payload.difficulty, payload.question_text, payload.question_image_url,
            payload.question_type, json.dumps(options_json), payload.correct_answers,
            payload.marks, payload.negative_marks, payload.explanation, payload.is_sample, user["name"],
        )
    return {"success": True, "question": json_safe(row)}


@router.get("/")
async def list_questions(subject: Optional[str] = None, chapter: Optional[str] = None,
                         user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        if subject and chapter:
            rows = await conn.fetch("SELECT * FROM questions WHERE subject = $1 AND chapter = $2 ORDER BY created_at DESC LIMIT 200",
                                    subject, chapter)
        elif subject:
            rows = await conn.fetch("SELECT * FROM questions WHERE subject = $1 ORDER BY created_at DESC LIMIT 200", subject)
        else:
            rows = await conn.fetch("SELECT * FROM questions ORDER BY created_at DESC LIMIT 200")
    return {"success": True, "questions": [json_safe(r) for r in rows]}


@router.delete("/{question_id}")
async def delete_question(question_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM questions WHERE question_id = $1", question_id)
    return {"success": True}
