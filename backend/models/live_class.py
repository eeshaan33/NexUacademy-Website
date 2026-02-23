"""
Live Classes Database Model
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MeetingPlatform(str, Enum):
    ZOOM = "Zoom"
    GOOGLE_MEET = "Google Meet"
    MICROSOFT_TEAMS = "Microsoft Teams"

class ClassStatus(str, Enum):
    UPCOMING = "upcoming"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Subject(str, Enum):
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    MATHEMATICS = "Mathematics"
    GENERAL = "General"

class AttendanceRecord(BaseModel):
    student_id: str
    joined_at: Optional[datetime] = None
    marked_at: Optional[datetime] = None

class RemindersSent(BaseModel):
    one_day_before: bool = False
    one_hour_before: bool = False
    fifteen_mins_before: bool = False

class LiveClass(BaseModel):
    class_id: str
    google_sheet_row_id: str
    title: str
    subject: Subject
    chapter: Optional[str] = None
    topic: Optional[str] = None
    teacher_name: str
    teacher_photo: Optional[str] = None
    scheduled_datetime: datetime
    duration: int = 60  # minutes
    meeting_link: str
    meeting_platform: MeetingPlatform = MeetingPlatform.ZOOM
    description: Optional[str] = None
    recording_url: Optional[str] = None
    notes_url: Optional[str] = None
    slides_url: Optional[str] = None
    status: ClassStatus = ClassStatus.UPCOMING
    batch_id: Optional[str] = None
    attendance: List[AttendanceRecord] = []
    reminders_sent: RemindersSent = Field(default_factory=RemindersSent)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ClassCreate(BaseModel):
    title: str
    subject: Subject
    chapter: Optional[str] = None
    topic: Optional[str] = None
    teacher_name: str
    teacher_photo: Optional[str] = None
    scheduled_datetime: datetime
    duration: int = 60
    meeting_link: str
    meeting_platform: MeetingPlatform = MeetingPlatform.ZOOM
    description: Optional[str] = None
    batch_id: Optional[str] = None

class ClassUpdate(BaseModel):
    title: Optional[str] = None
    subject: Optional[Subject] = None
    chapter: Optional[str] = None
    topic: Optional[str] = None
    teacher_name: Optional[str] = None
    scheduled_datetime: Optional[datetime] = None
    duration: Optional[int] = None
    meeting_link: Optional[str] = None
    meeting_platform: Optional[MeetingPlatform] = None
    description: Optional[str] = None
    recording_url: Optional[str] = None
    notes_url: Optional[str] = None
    slides_url: Optional[str] = None
    status: Optional[ClassStatus] = None
