from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
import asyncio
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import route modules (migrated to Supabase/Postgres)
from routes import (
    auth_routes,
    emergent_auth_routes,
    batch_routes,
    admission_routes,
    teacher_class_routes,
    teacher_live_class_routes,
    student_class_routes,
    student_live_class_routes,
    teacher_test_routes,
    student_test_routes,
    question_routes,
    upload_routes,
    announcement_routes,
    notification_routes,
    push_routes,
    profile_routes,
    contact_routes,
    payment_routes,
    analytics_routes,
    youtube_routes,
)

from config.database import init_pool, close_pool

app = FastAPI(title="NexUacademy API", version="2.0.0-supabase")
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "NexUacademy API is running", "status": "healthy", "db": "supabase-postgres"}


# Wire routers
for r in (
    auth_routes, emergent_auth_routes, batch_routes, admission_routes,
    teacher_class_routes, teacher_live_class_routes,
    student_class_routes, student_live_class_routes,
    teacher_test_routes, student_test_routes,
    question_routes, upload_routes,
    announcement_routes, notification_routes, push_routes,
    profile_routes, contact_routes,
    payment_routes, analytics_routes,
    youtube_routes,
):
    api_router.include_router(r.router)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event("startup")
async def startup_event():
    logger.info("NexUacademy API starting (Supabase Postgres backend)")
    await init_pool()
    # Run idempotent DB migrations (tier columns, applications, preseed roster)
    try:
        from services.migration_service import run_migrations, cleanup_batches
        await run_migrations()
        await cleanup_batches()
    except Exception as e:
        logger.warning(f"Migrations failed: {e}")
    # Ensure admin/teacher/student seed users exist in Supabase Auth
    try:
        from services.seed_service import ensure_seed_users
        await ensure_seed_users()
    except Exception as e:
        logger.warning(f"Seed users failed: {e}")
    # Reminder scheduler (best-effort — some legacy features will be re-added later)
    logger.info("Startup complete")


@app.on_event("shutdown")
async def shutdown_db_client():
    await close_pool()
    logger.info("Postgres pool closed")
