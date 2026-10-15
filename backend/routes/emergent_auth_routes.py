"""Emergent-managed Google Auth.

Exchanges a session_id (returned by https://auth.emergentagent.com/) for a
7-day httpOnly cookie-based session, creating/updating the Supabase Auth user
and the local `profiles` row along the way. Coexists with the existing
Supabase JWT flow — middleware/auth.py accepts either.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from config.database import get_pool, get_supabase_admin

router = APIRouter(prefix="/auth/emergent", tags=["auth-emergent"])
logger = logging.getLogger(__name__)

EMERGENT_SESSION_URL = (
    "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"
)
COOKIE_NAME = "session_token"
SESSION_TTL_DAYS = 7


async def _fetch_emergent_profile(session_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(EMERGENT_SESSION_URL, headers={"X-Session-ID": session_id})
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Emergent session_id")
    data = r.json()
    for key in ("email", "session_token"):
        if not data.get(key):
            raise HTTPException(status_code=502, detail=f"Emergent response missing {key}")
    return data


async def _ensure_supabase_user(email: str, name: str, picture: str | None) -> str:
    """Ensure a Supabase Auth user + `profiles` row exists for this email.

    Returns the Supabase auth user_id (UUID string).
    """
    admin = get_supabase_admin()
    user_id = None
    # Look up existing auth user by email
    try:
        existing = admin.auth.admin.list_users()
        found = next((u for u in existing if (u.email or "").lower() == email.lower()), None)
        if found:
            user_id = found.id
    except Exception as e:
        logger.warning(f"list_users failed: {e}")

    if not user_id:
        # Create fresh auth user with a random password (never used — user
        # signs in via Emergent, not password).
        random_password = secrets.token_urlsafe(24)
        try:
            res = admin.auth.admin.create_user({
                "email": email,
                "password": random_password,
                "email_confirm": True,
                "user_metadata": {"name": name, "role": "student", "auth_provider": "emergent"},
            })
            user_id = res.user.id
        except Exception as e:
            logger.exception("emergent create_user failed")
            raise HTTPException(status_code=500, detail=f"Could not create user: {str(e)[:200]}")

    # Upsert profile row (name + picture)
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO profiles (id, email, name, role, profile_pic)
            VALUES ($1, $2, $3, 'student', $4)
            ON CONFLICT (id) DO UPDATE
               SET name = COALESCE(profiles.name, EXCLUDED.name),
                   profile_pic = COALESCE(profiles.profile_pic, EXCLUDED.profile_pic)
            """,
            user_id, email, name or email.split("@")[0], picture,
        )

    return user_id


@router.post("/session")
async def create_session(request: Request, response: Response):
    """Exchange Emergent session_id for a cookie-based session.

    Header: X-Session-ID: <session_id>
    """
    session_id = request.headers.get("X-Session-ID") or request.headers.get("x-session-id")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-ID header")

    profile = await _fetch_emergent_profile(session_id)
    email = profile["email"].strip().lower()
    name = profile.get("name") or email.split("@")[0]
    picture = profile.get("picture")
    session_token = profile["session_token"]

    user_id = await _ensure_supabase_user(email, name, picture)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_TTL_DAYS)

    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO emergent_sessions (session_token, user_id, email, expires_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (session_token) DO UPDATE
               SET user_id = EXCLUDED.user_id,
                   email   = EXCLUDED.email,
                   expires_at = EXCLUDED.expires_at
            """,
            session_token, user_id, email, expires_at,
        )
        profile_row = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", user_id)

    # httpOnly cookie — same-origin (frontend + backend share ingress domain),
    # so SameSite=None + Secure is safe and required for the fetch that
    # follows the fragment redirect.
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        max_age=SESSION_TTL_DAYS * 24 * 60 * 60,
        expires=int(expires_at.timestamp()),
        path="/",
        httponly=True,
        secure=True,
        samesite="none",
    )

    p = dict(profile_row) if profile_row else {}
    return {
        "success": True,
        "user": {
            "user_id": str(user_id),
            "email": email,
            "name": p.get("name") or name,
            "role": p.get("role", "student"),
            "batch_id": p.get("batch_id"),
            "profile_pic": p.get("profile_pic") or picture,
            "access_tier": p.get("access_tier", "free"),
            "auth_provider": "emergent",
        },
    }


@router.post("/logout")
async def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE_NAME, "")
    if token:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM emergent_sessions WHERE session_token = $1", token)
    response.delete_cookie(COOKIE_NAME, path="/", samesite="none", secure=True)
    return {"success": True}
