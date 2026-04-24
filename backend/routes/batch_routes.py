from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

from config.batches import PREDEFINED_BATCHES
from config.database import get_database
from middleware.auth import get_current_user, get_current_teacher

router = APIRouter(prefix="/batches", tags=["batches"])


class BatchCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    year: int = Field(..., ge=2024, le=2035)


@router.get("/")
async def get_batches():
    """Return predefined + custom batches (de-duplicated)."""
    db = get_database()
    custom = await db.custom_batches.find({}, {"_id": 0}).sort("created_at", -1).to_list(length=200)
    seen = {b["id"] for b in PREDEFINED_BATCHES}
    merged = list(PREDEFINED_BATCHES)
    for b in custom:
        if b.get("id") in seen:
            continue
        seen.add(b["id"])
        merged.append({
            "id": b["id"],
            "name": b["name"],
            "year": b.get("year"),
            "is_custom": True,
            "created_by": b.get("created_by"),
            "created_by_id": b.get("created_by_id"),
        })
    return {"success": True, "batches": merged}


@router.post("/")
async def create_batch(payload: BatchCreateRequest, user=Depends(get_current_teacher)):
    """Teachers/admins can create a custom batch name."""
    db = get_database()

    predefined_names = {b["name"].lower() for b in PREDEFINED_BATCHES}
    if payload.name.lower() in predefined_names:
        raise HTTPException(status_code=400, detail="This batch name is already predefined")

    existing = await db.custom_batches.find_one({"name": payload.name})
    if existing:
        raise HTTPException(status_code=400, detail="Batch with this name already exists")

    batch_id = payload.name  # use human-readable id so existing batch_id-based filters keep working
    doc = {
        "id": batch_id,
        "name": payload.name,
        "year": payload.year,
        "is_custom": True,
        "created_by": user.get("name"),
        "created_by_id": user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.custom_batches.insert_one(doc)
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

    res = await db.custom_batches.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Batch not found (or not owned by you)")

    # Unassign any students still pointing at that batch
    await db.users.update_many(
        {"batch_id": batch_id},
        {"$set": {"batch_id": None}},
    )
    return {"success": True, "message": "Batch deleted"}
