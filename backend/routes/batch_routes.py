from fastapi import APIRouter
from config.batches import PREDEFINED_BATCHES

router = APIRouter(prefix="/batches", tags=["batches"])


@router.get("/")
async def get_batches():
    return {"success": True, "batches": PREDEFINED_BATCHES}
