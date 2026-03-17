import os
from fastapi import APIRouter, Request, Depends
from config.database import get_database
from middleware.auth import get_current_user

router = APIRouter(prefix="/push", tags=["push-notifications"])


@router.post("/subscribe")
async def subscribe(request: Request, user=Depends(get_current_user)):
    db = get_database()
    body = await request.json()
    subscription = body.get("subscription")
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"push_subscription": subscription, "notifications_enabled": True}},
    )
    return {"success": True, "message": "Subscribed to notifications"}


@router.post("/unsubscribe")
async def unsubscribe(user=Depends(get_current_user)):
    db = get_database()
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"push_subscription": None, "notifications_enabled": False}},
    )
    return {"success": True, "message": "Unsubscribed from notifications"}


@router.get("/vapid-public-key")
async def get_vapid_key():
    return {"public_key": os.environ.get("VAPID_PUBLIC_KEY", "")}
