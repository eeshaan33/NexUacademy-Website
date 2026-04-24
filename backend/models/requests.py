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


# ---------- Analytics ----------

class QuestionAttemptRequest(BaseModel):
    question_id: str = Field(..., min_length=1)
    selected_answer: str
    is_correct: bool
    time_taken: int = Field(0, ge=0)


class PageViewRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=200)
    page: Optional[str] = None
    referrer: Optional[str] = ""
    device: Optional[Literal["mobile", "tablet", "desktop", "unknown"]] = "unknown"


# ---------- Custom Test ----------

class TopicConfig(BaseModel):
    subject: Literal["Physics", "Chemistry", "Mathematics"]
    chapter: str
    topic: str
    questionCount: int = Field(..., ge=1, le=50)
    difficulty: Literal["Mixed", "Easy", "Medium", "Hard"] = "Mixed"


class YearRange(BaseModel):
    start: int = Field(..., ge=2000, le=2035)
    end: int = Field(..., ge=2000, le=2035)


class CustomTestCreateRequest(BaseModel):
    examType: Literal["Mixed", "JEE_Main", "JEE_Advanced"]
    selectedTopics: List[TopicConfig] = Field(..., min_length=1)
    yearRange: YearRange
    duration: int = Field(..., ge=5, le=600)
    totalQuestions: int = Field(..., ge=1, le=300)
    totalMarks: int = Field(..., ge=1)


class CustomTestSubmissionRequest(BaseModel):
    answers: Dict[str, Any] = Field(default_factory=dict)
    timeSpent: int = Field(0, ge=0)


class SaveProgressRequest(BaseModel):
    answers: Dict[str, Any] = Field(default_factory=dict)
    current_question: Optional[int] = None


# ---------- Admin Question Import ----------

class BulkQuestionImport(BaseModel):
    exam_type: Literal["JEE_Main", "JEE_Advanced", "NEET"]
    subject: Literal["Physics", "Chemistry", "Mathematics", "Biology"]
    chapter: str = Field(..., min_length=1)
    topic: str
    year: int = Field(..., ge=2000, le=2035)
    difficulty: Literal["Easy", "Medium", "Hard"] = "Medium"
    question_text: str = Field(..., min_length=1)
    question_image_url: Optional[str] = ""
    options: Dict[str, str] = Field(..., description="Keys A/B/C/D")
    correct_answer: Literal["A", "B", "C", "D"]
    marks: int = 4
    negative_marks: int = -1
    solution_youtube_url: Optional[str] = ""
    solution_timestamp: int = 0


class BulkImportRequest(BaseModel):
    questions: List[BulkQuestionImport] = Field(..., min_length=1, max_length=2000)
    replace_existing: bool = False


# ---------- Student Suggestions ----------

class SuggestionCreateRequest(BaseModel):
    suggestion_type: Literal[
        "Feature Request", "Bug Report", "Course Content", "UI/UX", "General", "Other"
    ] = "General"
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    category: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    screenshot: Optional[str] = None


class SuggestionUpdateRequest(BaseModel):
    status: Optional[Literal[
        "New", "In Review", "Planned", "In Progress", "Completed", "Rejected"
    ]] = None
    priority: Optional[Literal["Low", "Medium", "High", "Urgent"]] = None
    admin_notes: Optional[str] = None
    is_read: Optional[bool] = None
