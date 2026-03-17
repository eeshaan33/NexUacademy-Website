from fastapi import APIRouter, Depends
from config.database import get_database
from middleware.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def get_notifications(user=Depends(get_current_user)):
    db = get_database()
    notifications = await db.notifications.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=20)

    unread_count = await db.notifications.count_documents(
        {"user_id": user["user_id"], "is_read": False}
    )
    return {"success": True, "notifications": notifications, "unread_count": unread_count}


@router.put("/{notification_id}/read")
async def mark_read(notification_id: str, user=Depends(get_current_user)):
    db = get_database()
    await db.notifications.update_one(
        {"user_id": user["user_id"], "notification_id": notification_id},
        {"$set": {"is_read": True}},
    )
    return {"success": True}


@router.put("/read-all")
async def mark_all_read(user=Depends(get_current_user)):
    db = get_database()
    await db.notifications.update_many(
        {"user_id": user["user_id"], "is_read": False},
        {"$set": {"is_read": True}},
    )
    return {"success": True}
