"""Idempotently create the seed users in Supabase Auth on startup."""
import logging
import random
import string

from config.database import get_pool, get_supabase_admin

logger = logging.getLogger(__name__)

SEEDS = [
    {"email": "admin@nexuacademy.com", "password": "nexuacademy123", "name": "NexUacademy Admin", "role": "admin"},
    {"email": "teacher@test.com",      "password": "password123",    "name": "Demo Teacher",       "role": "teacher"},
    {"email": "nitin@nexuacademy.com", "password": "nitin@123",      "name": "Nitin Saini",        "role": "teacher"},
    {"email": "student@test.com",      "password": "password123",    "name": "Demo Student",       "role": "student", "batch_id": "NEX2027"},
]


def _roll() -> str:
    alphabet = string.ascii_uppercase + string.digits
    for c in "OI01":
        alphabet = alphabet.replace(c, "")
    return "NXU-26" + "".join(random.choices(alphabet, k=6))


async def ensure_seed_users():
    supabase = get_supabase_admin()
    pool = get_pool()

    for s in SEEDS:
        # Check by email
        try:
            existing = supabase.auth.admin.list_users()
            found = next((u for u in existing if u.email == s["email"]), None)
        except Exception as e:
            logger.warning(f"admin.list_users failed: {e}")
            found = None

        user_id = None
        if not found:
            try:
                res = supabase.auth.admin.create_user({
                    "email": s["email"],
                    "password": s["password"],
                    "email_confirm": True,
                    "user_metadata": {"name": s["name"], "role": s["role"],
                                      "batch_id": s.get("batch_id", "")},
                })
                user_id = res.user.id
                logger.info(f"Seed user created: {s['email']}")
            except Exception as e:
                logger.warning(f"Seed create failed for {s['email']}: {e}")
                continue
        else:
            user_id = found.id
            # Ensure password is what we expect (helps in dev)
            try:
                supabase.auth.admin.update_user_by_id(user_id, {"password": s["password"]})
            except Exception:
                pass

        # Ensure profile row has role + batch + roll_number.
        # For student@test.com we force batch to NEX2027 (user request Feb-2026).
        async with pool.acquire() as conn:
            force_batch = s.get("batch_id") if s["email"] == "student@test.com" else None
            await conn.execute(
                """
                INSERT INTO profiles (id, email, name, role, batch_id, roll_number)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE
                   SET name = EXCLUDED.name,
                       role = EXCLUDED.role,
                       batch_id = COALESCE($7, profiles.batch_id, EXCLUDED.batch_id),
                       roll_number = COALESCE(profiles.roll_number, EXCLUDED.roll_number)
                """,
                user_id, s["email"], s["name"], s["role"], s.get("batch_id"), _roll(),
                force_batch,
            )
    logger.info("Seed users ensured")
