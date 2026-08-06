"""Batches — Postgres-backed. Read is public; write requires teacher/admin."""
import random
import string
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config.database import get_pool
from middleware.auth import get_current_teacher

router = APIRouter(prefix="/batches", tags=["batches"])
logger = logging.getLogger(__name__)


class BatchCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    year: int = Field(..., ge=2024, le=2035)
    code: Optional[str] = Field(None, min_length=4, max_length=16)


def _gen_code(length: int = 8) -> str:
    alphabet = "".join(c for c in (string.ascii_uppercase + string.digits) if c not in "OI01")
    return "".join(random.choices(alphabet, k=length))


async def _unique_code(conn) -> str:
    for _ in range(20):
        code = _gen_code()
        exists = await conn.fetchval("SELECT 1 FROM batches WHERE code = $1", code)
        if not exists:
            return code
    return _gen_code(10)


@router.get("/")
async def list_batches():
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM batches ORDER BY is_predefined DESC, created_at ASC")
    return {"success": True, "batches": [
        {**dict(r), "created_at": r["created_at"].isoformat() if r["created_at"] else None}
        for r in rows
    ]}


@router.get("/by-code/{code}")
async def get_by_code(code: str):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM batches WHERE code = $1", code.strip().upper())
    if not row:
        raise HTTPException(status_code=404, detail=f"Batch '{code}' not recognised. Please check with your teacher.")
    return {"success": True, "batch": {**dict(row), "created_at": row["created_at"].isoformat() if row["created_at"] else None}}


@router.post("/")
async def create_batch(payload: BatchCreateRequest, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        # Auto-code or validate provided code
        if payload.code:
            code = payload.code.strip().upper()
            if not code.isalnum():
                raise HTTPException(status_code=400, detail="Batch code must be alphanumeric")
            if await conn.fetchval("SELECT 1 FROM batches WHERE code = $1", code):
                raise HTTPException(status_code=400, detail="Batch code already taken")
        else:
            code = await _unique_code(conn)

        # Name uniqueness
        if await conn.fetchval("SELECT 1 FROM batches WHERE name = $1", payload.name):
            raise HTTPException(status_code=400, detail="Batch with this name already exists")

        row = await conn.fetchrow(
            """
            INSERT INTO batches (id, code, name, year, is_predefined, is_custom, created_by, created_by_id)
            VALUES ($1, $1, $2, $3, false, true, $4, $5)
            RETURNING *
            """,
            code, payload.name, payload.year, user.get("name"), user.get("user_id"),
        )
    return {"success": True, "batch": {**dict(row), "created_at": row["created_at"].isoformat()}}


@router.delete("/{batch_id}")
async def delete_batch(batch_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM batches WHERE id = $1", batch_id.strip().upper())
        if not row:
            raise HTTPException(status_code=404, detail="Batch not found")
        if row["is_predefined"]:
            raise HTTPException(status_code=400, detail="Predefined batches cannot be deleted")
        if user["role"] != "admin" and str(row["created_by_id"]) != str(user["user_id"]):
            raise HTTPException(status_code=403, detail="Not the owner")
        await conn.execute("DELETE FROM batches WHERE id = $1", batch_id.strip().upper())
    return {"success": True, "message": "Batch deleted"}
