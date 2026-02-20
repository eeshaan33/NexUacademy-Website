from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime

class QuestionOptions(BaseModel):
    A: str
    B: str
    C: str
    D: str

class QuestionBase(BaseModel):
    exam_type: str  # JEE_Main or JEE_Advanced
    subject: str  # Physics, Chemistry, Mathematics
    chapter: str
    topic: str
    year: int
    difficulty: str = "Medium"  # Easy, Medium, Hard
    question_text: str
    question_image_url: Optional[str] = None
    options: QuestionOptions
    correct_answer: str  # A, B, C, or D
    marks: int = 4
    negative_marks: int = -1
    solution_youtube_url: str
    solution_timestamp: int  # in seconds

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    question_id: str
    created_by: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
