"""Admission form submission — creates Supabase Auth user + profile + admissions row."""
import logging
import random
import string
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from config.database import get_pool, get_supabase
from middleware.auth import get_current_user

router = APIRouter(prefix="/admissions", tags=["admissions"])
logger = logging.getLogger(__name__)


class AdmissionForm(BaseModel):
    student_name: str
    father_name: str
    mother_name: str
    date_of_birth: str
    gender: str
    contact_number: str
    email: EmailStr
    password: str
    address: str
    city: str
    state: str
    pincode: str
    course_applying: str
    batch_code: Optional[str] = None
    photo_base64: Optional[str] = None
    id_proof_base64: Optional[str] = None
    signature_base64: Optional[str] = None


def _admission_id() -> str:
    return f"ADM{datetime.now().strftime('%Y%m%d')}{''.join(random.choices(string.hexdigits.upper(), k=6))}"


async def _unique_roll(conn) -> str:
    yy = datetime.now(timezone.utc).strftime("%y")
    alphabet = "".join(c for c in string.ascii_uppercase + string.digits if c not in "OI01")
    for _ in range(20):
        roll = f"NXU-{yy}{''.join(random.choices(alphabet, k=6))}"
        if not await conn.fetchval("SELECT 1 FROM profiles WHERE roll_number = $1", roll):
            return roll
    return f"NXU-{yy}{''.join(random.choices(alphabet, k=10))}"


@router.post("/submit")
async def submit_admission(form: AdmissionForm):
    supabase = get_supabase()
    pool = get_pool()

    # Verify batch code exists in DB (FK will fail otherwise)
    batch_id = None
    if form.batch_code:
        code = form.batch_code.strip().upper()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT id FROM batches WHERE code = $1", code)
        if not row:
            raise HTTPException(status_code=400, detail=f"Batch '{code}' not recognised. Ask your teacher/admin for the correct Batch ID.")
        batch_id = row["id"]

    # Create Supabase Auth user (email-confirmed)
    try:
        res = supabase.auth.admin.create_user({
            "email": form.email,
            "password": form.password,
            "email_confirm": True,
            "user_metadata": {"name": form.student_name, "role": "student",
                              "batch_id": batch_id or ""},
        })
    except Exception as e:
        msg = str(e)
        if "already" in msg.lower():
            raise HTTPException(status_code=400, detail="This email is already registered. Please login.")
        logger.exception("admission create_user failed")
        raise HTTPException(status_code=400, detail=f"Signup failed: {msg[:200]}")

    user_id = res.user.id
    admission_id = _admission_id()

    async with pool.acquire() as conn:
        roll = await _unique_roll(conn)
        # Update profile row (trigger created skeleton)
        await conn.execute(
            """
            UPDATE profiles SET
                name = $2, role = 'student',
                batch_id = $3, course = $4, roll_number = $5, admission_id = $6,
                father_name = $7, mother_name = $8, date_of_birth = $9, gender = $10,
                address = $11, city = $12, state = $13, pincode = $14,
                phone_number = $15, profile_pic = $16, profile_complete = true
            WHERE id = $1
            """,
            user_id, form.student_name, batch_id, form.course_applying, roll, admission_id,
            form.father_name, form.mother_name, form.date_of_birth, form.gender,
            form.address, form.city, form.state, form.pincode,
            form.contact_number, form.photo_base64,
        )
        await conn.execute(
            """
            INSERT INTO admissions (admission_id, user_id, roll_number, student_name,
                father_name, mother_name, date_of_birth, gender,
                contact_number, email, address, city, state, pincode,
                course_applying, batch_code, batch_id, photo, id_proof, signature, status)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,'pending')
            """,
            admission_id, user_id, roll, form.student_name,
            form.father_name, form.mother_name, form.date_of_birth, form.gender,
            form.contact_number, form.email, form.address, form.city, form.state, form.pincode,
            form.course_applying, (form.batch_code or "").upper() or None, batch_id,
            form.photo_base64, form.id_proof_base64, form.signature_base64,
        )

    # Auto-login
    session = supabase.auth.sign_in_with_password({"email": form.email, "password": form.password})
    return {
        "success": True,
        "message": "Admission submitted and account created",
        "admission_id": admission_id,
        "access_token": session.session.access_token,
        "refresh_token": session.session.refresh_token,
        "token": session.session.access_token,
        "user": {
            "user_id": str(user_id),
            "email": form.email,
            "name": form.student_name,
            "role": "student",
            "admission_id": admission_id,
            "roll_number": roll,
            "batch_id": batch_id,
        },
    }


@router.get("/me")
async def get_my_admission(request: Request):
    user = await get_current_user(request)
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Only students have admission records")

    pool = get_pool()
    async with pool.acquire() as conn:
        admission = await conn.fetchrow(
            "SELECT * FROM admissions WHERE user_id = $1 ORDER BY submitted_at DESC LIMIT 1",
            user["user_id"],
        )
        batch = None
        if user.get("batch_id"):
            batch = await conn.fetchrow("SELECT * FROM batches WHERE id = $1", user["batch_id"])

    def _dt(v):
        return v.isoformat() if hasattr(v, "isoformat") else v

    admission_d = None
    if admission:
        admission_d = {k: _dt(v) for k, v in dict(admission).items()
                       if k not in ("photo", "id_proof", "signature")}

    return {
        "success": True,
        "user": {**{k: _dt(v) for k, v in user.items()}, "user_id": str(user["user_id"])},
        "admission": admission_d,
        "batch": {**dict(batch), "created_at": _dt(batch["created_at"])} if batch else None,
    }
