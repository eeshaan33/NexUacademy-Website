"""Supabase-backed database access.

Two clients are exposed:
  - `get_pool()` returns an asyncpg connection pool for raw SQL (server-role, RLS-bypass).
  - `get_supabase()` returns a supabase-py client (server-role, RLS-bypass) for
    Auth admin ops (create user, invite, reset password) and Storage.

Legacy `get_database()` remains but returns a stub that raises — every route
must migrate to the pool/supabase client.
"""
import os
import logging
from typing import Optional

import asyncpg
from supabase import create_client, Client

logger = logging.getLogger(__name__)

_POOL: Optional[asyncpg.Pool] = None
_SUPABASE: Optional[Client] = None


async def init_pool() -> asyncpg.Pool:
    global _POOL
    if _POOL is None:
        dsn = os.environ["DATABASE_URL"]
        _POOL = await asyncpg.create_pool(
            dsn=dsn,
            min_size=1,
            max_size=8,
            timeout=15,
            command_timeout=30,
            statement_cache_size=0,  # Supabase pooler requires this
            server_settings={"application_name": "nexuacademy-api"},
        )
        logger.info("Postgres pool initialised")
    return _POOL


def get_pool() -> asyncpg.Pool:
    if _POOL is None:
        raise RuntimeError("Postgres pool not initialised — call init_pool() at startup")
    return _POOL


def get_supabase() -> Client:
    global _SUPABASE
    if _SUPABASE is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _SUPABASE = create_client(url, key)
    return _SUPABASE


async def close_pool():
    global _POOL
    if _POOL:
        await _POOL.close()
        _POOL = None


# ---- Legacy shim so any un-migrated modules fail loudly instead of silently
class _LegacyMongoStub:
    def __getattr__(self, name):
        raise RuntimeError(
            "MongoDB has been removed. Route/service using db.%s must be migrated to Postgres." % name
        )

    def __call__(self, *_, **__):
        raise RuntimeError("MongoDB has been removed.")


def get_database():
    """Deprecated. Kept only so legacy imports don't crash at import time."""
    return _LegacyMongoStub()


async def connect_to_mongo():
    """Compat stub for old server.py — actually initialises Postgres pool now."""
    await init_pool()


async def close_mongo_connection():
    await close_pool()
