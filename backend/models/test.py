from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TestBase(BaseModel):
    test_name: str
    exam_type: str  # JEE_Main or JEE_Advanced
    questions: List[str]  # list of question_ids
    total_marks: int
    duration_minutes: int
    scheduled_date_time: Optional[datetime] = None
    is_custom: bool = False
    assigned_to: List[str] = []  # list of user_ids or batch_ids
    status: str = "published"  # draft, published, archived

class TestCreate(TestBase):
    pass

class Test(TestBase):
    test_id: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True

class AnswerSubmission(BaseModel):
    question_id: str
    selected_answer: str  # A, B, C, D
    is_correct: bool
    time_taken: int  # in seconds
    flagged: bool = False

class TestAttemptBase(BaseModel):
    test_id: str
    student_id: str
    answers: List[AnswerSubmission]
    score: int
    total_marks: int
    accuracy: float
    time_spent: int  # in seconds

class TestAttemptCreate(BaseModel):
    test_id: str
    student_id: str

class TestAttempt(TestAttemptBase):
    attempt_id: str
    rank: Optional[int] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
