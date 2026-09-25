"""Email-OTP flow: signup verification + new-device login challenge.

Endpoints:
  POST /api/auth/otp/start-signup    — collects credentials, sends email OTP
  POST /api/auth/otp/verify-signup   — verifies OTP, creates Supabase user + profile
  POST /api/auth/otp/verify-login    — verifies OTP for new-device sign-in, returns session
Regular /api/auth/login is patched (see auth_routes.py) to gate new-device sign-ins.
"""
import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from config.database import get_pool, get_supabase_admin
from services.otp_email import send_otp_email

router = APIRouter(prefix="/auth/otp", tags=["auth-otp"])
logger = logging.getLogger(__name__)

OTP_TTL_MIN = 10
MAX_ATTEMPTS = 5


def _hash_code(code: str, email: str) -> str:
    return hashlib.sha256(f"{email.lower()}::{code}".encode()).hexdigest()


def _gen_code() -> str:
    return f"{secrets.randbelow(1000000):06d}"


async def _create_otp(email: str, purpose: str, payload: Optional[dict] = None) -> str:
    code = _gen_code()
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO auth_otps (email, code_hash, purpose, payload, expires_at)
               VALUES ($1, $2, $3, $4::jsonb, $5)""",
            email.lower(),
            _hash_code(code, email),
            purpose,
            json.dumps(payload) if payload else None,
            datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MIN),
        )
    return code


async def _consume_otp(email: str, code: str, purpose: str) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT * FROM auth_otps
                 WHERE email = $1 AND purpose = $2 AND verified_at IS NULL
                   AND expires_at > NOW()
                 ORDER BY created_at DESC LIMIT 1""",
            email.lower(), purpose,
        )
        if not row:
            raise HTTPException(status_code=400, detail="No active code — request a new one")
        if row["attempts"] >= MAX_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Too many attempts — request a new code")
        if row["code_hash"] != _hash_code(code, email):
            await conn.execute(
                "UPDATE auth_otps SET attempts = attempts + 1 WHERE id = $1", row["id"]
            )
            raise HTTPException(status_code=400, detail="Incorrect code")
        await conn.execute(
            "UPDATE auth_otps SET verified_at = NOW() WHERE id = $1", row["id"]
        )
    payload = row["payload"]
    return json.loads(payload) if isinstance(payload, str) else (payload or {})


# =============================================================================
# SIGNUP
# =============================================================================
class SignupStart(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=6, max_length=20)
    password: str = Field(..., min_length=6, max_length=128)
    batch_code: Optional[str] = None


@router.post("/start-signup")
async def start_signup(payload: SignupStart):
    email = payload.email.lower()
    supabase = get_supabase_admin()
    # Reject if email is already registered on Supabase Auth
    try:
        listing = supabase.auth.admin.list_users()
        existing = [u for u in listing if getattr(u, "email", "").lower() == email]
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered — try signing in")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"list_users check failed (continuing): {e}")

    code = await _create_otp(
        email=email, purpose="signup",
        payload={
            "name": payload.name.strip(),
            "email": email,
            "phone": payload.phone.strip(),
            "password": payload.password,
            "batch_code": (payload.batch_code or "").strip() or None,
        },
    )
    sent = send_otp_email(email, code, purpose="signup")
    return {"success": True, "email_sent": sent, "expires_in_minutes": OTP_TTL_MIN}


class VerifyCode(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


@router.post("/verify-signup")
async def verify_signup(payload: VerifyCode, request: Request):
    saved = await _consume_otp(payload.email, payload.code, purpose="signup")
    if not saved:
        raise HTTPException(status_code=400, detail="Signup payload missing — please start over")

    supabase = get_supabase_admin()
    # Create Supabase Auth user (bcrypt-hashed by Supabase Auth internally)
    try:
        res = supabase.auth.admin.create_user({
            "email": saved["email"],
            "password": saved["password"],
            "email_confirm": True,
            "user_metadata": {"name": saved["name"]},
        })
    except Exception as e:
        logger.exception("Supabase create_user failed")
        raise HTTPException(status_code=500, detail=f"Account creation failed: {e}")

    user_id = res.user.id
    # Upsert profile
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO profiles (id, name, email, phone, role, batch_id,
                                     email_verified_at)
                 VALUES ($1,$2,$3,$4,'student',$5, NOW())
                 ON CONFLICT (id) DO UPDATE
                   SET name = EXCLUDED.name,
                       phone = EXCLUDED.phone,
                       email_verified_at = NOW()""",
            user_id, saved["name"], saved["email"], saved["phone"], saved.get("batch_code"),
        )

    # Sign the user in immediately so the client gets tokens right away
    try:
        session = supabase.auth.sign_in_with_password({
            "email": saved["email"], "password": saved["password"],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signin after signup failed: {e}")

    # Auto-trust the device this signup came from
    dev_id = (request.headers.get("x-device-id") or "").strip()
    if dev_id:
        client_ip = request.client.host if request.client else None
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO trusted_devices (user_id, device_id, last_ip)
                     VALUES ($1, $2, $3)
                     ON CONFLICT (user_id, device_id)
                     DO UPDATE SET last_seen_at = NOW(), last_ip = EXCLUDED.last_ip""",
                user_id, dev_id, client_ip,
            )

    from routes.question_bank_routes import teacher_has_question_bank
    return {
        "success": True,
        "access_token": session.session.access_token,
        "refresh_token": session.session.refresh_token,
        "token": session.session.access_token,
        "user": {
            "user_id": str(user_id),
            "email": saved["email"],
            "name": saved["name"],
            "role": "student",
            "batch_id": saved.get("batch_code"),
            "phone": saved["phone"],
            "features": {
                "question_bank": teacher_has_question_bank({"role": "student", "email": saved["email"]}),
            },
        },
    }


# =============================================================================
# LOGIN CHALLENGE (new device)
# =============================================================================
class LoginOtpStart(BaseModel):
    email: EmailStr


@router.post("/resend-login")
async def resend_login_code(payload: LoginOtpStart):
    """Manual resend button on the OTP screen."""
    code = await _create_otp(email=payload.email, purpose="login")
    sent = send_otp_email(payload.email, code, purpose="login")
    return {"success": True, "email_sent": sent, "expires_in_minutes": OTP_TTL_MIN}


class VerifyLoginOtp(BaseModel):
    email: EmailStr
    password: str
    code: str


@router.post("/verify-login")
async def verify_login(payload: VerifyLoginOtp, request: Request):
    await _consume_otp(payload.email, payload.code, purpose="login")
    supabase = get_supabase_admin()
    try:
        res = supabase.auth.sign_in_with_password({
            "email": payload.email, "password": payload.password,
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Password no longer valid — sign in again")

    user_id = res.user.id
    pool = get_pool()
    async with pool.acquire() as conn:
        profile = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", user_id)

    dev_id = (request.headers.get("x-device-id") or "").strip()
    client_ip = request.client.host if request.client else None
    if dev_id:
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO trusted_devices (user_id, device_id, last_ip)
                     VALUES ($1, $2, $3)
                     ON CONFLICT (user_id, device_id)
                     DO UPDATE SET last_seen_at = NOW(), last_ip = EXCLUDED.last_ip""",
                user_id, dev_id, client_ip,
            )

    prof = dict(profile) if profile else {}
    from routes.question_bank_routes import teacher_has_question_bank
    role = prof.get("role", "student")
    return {
        "success": True,
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "token": res.session.access_token,
        "user": {
            "user_id": str(user_id),
            "email": res.user.email,
            "name": prof.get("name") or res.user.email,
            "role": role,
            "batch_id": prof.get("batch_id"),
            "phone": prof.get("phone"),
            "profile_pic": prof.get("profile_pic"),
            "features": {"question_bank": teacher_has_question_bank({"role": role, "email": res.user.email})},
        },
    }


# =============================================================================
# HELPER used by /api/auth/login to decide if OTP is required
# =============================================================================
async def is_device_trusted(user_id: str, device_id: str) -> bool:
    if not device_id:
        return False
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM trusted_devices WHERE user_id = $1 AND device_id = $2",
            user_id, device_id,
        )
    return bool(row)


async def issue_login_challenge(email: str) -> None:
    code = await _create_otp(email=email, purpose="login")
    send_otp_email(email, code, purpose="login")
