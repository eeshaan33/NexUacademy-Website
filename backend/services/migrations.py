"""One-time idempotent migrations run on backend startup."""
import logging
from datetime import datetime, timezone
from config.database import get_database
from services.batch_service import (
    ensure_batch_codes_seeded,
    list_all_batches,
    generate_roll_number,
)

logger = logging.getLogger(__name__)


async def backfill_student_batches_and_rolls():
    """For every existing student missing batch_id / roll_number, populate them
    from their admission record (course_applying → batch_id) and generate a roll
    number if missing."""
    db = get_database()

    # 1. Ensure all batches (predefined + legacy custom) live in `batches` with codes
    await ensure_batch_codes_seeded()
    await list_all_batches()

    cursor = db.users.find({"role": "student"}, {"_id": 0})
    fixed_batch = 0
    fixed_roll = 0
    async for u in cursor:
        updates = {}

        if not u.get("batch_id"):
            # Try to recover from admission record
            adm = None
            if u.get("admission_id"):
                adm = await db.admissions.find_one({"admission_id": u["admission_id"]}, {"_id": 0})
            target_batch_id = None
            if adm and adm.get("batch_id"):
                target_batch_id = adm["batch_id"]
            elif adm and adm.get("course_applying"):
                # Look up by name/id
                b = await db.batches.find_one({"id": adm["course_applying"]}, {"_id": 0})
                if b:
                    target_batch_id = b["id"]
                else:
                    target_batch_id = adm["course_applying"]  # legacy free-text
            if target_batch_id:
                updates["batch_id"] = target_batch_id
                fixed_batch += 1

        if not u.get("roll_number"):
            updates["roll_number"] = await generate_roll_number()
            fixed_roll += 1

        if "notifications_enabled" not in u:
            updates["notifications_enabled"] = True

        if updates:
            updates["updated_at"] = datetime.now(timezone.utc).isoformat()
            await db.users.update_one({"user_id": u["user_id"]}, {"$set": updates})

    if fixed_batch or fixed_roll:
        logger.info(f"Backfill: {fixed_batch} students got batch_id, {fixed_roll} got roll numbers")
    else:
        logger.info("Backfill: nothing to migrate")
