"""Profile routes — separate from admissions for backwards compat with /api/profile."""
from fastapi import APIRouter, Request, HTTPException
from middleware.auth import get_current_user
from config.database import get_pool

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me")
async def profile_me(request: Request):
    user = await get_current_user(request)
    return {"success": True, "user": {k: (v.isoformat() if hasattr(v, "isoformat") else v)
                                       for k, v in user.items()}}
