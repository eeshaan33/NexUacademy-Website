"""Push subscription management — stores browser Push Subscription on the profile row."""
import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from config.database import get_pool
from middleware.auth import get_current_user

router = APIRouter(prefix="/push", tags=["push"])


class PushSubPayload(BaseModel):
    endpoint: str
    keys: dict


@router.post("/subscribe")
async def subscribe(payload: PushSubPayload, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE profiles SET push_subscription = $1::jsonb, notifications_enabled = true WHERE id = $2",
            json.dumps(payload.dict()), user["user_id"],
        )
    return {"success": True}


@router.post("/unsubscribe")
async def unsubscribe(user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE profiles SET push_subscription = NULL WHERE id = $1", user["user_id"],
        )
    return {"success": True}
