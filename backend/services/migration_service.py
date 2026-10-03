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

        # ---- emergent_sessions (Emergent-managed Google Auth cookie sessions)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.emergent_sessions (
                session_token TEXT PRIMARY KEY,
                user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
                email TEXT,
                expires_at TIMESTAMPTZ NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS emergent_sessions_user_idx ON public.emergent_sessions(user_id)"
        )

        # ---- Question Bank (topics, subtopics, questions, per-batch assignment ledger)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.topics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL UNIQUE,
                subject TEXT,
                created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.subtopics (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                topic_id UUID NOT NULL REFERENCES public.topics(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (topic_id, name)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.question_bank (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                topic_id UUID NOT NULL REFERENCES public.topics(id),
                subtopic_id UUID NOT NULL REFERENCES public.subtopics(id),
                question_text TEXT,
                question_image_url TEXT,
                question_type TEXT NOT NULL DEFAULT 'MCQ_Single'
                    CHECK (question_type IN ('MCQ_Single','MCQ_Multiple','Numerical_Integer','Numerical_Decimal')),
                options JSONB DEFAULT '{}'::jsonb,
                correct_answers TEXT[] DEFAULT '{}',
                numerical_answer NUMERIC,
                answer_range JSONB,
                difficulty TEXT CHECK (difficulty IN ('Easy','Medium','Hard')),
                marks INTEGER DEFAULT 4,
                negative_marks INTEGER DEFAULT -1,
                teacher_note TEXT,
                created_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.question_batch_assignments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                question_id UUID NOT NULL REFERENCES public.question_bank(id) ON DELETE CASCADE,
                batch_code TEXT NOT NULL,
                test_id TEXT REFERENCES public.tests(test_id) ON DELETE SET NULL,
                assigned_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (question_id, batch_code)
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_qbank_topic_subtopic ON public.question_bank(topic_id, subtopic_id)"
        )
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_qba_batch ON public.question_batch_assignments(batch_code)"
        )
        # Normalize batch_code on assignment inserts
        await conn.execute("""
            CREATE OR REPLACE FUNCTION public.normalize_qba_batch() RETURNS trigger AS $$
            BEGIN
                NEW.batch_code := UPPER(TRIM(NEW.batch_code));
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)
        await conn.execute(
            "DROP TRIGGER IF EXISTS qba_normalize ON public.question_batch_assignments"
        )
        await conn.execute("""
            CREATE TRIGGER qba_normalize BEFORE INSERT OR UPDATE
                ON public.question_batch_assignments
                FOR EACH ROW EXECUTE FUNCTION public.normalize_qba_batch();
        """)

        # add solution/hint enrichment cols (YouTube + image/video) — idempotent
        await conn.execute("""
            ALTER TABLE public.question_bank
                ADD COLUMN IF NOT EXISTS solution_youtube_url TEXT,
                ADD COLUMN IF NOT EXISTS solution_media_url   TEXT,
                ADD COLUMN IF NOT EXISTS solution_media_type  TEXT
                    CHECK (solution_media_type IN ('image','video'))
        """)

        # ---- QB FOLDER HIERARCHY (Feb 2026 refactor) --------------------------
        # Fixed tree: PYQ / Non-PYQ  →  exam / subject / (section / subject)
        # Replaces the dynamic topics/subtopics model for Question Bank.
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.qb_folders (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                parent_id UUID REFERENCES public.qb_folders(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                path TEXT NOT NULL UNIQUE,
                level INT NOT NULL,
                is_leaf BOOLEAN NOT NULL DEFAULT FALSE,
                sort_order INT NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_qb_folders_parent ON public.qb_folders(parent_id)"
        )
        # Add folder_id on question_bank, nullable (legacy rows have none)
        # and relax topic/subtopic FKs so new rows can skip them.
        await conn.execute("""
            ALTER TABLE public.question_bank
                ADD COLUMN IF NOT EXISTS folder_id UUID REFERENCES public.qb_folders(id)
        """)
        await conn.execute("""
            DO $$ BEGIN
              ALTER TABLE public.question_bank ALTER COLUMN topic_id DROP NOT NULL;
              ALTER TABLE public.question_bank ALTER COLUMN subtopic_id DROP NOT NULL;
            EXCEPTION WHEN others THEN NULL; END $$;
        """)
        # Difficulty: accept Easy / Moderate / Difficult (new standard) + legacy
        await conn.execute("""
            DO $$ BEGIN
              ALTER TABLE public.question_bank DROP CONSTRAINT IF EXISTS question_bank_difficulty_check;
            EXCEPTION WHEN others THEN NULL; END $$;
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_qbank_folder ON public.question_bank(folder_id)"
        )

        # Seed the fixed folder hierarchy (idempotent — ON CONFLICT DO NOTHING)
        FOLDER_SEED = [
            # (path, level, is_leaf, sort_order)
            ("PYQ", 0, False, 1),
            ("PYQ/JEE", 1, False, 1),
            ("PYQ/JEE/JEE Mains", 2, False, 1),
            ("PYQ/JEE/JEE Mains/Physics", 3, True, 1),
            ("PYQ/JEE/JEE Mains/Chemistry", 3, True, 2),
            ("PYQ/JEE/JEE Mains/Maths", 3, True, 3),
            ("PYQ/JEE/JEE Advanced", 2, False, 2),
            ("PYQ/JEE/JEE Advanced/Physics", 3, True, 1),
            ("PYQ/JEE/JEE Advanced/Chemistry", 3, True, 2),
            ("PYQ/JEE/JEE Advanced/Maths", 3, True, 3),
            ("PYQ/NEET", 1, False, 2),
            ("PYQ/NEET/Physics", 2, True, 1),
            ("PYQ/NEET/Chemistry", 2, True, 2),
            ("PYQ/NEET/Biology", 2, True, 3),
            ("PYQ/Olympiads", 1, False, 3),
            ("PYQ/Olympiads/NSEP", 2, True, 1),
            ("PYQ/Olympiads/NSEC", 2, True, 2),
            ("PYQ/Olympiads/NSEB", 2, True, 3),
            ("PYQ/Olympiads/NSEA", 2, True, 4),
            ("PYQ/Olympiads/NSEJS", 2, True, 5),
            ("Non-PYQ", 0, False, 2),
            ("Non-PYQ/Physics", 1, True, 1),
            ("Non-PYQ/Chemistry", 1, True, 2),
            ("Non-PYQ/Maths", 1, True, 3),
            ("Non-PYQ/Biology", 1, True, 4),
        ]
        for path, level, is_leaf, order in FOLDER_SEED:
            parent_path = path.rsplit("/", 1)[0] if "/" in path else None
            name = path.rsplit("/", 1)[-1]
            await conn.execute(
                """
                INSERT INTO public.qb_folders (parent_id, name, path, level, is_leaf, sort_order)
                VALUES (
                    (SELECT id FROM public.qb_folders WHERE path = $1),
                    $2, $3, $4, $5, $6
                )
                ON CONFLICT (path) DO NOTHING
                """,
                parent_path, name, path, level, is_leaf, order,
            )
        # Prune any legacy / stray folders that don't match the master tree
        allowed_paths = [p for p, *_ in FOLDER_SEED]
        await conn.execute(
            "DELETE FROM public.qb_folders WHERE path <> ALL($1::text[])",
            allowed_paths,
        )

        # ---- SELF-REPORTED ERROR TAGS on test attempts -----------------------
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.attempt_error_tags (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                attempt_id TEXT NOT NULL REFERENCES public.test_attempts(attempt_id) ON DELETE CASCADE,
                question_number INT NOT NULL,
                error_tag TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (attempt_id, question_number)
            )
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_err_tags_attempt ON public.attempt_error_tags(attempt_id)"
        )

        # ---- OTP + trusted-device store (email OTP on signup + new-device login)
        await conn.execute("""
            ALTER TABLE public.profiles
                ADD COLUMN IF NOT EXISTS phone TEXT,
                ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ,
                ADD COLUMN IF NOT EXISTS phone_verified_at TIMESTAMPTZ
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.auth_otps (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                purpose TEXT NOT NULL CHECK (purpose IN ('signup','login','email_verify')),
                payload JSONB,
                attempts INTEGER NOT NULL DEFAULT 0,
                expires_at TIMESTAMPTZ NOT NULL,
                verified_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        # If table already existed with the old check constraint, migrate it.
        await conn.execute("""
            DO $$ BEGIN
              ALTER TABLE public.auth_otps DROP CONSTRAINT IF EXISTS auth_otps_purpose_check;
              ALTER TABLE public.auth_otps
                ADD CONSTRAINT auth_otps_purpose_check
                CHECK (purpose IN ('signup','login','email_verify'));
            EXCEPTION WHEN others THEN NULL; END $$;
        """)
        await conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_otps_email ON public.auth_otps(email, purpose, created_at DESC)"
        )
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS public.trusted_devices (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
                device_id TEXT NOT NULL,
                last_ip TEXT,
                last_seen_at TIMESTAMPTZ DEFAULT NOW(),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (user_id, device_id)
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


async def cleanup_batches():
    """One-shot cleanup requested by admin (Feb 2026):
    Move every student currently in JEEM2027 → NEX2027 so all JEE Mains 2027
    students land in the NexUacademy 2027 batch. Idempotent.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        # Only run if NEX2027 exists to avoid an FK violation.
        exists = await conn.fetchval("SELECT 1 FROM batches WHERE id = 'NEX2027'")
        if not exists:
            logger.info("cleanup_batches: NEX2027 batch not found, skipping")
            return
        moved = await conn.fetchval(
            """
            WITH updated AS (
                UPDATE profiles SET batch_id = 'NEX2027'
                 WHERE batch_id = 'JEEM2027' AND role = 'student'
                 RETURNING 1
            )
            SELECT count(*) FROM updated
            """
        )
        logger.info(f"cleanup_batches: moved {moved or 0} JEEM2027 students → NEX2027")
