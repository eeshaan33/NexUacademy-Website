"""Upload image → Supabase Storage bucket 'question-images'. Returns public URL."""
import base64
import logging
import mimetypes
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from config.database import get_supabase
from middleware.auth import get_current_teacher

router = APIRouter(prefix="/upload", tags=["upload"])
logger = logging.getLogger(__name__)

BUCKET = "question-images"


def _ensure_bucket():
    supabase = get_supabase()
    try:
        buckets = supabase.storage.list_buckets()
        names = [b.name if hasattr(b, "name") else b.get("name") for b in buckets]
        if BUCKET not in names:
            supabase.storage.create_bucket(BUCKET, {"public": True})
    except Exception as e:
        logger.warning(f"ensure_bucket failed (may already exist): {e}")


@router.post("/image")
async def upload_image(file: UploadFile = File(...), user=Depends(get_current_teacher)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")
    _ensure_bucket()
    ext = mimetypes.guess_extension(file.content_type) or ".png"
    if ext.lower() in (".jpeg",):
        ext = ".jpg"
    key = f"{user['user_id']}/{uuid.uuid4().hex}{ext}"
    data = await file.read()
    supabase = get_supabase()
    try:
        supabase.storage.from_(BUCKET).upload(key, data, {"content-type": file.content_type, "upsert": "true"})
        public_url = supabase.storage.from_(BUCKET).get_public_url(key)
    except Exception as e:
        logger.exception("upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)[:200]}")
    return {"success": True, "url": public_url, "key": key}
