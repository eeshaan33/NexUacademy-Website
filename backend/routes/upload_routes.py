from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from services.storage_service import upload_image, get_object, init_storage
from middleware.auth import get_current_user
from config.database import get_database
from datetime import datetime, timezone
from fastapi import Request
import uuid
import logging

router = APIRouter(prefix="/upload", tags=["upload"])
logger = logging.getLogger(__name__)

@router.post("/image")
async def upload_image_endpoint(request: Request, file: UploadFile = File(...)):
    user = await get_current_user(request)
    if file.content_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only image files (JPEG, PNG, GIF, WebP) allowed")
    data = await file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    try:
        storage_path = upload_image(data, file.filename, file.content_type, folder=f"uploads/{user['user_id']}")
        db = get_database()
        file_doc = {
            "file_id": f"file_{uuid.uuid4().hex[:12]}",
            "storage_path": storage_path,
            "original_filename": file.filename,
            "content_type": file.content_type,
            "size": len(data),
            "uploaded_by": user["user_id"],
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc)
        }
        await db.files.insert_one(file_doc)
        file_doc.pop("_id", None)
        return {"url": f"/api/upload/files/{storage_path}", "path": storage_path, "file": file_doc}
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

@router.get("/files/{path:path}")
async def serve_file(path: str):
    try:
        data, content_type = get_object(path)
        return Response(content=data, media_type=content_type, headers={"Cache-Control": "public, max-age=86400"})
    except Exception as e:
        logger.error(f"File serve failed: {e}")
        raise HTTPException(status_code=404, detail="File not found")
