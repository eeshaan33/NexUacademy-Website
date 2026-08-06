"""Auth routes — thin wrapper over Supabase Auth.

- POST /api/auth/login       → email+password → session
- POST /api/auth/signup      → creates user (student by default) + profile row
- POST /api/auth/logout      → invalidates session (client-driven)
- GET  /api/auth/me          → current user + profile
- POST /api/auth/google      → returns Supabase OAuth URL for the client to redirect to
"""
import os
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from config.database import get_pool, get_supabase
from middleware.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str
    role: str = "student"
    batch_code: Optional[str] = None
    phone_number: Optional[str] = None


@router.post("/login")
async def login(payload: LoginRequest):
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

    return {
        "success": True,
        "access_token": res.session.access_token,
        "refresh_token": res.session.refresh_token,
        "token": res.session.access_token,  # legacy client alias
        "expires_at": res.session.expires_at,
        "user": {
            "user_id": str(res.user.id),
            "email": res.user.email,
            "name": (dict(profile) if profile else {}).get("name") or res.user.email,
            "role": (dict(profile) if profile else {}).get("role", "student"),
            "batch_id": (dict(profile) if profile else {}).get("batch_id"),
            "profile_pic": (dict(profile) if profile else {}).get("profile_pic"),
        },
    }


@router.post("/signup")
async def signup(payload: SignupRequest):
    supabase = get_supabase()
    metadata = {"name": payload.name, "role": payload.role}
    if payload.batch_code:
        metadata["batch_id"] = payload.batch_code.strip().upper()

    try:
        res = supabase.auth.admin.create_user({
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

    # Update profile with extra fields (trigger created the base row)
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE profiles SET name = $2, role = $3, phone_number = $4
            WHERE id = $1
            """,
            res.user.id, payload.name, payload.role, payload.phone_number,
        )

    # Auto-login
    session = supabase.auth.sign_in_with_password({"email": payload.email, "password": payload.password})
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
    return {"success": True, "user": user}


@router.post("/logout")
async def logout():
    # Supabase sessions are stateless JWTs — client just discards the token.
    return {"success": True}


@router.get("/google/url")
async def google_oauth_url():
    """Return Supabase Google-OAuth authorize URL for the frontend to redirect to."""
    base = os.environ["SUPABASE_URL"].rstrip("/")
    site = os.environ.get("SITE_URL") or os.environ.get("REACT_APP_BACKEND_URL", "")
    redirect_to = f"{site}/auth/callback" if site else ""
    url = f"{base}/auth/v1/authorize?provider=google"
    if redirect_to:
        from urllib.parse import quote
        url += f"&redirect_to={quote(redirect_to, safe='')}"
    return {"success": True, "url": url}
