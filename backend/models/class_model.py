from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

class ClassBase(BaseModel):
    title: str
    teacher_id: str
    batch_id: str
    meeting_link: str
    scheduled_time: datetime
    description: Optional[str] = None
    recording_url: Optional[str] = None
    notes_url: Optional[str] = None
    status: str = "upcoming"  # upcoming, ongoing, completed

class ClassCreate(ClassBase):
    pass

class Class(ClassBase):
    class_id: str
    attendance: List[str] = []  # list of user_ids
    created_at: datetime

    class Config:
        from_attributes = True
