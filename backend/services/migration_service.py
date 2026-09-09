"""Idempotent DB migrations for tier system + student_applications + preseed roster.

Runs on every backend startup. Uses `IF NOT EXISTS` / `ALTER TABLE ... ADD COLUMN
IF NOT EXISTS` so it is safe to re-run.
"""
import logging

from config.database import get_pool

logger = logging.getLogger(__name__)


# NEX2027 + Shefali (19 total), NEX2028 (2). First names only — case-insensitive
# matching on claim. Default password = firstname_lower + batch_year.
PRESEED_ROSTER = [
    # NEX2027
    ("Arjun", "NEX2027"),
    ("Garvit", "NEX2027"),
    ("Khushi", "NEX2027"),
    ("Kartavya", "NEX2027"),
    ("Kovid", "NEX2027"),
    ("Krisha", "NEX2027"),
    ("Naavya", "NEX2027"),
    ("Pragya", "NEX2027"),
    ("Abhinav", "NEX2027"),
    ("Vivaan", "NEX2027"),
    ("Urveesh", "NEX2027"),
    ("Yashasvi", "NEX2027"),
    ("Madhav", "NEX2027"),
    ("Aniket", "NEX2027"),
    ("Rittam", "NEX2027"),
    ("Eeshaan", "NEX2027"),
    ("Aaryan", "NEX2027"),
    ("Ayush", "NEX2027"),
    ("Shefali", "NEX2027"),
    # NEX2028
    ("Shantanu", "NEX2028"),
    ("Pranit", "NEX2028"),
]


def default_password_for(first_name: str, batch_id: str) -> str:
    """firstname lowercase (no spaces) + batch year (last 4 chars of batch_id)."""
    year = "".join(c for c in (batch_id or "") if c.isdigit())[-4:] or "2027"
    return f"{first_name.strip().lower().replace(' ', '')}{year}"


async def run_migrations():
    pool = get_pool()
    async with pool.acquire() as conn:
        # ---- profiles: add tier columns
        await conn.execute("""
            ALTER TABLE public.profiles
                ADD COLUMN IF NOT EXISTS access_tier TEXT DEFAULT 'free',
                ADD COLUMN IF NOT EXISTS is_existing_student BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS whatsapp_number TEXT,
                ADD COLUMN IF NOT EXISTS payment_status TEXT DEFAULT 'pending',
                ADD COLUMN IF NOT EXISTS payment_completed_at TIMESTAMPTZ
        """)

        # ---- payments table (create if missing — earlier migrations may have skipped)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.payments (
                payment_id TEXT PRIMARY KEY,
                user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
                razorpay_order_id TEXT UNIQUE,
                razorpay_payment_id TEXT,
                razorpay_signature TEXT,
                amount INTEGER NOT NULL,
                currency TEXT DEFAULT 'INR',
                plan TEXT DEFAULT 'admission_fee',
                status TEXT DEFAULT 'created',
                receipt TEXT,
                notes JSONB DEFAULT '{}'::jsonb,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                paid_at TIMESTAMPTZ,
                failed_at TIMESTAMPTZ
            )
        """)

        # ---- student_applications (3-field public admission form)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.student_applications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                whatsapp_number TEXT NOT NULL,
                payment_status TEXT DEFAULT 'pending',
                amount_paid NUMERIC DEFAULT 30000,
                user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
                razorpay_order_id TEXT
            )
        """)

        # ---- preseed_students (whitelist for first-time claim)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.preseed_students (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                first_name TEXT NOT NULL,
                first_name_lower TEXT GENERATED ALWAYS AS (lower(first_name)) STORED,
                batch_id TEXT NOT NULL,
                default_password TEXT NOT NULL,
                claimed_email TEXT UNIQUE,
                claimed_at TIMESTAMPTZ,
                claimed_user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
                UNIQUE (first_name_lower, batch_id)
            )
        """)

        # Seed roster (idempotent — ON CONFLICT DO NOTHING)
        for first_name, batch_id in PRESEED_ROSTER:
            await conn.execute(
                """
                INSERT INTO public.preseed_students (first_name, batch_id, default_password)
                VALUES ($1, $2, $3)
                ON CONFLICT (first_name_lower, batch_id) DO NOTHING
                """,
                first_name, batch_id, default_password_for(first_name, batch_id),
            )

    logger.info(
        "Migrations complete — profiles tier cols + student_applications + "
        f"preseed_students ({len(PRESEED_ROSTER)} rows)"
    )
