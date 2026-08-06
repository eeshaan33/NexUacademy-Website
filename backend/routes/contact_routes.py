"""Landing-page contact form (public)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from config.database import get_pool
from services.pg_utils import short_id, json_safe

router = APIRouter(prefix="/contacts", tags=["contacts"])


class ContactSubmit(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""
    course: str = ""
    message: str


@router.post("/submit")
async def submit(payload: ContactSubmit):
    pool = get_pool()
    cid = short_id("c")
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO contacts (contact_id, name, email, phone, course, message)
               VALUES ($1,$2,$3,$4,$5,$6)""",
            cid, payload.name, payload.email, payload.phone, payload.course, payload.message,
        )
    return {"success": True, "message": "Thanks — we'll reach out shortly."}
