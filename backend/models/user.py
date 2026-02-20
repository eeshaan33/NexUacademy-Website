from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: str = "student"  # student or teacher
    batch_id: Optional[str] = None
    profile_pic: Optional[str] = None
    phone_number: Optional[str] = None
    telegram_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    user_id: str
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserSession(BaseModel):
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
