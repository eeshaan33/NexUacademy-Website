"""Auth middleware — verifies Supabase Auth JWTs OR Emergent cookie sessions."""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, Request, status
from jwt import PyJWKClient

from config.database import get_pool, get_supabase_admin

logger = logging.getLogger(__name__)

EMERGENT_COOKIE = "session_token"

# Supabase issues JWTs signed with a project-level JWT secret. For simplicity we
# verify tokens by calling supabase.auth.get_user(access_token) which validates
# server-side. This is 1 network call per request but avoids managing JWKS.


async def _load_profile(user_id: str) -> Optional[dict]:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", user_id)
        return dict(row) if row else None


def _read_token(request: Request) -> tuple[str, str]:
    """Return (kind, token). kind is 'jwt' or 'emergent'."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return ("jwt", auth[7:].strip())
    # Emergent cookie session — set by /api/auth/emergent/session
    tok = request.cookies.get(EMERGENT_COOKIE, "")
    if tok:
        return ("emergent", tok)
    # Legacy cookie fallback (Supabase access_token stored in cookie)
    tok = request.cookies.get("access_token", "")
    if tok:
        return ("jwt", tok)
    raise HTTPException(status_code=401, detail="Missing bearer token")


async def _resolve_emergent_session(token: str) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, email, expires_at FROM emergent_sessions WHERE session_token = $1",
            token,
        )
    if not row:
        raise HTTPException(status_code=401, detail="Invalid session")
    expires_at = row["expires_at"]
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")

    profile = await _load_profile(str(row["user_id"])) or {}
    profile["user_id"] = str(row["user_id"])
    profile["email"] = row["email"]
    profile["name"] = profile.get("name") or row["email"].split("@")[0]
    profile.setdefault("role", "student")
    profile["auth_provider"] = "emergent"
    return profile


async def get_current_user(request: Request) -> dict:
    """Verify Supabase JWT or Emergent cookie session and return profile dict.
    Adds convenience keys: `user_id`, `email`, `name`, `role`."""
    kind, token = _read_token(request)
    if kind == "emergent":
        return await _resolve_emergent_session(token)

    supabase = get_supabase_admin()
    try:
        res = supabase.auth.get_user(token)
        u = res.user
        if not u:
            raise HTTPException(status_code=401, detail="Invalid session")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Supabase get_user failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid session")

    profile = await _load_profile(u.id)
    if not profile:
        # Trigger should have created it; create defensively
        pool = get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO profiles (id, email, name, role)
                VALUES ($1, $2, $3, 'student')
                ON CONFLICT (id) DO NOTHING
                RETURNING *
                """,
                u.id, u.email, (u.user_metadata or {}).get("name") or u.email.split("@")[0]
            )
            profile = dict(row) if row else await _load_profile(u.id)

    profile = profile or {}
    profile["user_id"] = str(u.id)
    profile["email"] = u.email
    profile["name"] = profile.get("name") or (u.user_metadata or {}).get("name") or u.email
    profile.setdefault("role", "student")
    return profile


async def get_current_teacher(request: Request) -> dict:
    user = await get_current_user(request)
    if user.get("role") not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teachers or admins only")
    return user


async def get_current_admin(request: Request) -> dict:
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user
