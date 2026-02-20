from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class BookmarkBase(BaseModel):
    student_id: str
    question_id: str
    notes: Optional[str] = None

class BookmarkCreate(BookmarkBase):
    pass

class Bookmark(BookmarkBase):
    bookmark_id: str
    created_at: datetime

    class Config:
        from_attributes = True
