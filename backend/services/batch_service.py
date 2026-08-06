"""
Centralized batch + roll-number helpers.

A "batch" is uniquely identified by:
  - id   = legacy human-readable name (kept for backwards compat with
           existing queries that filter on `assigned_batches: <name>` and
           `users.batch_id: <name>`)
  - code = short alphanumeric join-code (8 chars, uppercase). What students
           type into the admission form to join the batch.

Predefined batches are auto-seeded on startup with deterministic codes.
"""
import random
import string
from datetime import datetime, timezone

from config.batches import PREDEFINED_BATCHES
from config.database import get_database


def _generate_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    # Avoid easily-confused characters
    alphabet = alphabet.replace("O", "").replace("I", "").replace("0", "").replace("1", "")
    return "".join(random.choices(alphabet, k=length))


# Deterministic codes for the original predefined batches so existing
# students/links keep working.
_PREDEFINED_CODE_MAP = {
    "JEE Mains 2027": "JEEM2027",
    "JEE Mains 2028": "JEEM2028",
    "JEE Mains 2029": "JEEM2029",
    "JEE Advance 2027": "JEEA2027",
    "JEE Advance 2028": "JEEA2028",
    "NEX2027": "NEX2027",
    "NEX2028": "NEX2028",
}


async def ensure_batch_codes_seeded():
    """Backfill `batches` collection with predefined batches + codes."""
    db = get_database()
    for b in PREDEFINED_BATCHES:
        existing = await db.batches.find_one({"id": b["id"]})
        if existing:
            # Make sure code field is present
            if not existing.get("code"):
                code = _PREDEFINED_CODE_MAP.get(b["id"]) or await _unique_code()
                await db.batches.update_one({"id": b["id"]}, {"$set": {"code": code}})
            continue
        code = _PREDEFINED_CODE_MAP.get(b["id"]) or await _unique_code()
        await db.batches.insert_one({
            "id": b["id"],
            "name": b["name"],
            "year": b.get("year"),
            "code": code,
            "is_predefined": True,
            "is_custom": False,
            "created_by": "system",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })


async def _unique_code() -> str:
    db = get_database()
    for _ in range(20):
        code = _generate_code()
        if not await db.batches.find_one({"code": code}):
            return code
    # Fallback: longer code
    return _generate_code(10)


async def list_all_batches():
    """Return merged list of batches (predefined + custom). Always includes
    `code` field. Falls back to seeding if `batches` collection is empty."""
    db = get_database()
    docs = await db.batches.find({}, {"_id": 0}).sort("created_at", 1).to_list(length=500)
    if not docs:
        await ensure_batch_codes_seeded()
        docs = await db.batches.find({}, {"_id": 0}).sort("created_at", 1).to_list(length=500)

    # Also include legacy `custom_batches` rows that pre-date this collection.
    legacy = await db.custom_batches.find({}, {"_id": 0}).to_list(length=500)
    seen_ids = {d["id"] for d in docs}
    for b in legacy:
        if b.get("id") in seen_ids:
            continue
        code = await _unique_code()
        merged = {
            "id": b["id"],
            "name": b["name"],
            "year": b.get("year"),
            "code": code,
            "is_predefined": False,
            "is_custom": True,
            "created_by": b.get("created_by"),
            "created_by_id": b.get("created_by_id"),
            "created_at": b.get("created_at") or datetime.now(timezone.utc).isoformat(),
        }
        await db.batches.insert_one(dict(merged))
        merged.pop("_id", None)
        docs.append(merged)
        seen_ids.add(b["id"])

    return docs


async def find_batch_by_code(code: str):
    db = get_database()
    if not code:
        return None
    return await db.batches.find_one({"code": code.strip().upper()}, {"_id": 0})


async def generate_roll_number() -> str:
    """Generate a unique, short, human-friendly roll number.
    Format: NXU-<YY><RANDOM6>  e.g. NXU-26K7QPM3
    """
    db = get_database()
    yy = datetime.now(timezone.utc).strftime("%y")
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace("O", "").replace("I", "").replace("0", "").replace("1", "")
    for _ in range(20):
        suffix = "".join(random.choices(alphabet, k=6))
        roll = f"NXU-{yy}{suffix}"
        if not await db.users.find_one({"roll_number": roll}):
            return roll
    # Fallback
    return f"NXU-{yy}{''.join(random.choices(alphabet, k=10))}"
