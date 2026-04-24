"""Pydantic request schemas for write endpoints.

Kept in one module to avoid scattering models and keep server startup fast.
"""
from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


# ---------- Questions ----------

class QuestionOptionValue(BaseModel):
    text: str = ""
    imageUrl: str = ""


class AnswerRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


QuestionType = Literal["MCQ_Single", "MCQ_Multiple", "Numerical_Integer", "Numerical_Decimal"]


class QuestionAddRequest(BaseModel):
    question_text: str = Field(..., min_length=1)
    question_image_url: str = ""
    question_type: QuestionType = "MCQ_Single"
    # Options are keyed by A/B/C/D. Each value is either a string (legacy) or {text,imageUrl}.
    options: Dict[str, Any] = Field(default_factory=dict)
    correct_answers: List[str] = Field(default_factory=list)
    correct_answer: Optional[str] = None  # legacy fallback
    numerical_answer: Optional[float] = None
    answer_range: Optional[AnswerRange] = None
    marks: int = 4
    negative_marks: int = -1
    subject: str = ""
    chapter: str = ""
    topic: str = ""
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    teacher_note: str = ""

    @field_validator("options", mode="before")
    @classmethod
    def _coerce_options(cls, v):
        # Accept either string options or {text, imageUrl}
        if not isinstance(v, dict):
            return {}
        coerced = {}
        for k, val in v.items():
            if isinstance(val, str):
                coerced[k] = {"text": val, "imageUrl": ""}
            elif isinstance(val, dict):
                coerced[k] = {"text": val.get("text", ""), "imageUrl": val.get("imageUrl", "")}
            else:
                coerced[k] = {"text": "", "imageUrl": ""}
        return coerced


# ---------- Tests ----------

class TestCreateRequest(BaseModel):
    test_name: str = Field(..., min_length=1)
    exam_type: Literal["JEE_Main", "JEE_Advanced", "Practice"]
    test_pattern: Literal["JEE_Main_Pattern", "JEE_Advanced_Pattern"] = "JEE_Main_Pattern"
    subject: str
    test_type: str = "Full Length"
    chapters: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    scheduled_date_time: str
    duration: int = Field(..., gt=0, le=600)
    instructions: str = ""
    allow_reattempts: bool = False
    max_attempts: int = 1
    show_solutions_after_submit: bool = True
    show_results_immediately: bool = True
    randomize_questions: bool = False
    assigned_batches: List[str] = Field(default_factory=list)
    questions: List[QuestionAddRequest] = Field(default_factory=list)


class TestUpdateRequest(BaseModel):
    """Partial update — all fields optional."""
    test_name: Optional[str] = None
    scheduled_date_time: Optional[str] = None
    duration: Optional[int] = Field(None, gt=0, le=600)
    instructions: Optional[str] = None
    allow_reattempts: Optional[bool] = None
    max_attempts: Optional[int] = None
    show_solutions_after_submit: Optional[bool] = None
    show_results_immediately: Optional[bool] = None
    randomize_questions: Optional[bool] = None
    assigned_batches: Optional[List[str]] = None


# ---------- Classes ----------

class ClassCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    subject: Literal["Physics", "Chemistry", "Mathematics", "General"]
    chapter: str = ""
    topic: str = ""
    meeting_link: str = Field(..., min_length=1)
    meeting_platform: str = "Zoom"
    scheduled_date: str
    scheduled_time: str
    duration: int = 60
    description: str = ""
    prerequisites: str = ""
    assigned_batches: List[str]

    @field_validator("duration", mode="before")
    @classmethod
    def _coerce_duration(cls, v):
        try:
            return int(v)
        except (ValueError, TypeError):
            return 60
