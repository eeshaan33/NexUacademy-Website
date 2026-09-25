"""Admin-only central contacts store: name / email / phone / verification / role.

Powered by the same `profiles` table — no separate contacts collection.
"""
import csv
import io
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from config.database import get_pool
from middleware.auth import get_current_admin
from services.pg_utils import json_safe

router = APIRouter(prefix="/admin/contacts", tags=["admin-contacts"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_contacts(user=Depends(get_current_admin)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, name, email, phone, role, batch_id,
                      email_verified_at, phone_verified_at, created_at
                 FROM profiles
                ORDER BY created_at DESC"""
        )
    return {"success": True, "contacts": [json_safe(r) for r in rows], "total": len(rows)}


@router.get("/export.csv")
async def export_csv(request: Request):
    # Support Authorization header OR ?token= for a direct browser download link
    user = await get_current_admin(request)
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT name, email, phone, role, batch_id,
                      email_verified_at, phone_verified_at, created_at
                 FROM profiles
                ORDER BY created_at DESC"""
        )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Name", "Email", "Phone", "Role", "Batch",
        "Email Verified", "Phone Verified", "Signed Up",
    ])
    for r in rows:
        writer.writerow([
            r["name"] or "",
            r["email"] or "",
            r["phone"] or "",
            r["role"] or "",
            r["batch_id"] or "",
            r["email_verified_at"].isoformat() if r["email_verified_at"] else "",
            r["phone_verified_at"].isoformat() if r["phone_verified_at"] else "",
            r["created_at"].isoformat() if r["created_at"] else "",
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="nexuacademy-contacts.csv"'},
    )
