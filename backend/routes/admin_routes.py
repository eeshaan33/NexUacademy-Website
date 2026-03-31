from fastapi import APIRouter, HTTPException, status, Request, Response
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, timezone, timedelta
from config.database import get_database
from middleware.auth import get_current_user
import bcrypt
import uuid
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

ADMIN_EMAIL = "admin@nexuacademy.com"
ADMIN_DEFAULT_PASSWORD = "nexuacademy123"

class CreateTeacherRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class ContactFormRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    course: str
    message: Optional[str] = ""

async def ensure_admin_user():
    db = get_database()
    admin = await db.users.find_one({"email": ADMIN_EMAIL})
    if not admin:
        hashed = bcrypt.hashpw(ADMIN_DEFAULT_PASSWORD.encode('utf-8'), bcrypt.gensalt())
        await db.users.insert_one({
            "user_id": f"user_admin_{uuid.uuid4().hex[:8]}",
            "email": ADMIN_EMAIL,
            "name": "Admin",
            "role": "admin",
            "batch_id": None,
            "profile_pic": None,
            "phone_number": None,
            "telegram_id": None,
            "password": hashed.decode('utf-8'),
            "created_at": datetime.now(timezone.utc),
            "last_login": None
        })
        logger.info("Admin user created: admin@nexuacademy.com")

async def require_admin(request: Request):
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user

@router.post("/create-teacher")
async def create_teacher(data: CreateTeacherRequest, request: Request):
    await require_admin(request)
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
    await require_admin(request)
    db = get_database()
    teachers = await db.users.find({"role": "teacher"}, {"_id": 0, "password": 0}).to_list(100)
    return {"teachers": teachers}

@router.post("/contact")
async def submit_contact(data: ContactFormRequest):
    db = get_database()
    contact_doc = {
        "contact_id": f"contact_{uuid.uuid4().hex[:12]}",
        "name": data.name,
        "email": data.email,
        "phone": data.phone,
        "course": data.course,
        "message": data.message,
        "status": "new",
        "created_at": datetime.now(timezone.utc)
    }
    await db.contact_inquiries.insert_one(contact_doc)
    contact_doc.pop("_id", None)
    return {"message": "Your message has been sent successfully! We'll get back to you within 24 hours.", "inquiry": contact_doc}

@router.get("/contacts")
async def list_contacts(request: Request):
    await require_admin(request)
    db = get_database()
    contacts = await db.contact_inquiries.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)
    stats = {
        "total": await db.contact_inquiries.count_documents({}),
        "new": await db.contact_inquiries.count_documents({"status": "new"}),
        "responded": await db.contact_inquiries.count_documents({"status": "responded"})
    }
    return {"contacts": contacts, "stats": stats}

@router.put("/contacts/{contact_id}/status")
async def update_contact_status(contact_id: str, request: Request):
    await require_admin(request)
    db = get_database()
    result = await db.contact_inquiries.update_one(
        {"contact_id": contact_id},
        {"$set": {"status": "responded", "responded_at": datetime.now(timezone.utc)}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Status updated"}
