"""Auth routes — thin wrapper over Supabase Auth.

- POST /api/auth/login             → email+password → session
- POST /api/auth/signup            → creates user (student by default) + profile row
- POST /api/auth/logout            → invalidates session (client-driven)
- GET  /api/auth/me                → current user + profile
- POST /api/auth/google            → returns Supabase OAuth URL for the client to redirect to
- POST /api/auth/claim-preseed     → one-shot claim for the whitelisted enrolled students
- GET  /api/auth/preseed-status    → check whether an email belongs to an unclaimed preseed
"""
import os
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from config.database import get_pool, get_supabase, get_supabase_admin
from middleware.auth import get_current_user
from services.otp_email import send_otp_email

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmailOnlyRequest(BaseModel):
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str
    role: str = "student"
    batch_code: Optional[str] = None
    phone_number: Optional[str] = None


# =============================================================================
# Generic email-OTP endpoints (per Phase-21 spec)
#   POST /api/auth/send-otp     { email }        → sends 6-digit code, 5 min TTL
#   POST /api/auth/verify-otp   { email, otp }   → marks verified, clears code
# Backed by the same `auth_otps` table as the signup/login flows but with the
# dedicated purpose='email_verify' so it never collides with those codes.
# =============================================================================
import hashlib
import secrets as _secrets
from datetime import datetime, timedelta, timezone

GENERIC_OTP_TTL_MIN = 5
GENERIC_OTP_MAX_ATTEMPTS = 5


def _hash_generic(code: str, email: str) -> str:
    return hashlib.sha256(f"{email.lower()}::{code}".encode()).hexdigest()


@router.post("/send-otp")
async def send_otp(payload: EmailOnlyRequest):
    email = payload.email.lower()
    code = f"{_secrets.randbelow(1_000_000):06d}"
    expires = datetime.now(timezone.utc) + timedelta(minutes=GENERIC_OTP_TTL_MIN)
    pool = get_pool()
    async with pool.acquire() as conn:
        # Invalidate any prior unverified codes for this email
        await conn.execute(
            """UPDATE auth_otps SET verified_at = NOW()
                 WHERE email = $1 AND purpose = 'email_verify' AND verified_at IS NULL""",
            email,
        )
        await conn.execute(
            """INSERT INTO auth_otps (email, code_hash, purpose, expires_at)
               VALUES ($1, $2, 'email_verify', $3)""",
            email, _hash_generic(code, email), expires,
        )

    result = send_otp_email(email, code, purpose="email_verify")
    if not result.get("ok"):
        # Surface the real Resend error back to the client — no silent success.
        logger.warning(
            f"send-otp: Resend delivery failed for {email}: "
            f"name={result.get('name')} status={result.get('status_code')} message={result.get('error')}"
        )
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Could not send verification email",
                "resend_error": result.get("error"),
                "resend_status_code": result.get("status_code"),
                "resend_error_name": result.get("name"),
            },
        )
    return {"success": True, "message": "OTP sent successfully", "resend_id": result.get("id")}


@router.post("/verify-otp")
async def verify_otp(payload: VerifyOtpRequest):
    email = payload.email.lower()
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT * FROM auth_otps
                WHERE email = $1 AND purpose = 'email_verify'
                  AND verified_at IS NULL AND expires_at > NOW()
                ORDER BY created_at DESC LIMIT 1""",
            email,
        )
        if not row:
            raise HTTPException(status_code=400, detail="No active code — request a new one")
        if row["attempts"] >= GENERIC_OTP_MAX_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Too many attempts — request a new code")
        if row["code_hash"] != _hash_generic(payload.otp, email):
            await conn.execute(
                "UPDATE auth_otps SET attempts = attempts + 1 WHERE id = $1", row["id"]
            )
            raise HTTPException(status_code=400, detail="Incorrect code")
        await conn.execute(
            "UPDATE auth_otps SET verified_at = NOW() WHERE id = $1", row["id"]
        )
    return {"success": True, "message": "Email verified"}


@router.post("/login")
async def login(payload: LoginRequest, request: Request):
    supabase = get_supabase()
    try:
        res = supabase.auth.sign_in_with_password({"email": payload.email, "password": payload.password})
    except Exception as e:
        logger.info(f"Login failed for {payload.email}: {e}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not res.session:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    pool = get_pool()
    async with pool.acquire() as conn:
        profile = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", res.user.id)

    prof = dict(profile) if profile else {}
    from routes.question_bank_routes import teacher_has_question_bank
    from routes.otp_routes import is_device_trusted, issue_login_challenge
    role = prof.get("role", "student")
    email = res.user.email

    # New-device OTP challenge — only enforced when the client sends a device id
    # (backward-compatible for older clients that haven't been upgraded yet).
    device_id = (request.headers.get("x-device-id") or "").strip()
    if device_id:
        trusted = await is_device_trusted(str(res.user.id), device_id)
        if not trusted:
            await issue_login_challenge(email)
            return {
                "success": True,
                "requires_otp": True,
                "email": email,
                "message": "New device detected — check your email for a 6-digit code.",
            }
        # Trusted — refresh last_seen_at
        client_ip = request.client.host if request.client else None
        async with pool.acquire() as conn:
            await conn.execute(
                """UPDATE trusted_devices
                     SET last_seen_at = NOW(), last_ip = $3
                   WHERE user_id = $1 AND device_id = $2""",
                res.user.id, device_id, client_ip,
            )

    return {
        "success": True,
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "token": res.session.access_token,
        "expires_at": res.session.expires_at,
        "user": {
            "user_id": str(res.user.id),
            "email": email,
            "name": prof.get("name") or email,
            "role": role,
            "batch_id": prof.get("batch_id"),
            "profile_pic": prof.get("profile_pic"),
            "phone": prof.get("phone"),
            "access_tier": prof.get("access_tier", "free"),
            "is_existing_student": prof.get("is_existing_student", False),
            "features": {
                "question_bank": teacher_has_question_bank({"role": role, "email": email}),
            },
        },
    }


@router.post("/signup")
async def signup(payload: SignupRequest):
    admin_client = get_supabase_admin()
    metadata = {"name": payload.name, "role": payload.role}
    if payload.batch_code:
        metadata["batch_id"] = payload.batch_code.strip().upper()

    try:
        res = admin_client.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
            "user_metadata": metadata,
        })
    except Exception as e:
        msg = str(e)
        if "already" in msg.lower() or "registered" in msg.lower():
            raise HTTPException(status_code=400, detail="This email is already registered")
        logger.exception("Signup failed")
        raise HTTPException(status_code=400, detail=f"Signup failed: {msg[:200]}")

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE profiles SET name = $2, role = $3, phone_number = $4
            WHERE id = $1
            """,
            res.user.id, payload.name, payload.role, payload.phone_number,
        )

    # Sign in via a fresh anon client for a valid session token
    anon = get_supabase()
    session = anon.auth.sign_in_with_password({"email": payload.email, "password": payload.password})
    return {
        "success": True,
        "access_token": session.session.access_token,
        "refresh_token": session.session.refresh_token,
        "token": session.session.access_token,
        "user": {
            "user_id": str(res.user.id),
            "email": res.user.email,
            "name": payload.name,
            "role": payload.role,
        },
    }


@router.get("/me")
async def me(request: Request):
    user = await get_current_user(request)
    # Convert UUIDs / datetimes → strings for JSON
    for k, v in list(user.items()):
        if hasattr(v, "isoformat"):
            user[k] = v.isoformat()
        elif hasattr(v, "hex") and not isinstance(v, (bytes, bytearray)):
            user[k] = str(v)
    user.pop("push_subscription", None)
    # Ensure new tier fields are always present in the response
    user.setdefault("access_tier", "free")
    user.setdefault("is_existing_student", False)
    # Feature flags (Question Bank is gated to allow-listed teachers + admins)
    from routes.question_bank_routes import teacher_has_question_bank
    user["features"] = {"question_bank": teacher_has_question_bank(user)}
    return {"success": True, "user": user}


@router.post("/logout")
async def logout():
    # Supabase sessions are stateless JWTs — client just discards the token.
    return {"success": True}


@router.get("/google/url")
async def google_oauth_url(redirect_to: Optional[str] = None):
    """Return Supabase Google-OAuth authorize URL for the frontend to redirect to.

    The frontend passes `?redirect_to=<origin>/auth/callback` explicitly so
    Supabase sends the browser back to the right domain (dev/preview/prod).
    Falls back to backend env values only if the client omits it.
    """
    base = os.environ["SUPABASE_URL"].rstrip("/")
    if not redirect_to:
        site = (
            os.environ.get("SITE_URL")
            or os.environ.get("FRONTEND_URL")
            or os.environ.get("REACT_APP_BACKEND_URL", "")
        )
        redirect_to = f"{site.rstrip('/')}/auth/callback" if site else ""
    url = f"{base}/auth/v1/authorize?provider=google"
    if redirect_to:
        from urllib.parse import quote
        url += f"&redirect_to={quote(redirect_to, safe='')}"
    return {"success": True, "url": url, "redirect_to": redirect_to}


# ---------------------------------------------------------------------------
# Preseed claim flow — for the 21 already-enrolled students named by the admin
# ---------------------------------------------------------------------------
class ClaimPreseedRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=60)
    email: EmailStr
    batch_id: str = Field(..., min_length=2, max_length=20)


@router.get("/preseed-status")
async def preseed_status(email: str = "", first_name: str = "", batch_id: str = ""):
    """Query helper used by /auth/callback to tell if an email is a preseed
    student that hasn't claimed their account yet. Returns:
      { is_preseed: bool, claimed: bool, batch_id: str|null, first_name: str|null }
    """
    pool = get_pool()
    email = (email or "").strip().lower()
    async with pool.acquire() as conn:
        by_email = None
        if email:
            by_email = await conn.fetchrow(
                "SELECT first_name, batch_id, claimed_email FROM preseed_students WHERE lower(claimed_email) = $1",
                email,
            )
        if by_email:
            return {"is_preseed": True, "claimed": True,
                    "batch_id": by_email["batch_id"], "first_name": by_email["first_name"]}

        if first_name and batch_id:
            row = await conn.fetchrow(
                """SELECT first_name, batch_id, claimed_email
                     FROM preseed_students
                    WHERE first_name_lower = lower($1) AND upper(batch_id) = upper($2)""",
                first_name.strip(), batch_id.strip(),
            )
            if row:
                return {"is_preseed": True, "claimed": row["claimed_email"] is not None,
                        "batch_id": row["batch_id"], "first_name": row["first_name"]}
    return {"is_preseed": False, "claimed": False, "batch_id": None, "first_name": None}


@router.post("/claim-preseed")
async def claim_preseed(payload: ClaimPreseedRequest):
    """First-time account claim for enrolled students.

    Flow:
      1. Lookup preseed row by (first_name, batch_id). Reject if unknown or already claimed.
      2. Create Supabase auth user with the requested email + default password
         (or bind to an existing auth user with the same email).
      3. Set profile.access_tier='live_batch', is_existing_student=true, batch_id set.
      4. Mark preseed row claimed. Return session tokens + default password (shown once).
    """
    admin_client = get_supabase_admin()
    pool = get_pool()

    first_name = payload.first_name.strip()
    email = payload.email.strip().lower()
    batch_id = payload.batch_id.strip().upper()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT id, first_name, batch_id, default_password, claimed_email
                 FROM preseed_students
                WHERE first_name_lower = lower($1) AND upper(batch_id) = $2""",
            first_name, batch_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail=(
                f"'{first_name}' is not on the {batch_id} enrolled list. "
                "Double-check spelling/batch, or use the New Student Application."
            ))
        if row["claimed_email"]:
            raise HTTPException(status_code=400, detail=(
                f"This account has already been claimed. Please sign in with {row['claimed_email']}."
            ))
        # Confirm batch exists (FK safety)
        batch_exists = await conn.fetchval("SELECT 1 FROM batches WHERE id = $1", batch_id)
        if not batch_exists:
            raise HTTPException(status_code=400, detail=f"Batch {batch_id} does not exist.")

    default_password = row["default_password"]

    # Create or bind to existing Supabase auth user
    user_id = None
    try:
        res = admin_client.auth.admin.create_user({
            "email": email,
            "password": default_password,
            "email_confirm": True,
            "user_metadata": {"name": row["first_name"], "role": "student", "batch_id": batch_id},
        })
        user_id = res.user.id
    except Exception as e:
        msg = str(e).lower()
        if any(x in msg for x in ("already", "registered", "exists")):
            existing = admin_client.auth.admin.list_users()
            found = next((u for u in existing if u.email == email), None)
            if not found:
                raise HTTPException(status_code=400, detail="Could not bind to existing account.")
            user_id = found.id
            # Reset password so we can also sign them in via password
            try:
                admin_client.auth.admin.update_user_by_id(user_id, {"password": default_password})
            except Exception:
                pass
        else:
            logger.exception("claim-preseed create_user failed")
            raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)[:200]}")

    # Set profile flags + mark preseed row claimed
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE profiles
               SET name = $2,
                   role = 'student',
                   batch_id = $3,
                   access_tier = 'live_batch',
                   is_existing_student = TRUE,
                   payment_status = COALESCE(payment_status, 'paid')
             WHERE id = $1
            """,
            user_id, row["first_name"], batch_id,
        )
        await conn.execute(
            """UPDATE preseed_students
                  SET claimed_email = $1, claimed_at = NOW(), claimed_user_id = $2
                WHERE id = $3""",
            email, user_id, row["id"],
        )

    # Sign in the student so they land on the dashboard immediately
    anon = get_supabase()
    session = anon.auth.sign_in_with_password({"email": email, "password": default_password})

    return {
        "success": True,
        "default_password": default_password,
        "access_token": session.session.access_token,
        "refresh_token": session.session.refresh_token,
        "token": session.session.access_token,
        "user": {
            "user_id": str(user_id),
            "email": email,
            "name": row["first_name"],
            "role": "student",
            "batch_id": batch_id,
            "access_tier": "live_batch",
            "is_existing_student": True,
        },
    }
