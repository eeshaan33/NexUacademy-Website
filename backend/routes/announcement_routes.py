"""Announcements — teacher/admin posts, students see their batch's announcements.
Part 5 requirement."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from config.database import get_pool
from middleware.auth import get_current_user, get_current_teacher
from services.push_service import notify_students_about_announcement
from services.pg_utils import short_id, json_safe

router = APIRouter(prefix="/announcements", tags=["announcements"])


class AnnouncementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    assigned_batches: List[str]
    is_pinned: Optional[bool] = False


@router.post("/")
async def create_announcement(payload: AnnouncementCreate, user=Depends(get_current_teacher)):
    batches = [b.strip().upper() for b in payload.assigned_batches if b.strip()]
    if not batches:
        raise HTTPException(status_code=400, detail="At least one batch is required")
    ann_id = short_id("ann")
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO announcements (announcement_id, title, message, assigned_batches,
                created_by, created_by_name, is_pinned)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            ann_id, payload.title, payload.message, batches,
            user["user_id"], user["name"], payload.is_pinned,
        )
    doc = json_safe(row)
    try:
        await notify_students_about_announcement(doc)
    except Exception:
        pass
    return {"success": True, "announcement": doc}


@router.get("/")
async def list_announcements(user=Depends(get_current_user)):
    """List announcements: teachers/admins see everything, students see their batch."""
    pool = get_pool()
    async with pool.acquire() as conn:
        if user["role"] in ("teacher", "admin"):
            rows = await conn.fetch(
                "SELECT * FROM announcements ORDER BY is_pinned DESC, created_at DESC LIMIT 100"
            )
        else:
            batch = user.get("batch_id")
            if not batch:
                return {"success": True, "announcements": []}
            rows = await conn.fetch(
                """SELECT * FROM announcements WHERE $1 = ANY(assigned_batches)
                   ORDER BY is_pinned DESC, created_at DESC LIMIT 100""",
                batch,
            )
    return {"success": True, "announcements": [json_safe(r) for r in rows]}


@router.delete("/{announcement_id}")
async def delete_announcement(announcement_id: str, user=Depends(get_current_teacher)):
    pool = get_pool()
    async with pool.acquire() as conn:
        ann = await conn.fetchrow("SELECT created_by FROM announcements WHERE announcement_id = $1", announcement_id)
        if not ann:
            raise HTTPException(status_code=404, detail="Announcement not found")
        if user["role"] != "admin" and str(ann["created_by"]) != str(user["user_id"]):
            raise HTTPException(status_code=403, detail="Not the author")
        await conn.execute("DELETE FROM announcements WHERE announcement_id = $1", announcement_id)
    return {"success": True}
