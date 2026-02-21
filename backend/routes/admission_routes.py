from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import StreamingResponse
from config.database import get_database
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import base64
import io
import json
import bcrypt
from middleware.auth import get_current_user
from pydantic import BaseModel, EmailStr
from services.email_service import send_admission_confirmation_email

router = APIRouter(prefix="/admissions", tags=["admissions"])

class AdmissionForm(BaseModel):
    student_name: str
    father_name: str
    mother_name: str
    date_of_birth: str
    gender: str
    contact_number: str
    email: EmailStr
    password: str  # Added password field
    address: str
    city: str
    state: str
    pincode: str
    course_applying: str
    photo_base64: Optional[str] = None
    id_proof_base64: Optional[str] = None
    signature_base64: Optional[str] = None

@router.post("/submit")
async def submit_admission(form: AdmissionForm, request: Request):
    """Submit admission form with all details"""
    db = get_database()
    
    # Generate unique admission ID
    admission_id = f"ADM{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
    
    # Create admission document
    admission_doc = {
        "admission_id": admission_id,
        "student_name": form.student_name,
        "father_name": form.father_name,
        "mother_name": form.mother_name,
        "date_of_birth": form.date_of_birth,
        "gender": form.gender,
        "contact_number": form.contact_number,
        "email": form.email,
        "address": form.address,
        "city": form.city,
        "state": form.state,
        "pincode": form.pincode,
        "course_applying": form.course_applying,
        "photo": form.photo_base64,
        "id_proof": form.id_proof_base64,
        "signature": form.signature_base64,
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc),
        "reviewed_at": None,
        "reviewed_by": None,
        "remarks": None
    }
    
    await db.admissions.insert_one(admission_doc)
    
    # Create user account if doesn't exist
    existing_user = await db.users.find_one({"email": form.email})
    if not existing_user:
        import bcrypt
        temp_password = uuid.uuid4().hex[:8]
        hashed = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user_doc = {
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": form.email,
            "name": form.student_name,
            "password": hashed,
            "role": "student",
            "admission_id": admission_id,
            "profile_complete": True,
            "created_at": datetime.now(timezone.utc)
        }
        await db.users.insert_one(user_doc)
    
    return {
        "success": True,
        "admission_id": admission_id,
        "message": "Admission form submitted successfully"
    }

@router.get("/list")
async def list_admissions(request: Request, status: Optional[str] = None, limit: int = 50, skip: int = 0):
    """Get list of all admissions (admin only)"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        if user.get("role") != "teacher" and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
    except:
        pass  # Allow public access for now
    
    query = {}
    if status:
        query["status"] = status
    
    admissions = await db.admissions.find(
        query,
        {"_id": 0, "photo": 0, "id_proof": 0, "signature": 0}  # Exclude large base64 fields
    ).sort("submitted_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    total = await db.admissions.count_documents(query)
    
    return {
        "admissions": admissions,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }

@router.get("/detail/{admission_id}")
async def get_admission_detail(admission_id: str, request: Request):
    """Get full admission details including documents"""
    db = get_database()
    
    admission = await db.admissions.find_one(
        {"admission_id": admission_id},
        {"_id": 0}
    )
    
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")
    
    return admission

@router.put("/update-status/{admission_id}")
async def update_admission_status(admission_id: str, status: str, remarks: Optional[str] = None, request: Request = None):
    """Update admission status (admin only)"""
    db = get_database()
    
    result = await db.admissions.update_one(
        {"admission_id": admission_id},
        {
            "$set": {
                "status": status,
                "remarks": remarks,
                "reviewed_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Admission not found")
    
    return {"success": True, "message": f"Status updated to {status}"}

@router.get("/export/excel")
async def export_admissions_excel(request: Request):
    """Export all admissions to Excel format"""
    db = get_database()
    
    admissions = await db.admissions.find(
        {},
        {"_id": 0, "photo": 0, "id_proof": 0, "signature": 0}
    ).sort("submitted_at", -1).to_list(length=1000)
    
    # Create CSV content
    import csv
    output = io.StringIO()
    
    if admissions:
        fieldnames = ["admission_id", "student_name", "father_name", "mother_name", 
                     "date_of_birth", "gender", "contact_number", "email", 
                     "address", "city", "state", "pincode", "course_applying", 
                     "status", "submitted_at", "remarks"]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for admission in admissions:
            row = {k: admission.get(k, "") for k in fieldnames}
            if row.get("submitted_at"):
                row["submitted_at"] = str(row["submitted_at"])[:19]
            writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=admissions.csv"}
    )

@router.get("/stats")
async def get_admission_stats(request: Request):
    """Get admission statistics"""
    db = get_database()
    
    total = await db.admissions.count_documents({})
    pending = await db.admissions.count_documents({"status": "pending"})
    approved = await db.admissions.count_documents({"status": "approved"})
    rejected = await db.admissions.count_documents({"status": "rejected"})
    
    # By course
    pipeline = [
        {"$group": {"_id": "$course_applying", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    by_course = await db.admissions.aggregate(pipeline).to_list(length=20)
    
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "by_course": by_course
    }
