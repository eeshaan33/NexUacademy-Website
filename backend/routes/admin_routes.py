from fastapi import APIRouter, HTTPException, status, Request, Response
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
from config.database import get_database
import bcrypt
import uuid
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "nexuacademy123"

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class CreateTeacherRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

async def verify_admin_session(request: Request):
    db = get_database()
    session_token = request.cookies.get("admin_session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.replace("Bearer ", "")
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not authenticated")
    session = await db.admin_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin session")
    expires_at = session["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin session expired")
    return True

@router.post("/login")
async def admin_login(data: AdminLoginRequest, response: Response):
    if data.username != ADMIN_USERNAME or data.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")
    db = get_database()
    session_token = f"admin_{uuid.uuid4().hex}"
    await db.admin_sessions.insert_one({
        "session_token": session_token,
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=12),
        "created_at": datetime.now(timezone.utc)
    })
    response.set_cookie(
        key="admin_session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=12 * 60 * 60
    )
    return {"message": "Admin login successful", "token": session_token}

@router.post("/create-teacher")
async def create_teacher(data: CreateTeacherRequest, request: Request):
    await verify_admin_session(request)
    db = get_database()
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    hashed_password = bcrypt.hashpw(data.password.encode('utf-8'), bcrypt.gensalt())
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    teacher_doc = {
        "user_id": user_id,
        "email": data.email,
        "name": data.name,
        "role": "teacher",
        "batch_id": None,
        "profile_pic": None,
        "phone_number": None,
        "telegram_id": None,
        "password": hashed_password.decode('utf-8'),
        "created_at": datetime.now(timezone.utc),
        "last_login": None
    }
    await db.users.insert_one(teacher_doc)
    teacher_doc.pop("_id", None)
    teacher_doc.pop("password", None)
    logger.info(f"Teacher account created: {data.email}")
    return {"message": "Teacher account created successfully", "teacher": teacher_doc}

@router.get("/teachers")
async def list_teachers(request: Request):
    await verify_admin_session(request)
    db = get_database()
    teachers = await db.users.find({"role": "teacher"}, {"_id": 0, "password": 0}).to_list(100)
    return {"teachers": teachers}

@router.post("/logout")
async def admin_logout(request: Request, response: Response):
    db = get_database()
    session_token = request.cookies.get("admin_session_token")
    if session_token:
        await db.admin_sessions.delete_one({"session_token": session_token})
    response.delete_cookie(key="admin_session_token", path="/", samesite="none", secure=True)
    return {"message": "Admin logout successful"}
