"""Auth middleware — verifies Supabase Auth JWTs and loads the user's profile."""
import os
import logging
from typing import Optional

import jwt
from fastapi import HTTPException, Request, status
from jwt import PyJWKClient

from config.database import get_pool, get_supabase

logger = logging.getLogger(__name__)

# Supabase issues JWTs signed with a project-level JWT secret. For simplicity we
# verify tokens by calling supabase.auth.get_user(access_token) which validates
# server-side. This is 1 network call per request but avoids managing JWKS.


async def _load_profile(user_id: str) -> Optional[dict]:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM profiles WHERE id = $1", user_id)
        return dict(row) if row else None


def _read_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    # Cookie fallback for browser sessions we set manually
    tok = request.cookies.get("access_token", "")
    if tok:
        return tok
    raise HTTPException(status_code=401, detail="Missing bearer token")


async def get_current_user(request: Request) -> dict:
    """Verify Supabase Auth JWT and return the merged profile dict.
    Adds convenience keys: `user_id`, `email`, `name`, `role`."""
    token = _read_token(request)
    supabase = get_supabase()
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
