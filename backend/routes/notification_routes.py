"""Simple in-app notifications API."""
from fastapi import APIRouter, Depends, HTTPException
from config.database import get_pool
from middleware.auth import get_current_user
from services.pg_utils import json_safe

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def list_notifications(user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM notifications WHERE user_id = $1 ORDER BY created_at DESC LIMIT 100",
            user["user_id"],
        )
        unread = await conn.fetchval(
            "SELECT count(*) FROM notifications WHERE user_id = $1 AND is_read = false",
            user["user_id"],
        )
    return {"notifications": [json_safe(r) for r in rows], "unread_count": unread or 0}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE notifications SET is_read = true WHERE notification_id = $1 AND user_id = $2",
            notification_id, user["user_id"],
        )
    return {"success": True}


@router.post("/mark-all-read")
async def mark_all_read(user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE notifications SET is_read = true WHERE user_id = $1 AND is_read = false",
            user["user_id"],
        )
    return {"success": True}
