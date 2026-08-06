"""Student-side classes: list, mark-attendance."""
from fastapi import APIRouter, Depends
from config.database import get_pool
from middleware.auth import get_current_user
from services.pg_utils import json_safe

router = APIRouter(prefix="/student/classes", tags=["student-classes"])


@router.get("/my-classes")
async def my_classes(user=Depends(get_current_user)):
    pool = get_pool()
    batch = user.get("batch_id")
    if not batch:
        return {"success": True, "classes": []}
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM classes WHERE $1 = ANY(assigned_batches) ORDER BY scheduled_date_time ASC",
            batch,
        )
    return {"success": True, "classes": [json_safe(r) for r in rows]}
