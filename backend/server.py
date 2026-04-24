from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path

# Import route modules
from routes import auth_routes, question_routes, test_routes, class_routes, bookmark_routes, analytics_routes, admin_routes, admission_routes
from routes import test_template_routes, custom_test_routes
from routes import teacher_class_routes, teacher_test_routes, teacher_student_routes
from routes import student_class_routes, student_test_routes, student_analytics_routes
from routes import notification_routes, push_routes, batch_routes
from routes import upload_routes
from routes import admin_dashboard_routes, student_suggestion_routes

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="NexUacademy API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check endpoint
@api_router.get("/")
async def root():
    return {"message": "NexUacademy API is running", "status": "healthy"}

# Include all route modules
api_router.include_router(auth_routes.router)
api_router.include_router(question_routes.router)
api_router.include_router(test_routes.router)
api_router.include_router(class_routes.router)
api_router.include_router(bookmark_routes.router)
api_router.include_router(analytics_routes.router)
api_router.include_router(admin_routes.router)
api_router.include_router(admission_routes.router)
api_router.include_router(test_template_routes.router)
api_router.include_router(custom_test_routes.router)
api_router.include_router(teacher_class_routes.router)
api_router.include_router(teacher_test_routes.router)
api_router.include_router(teacher_student_routes.router)
api_router.include_router(student_class_routes.router)
api_router.include_router(student_test_routes.router)
api_router.include_router(student_analytics_routes.router)
api_router.include_router(admin_dashboard_routes.router)
api_router.include_router(student_suggestion_routes.router)
api_router.include_router(notification_routes.router)
api_router.include_router(push_routes.router)
api_router.include_router(batch_routes.router)
api_router.include_router(upload_routes.router)

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("NexUacademy API started successfully")
    # Ensure admin user exists
    from routes.admin_routes import ensure_admin_user
    await ensure_admin_user()
    # Initialize object storage
    try:
        from services.storage_service import init_storage
        init_storage()
    except Exception as e:
        logger.warning(f"Storage init failed (will retry on first upload): {e}")
    # Start the test reminder background scheduler
    from services.reminder_scheduler import reminder_loop
    asyncio.create_task(reminder_loop())
    logger.info("Test reminder scheduler started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("MongoDB connection closed")