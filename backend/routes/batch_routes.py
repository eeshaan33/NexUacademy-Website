from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Optional

from config.batches import PREDEFINED_BATCHES
from config.database import get_database
from middleware.auth import get_current_user, get_current_teacher
from services.batch_service import (
    list_all_batches,
    find_batch_by_code,
    _unique_code,
    ensure_batch_codes_seeded,
)

router = APIRouter(prefix="/batches", tags=["batches"])


class BatchCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    year: int = Field(..., ge=2024, le=2035)
    code: Optional[str] = Field(None, min_length=4, max_length=16)


@router.get("/")
async def get_batches():
    """Return predefined + custom batches with codes."""
    batches = await list_all_batches()
    return {"success": True, "batches": batches}


@router.get("/by-code/{code}")
async def get_batch_by_code(code: str):
    """Public endpoint to verify a batch code (used by admission form)."""
    batch = await find_batch_by_code(code)
    if not batch:
        raise HTTPException(status_code=404, detail="Invalid batch code")
    return {"success": True, "batch": batch}


@router.post("/")
async def create_batch(payload: BatchCreateRequest, user=Depends(get_current_teacher)):
    """Teachers/admins can create a custom batch with an alphanumeric join code."""
    db = get_database()
    await ensure_batch_codes_seeded()

    predefined_names = {b["name"].lower() for b in PREDEFINED_BATCHES}
    if payload.name.lower() in predefined_names:
        raise HTTPException(status_code=400, detail="This batch name is already predefined")

    existing_name = await db.batches.find_one({"name": payload.name})
    if existing_name:
        raise HTTPException(status_code=400, detail="Batch with this name already exists")

    # Resolve code: admin-supplied (alphanumeric) or auto-generated
    if payload.code:
        code = payload.code.strip().upper()
        if not code.isalnum():
            raise HTTPException(status_code=400, detail="Batch code must be alphanumeric")
        existing_code = await db.batches.find_one({"code": code})
        if existing_code:
            raise HTTPException(status_code=400, detail="Batch code already taken, pick another")
    else:
        code = await _unique_code()

    batch_id = payload.name  # human-readable id (kept for backwards compat)
    doc = {
        "id": batch_id,
        "name": payload.name,
        "year": payload.year,
        "code": code,
        "is_predefined": False,
        "is_custom": True,
        "created_by": user.get("name"),
        "created_by_id": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.batches.insert_one(dict(doc))
    # Also write to legacy collection for any older code path still reading it
    await db.custom_batches.update_one(
        {"id": batch_id}, {"$set": {**doc}}, upsert=True
    )
    doc.pop("_id", None)
    return {"success": True, "batch": doc}


@router.delete("/{batch_id}")
async def delete_batch(batch_id: str, user=Depends(get_current_teacher)):
    db = get_database()
    predefined_ids = {b["id"] for b in PREDEFINED_BATCHES}
    if batch_id in predefined_ids:
        raise HTTPException(status_code=400, detail="Predefined batches cannot be deleted")

    query = {"id": batch_id}
    if user.get("role") != "admin":
        query["created_by_id"] = user.get("user_id")

    res = await db.batches.delete_one(query)
    await db.custom_batches.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Batch not found (or not owned by you)")

    # Unassign any students still pointing at that batch
    await db.users.update_many(
        {"batch_id": batch_id},
        {"$set": {"batch_id": None}},
    )
    return {"success": True, "message": "Batch deleted"}
