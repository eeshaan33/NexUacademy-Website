"""
Test Template Routes - For saving and loading custom test configurations
"""
from fastapi import APIRouter, HTTPException, Request
from config.database import get_database
from datetime import datetime, timezone
from typing import Optional, List
import uuid
from middleware.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/test-templates", tags=["test-templates"])

class TopicConfig(BaseModel):
    subject: str
    chapter: str
    topic: str
    questionCount: int
    difficulty: str = "Mixed"

class YearRange(BaseModel):
    start: int
    end: int

class TemplateCreate(BaseModel):
    templateName: str
    examType: str
    selectedTopics: List[TopicConfig]
    yearRange: YearRange
    duration: int
    totalQuestions: int
    totalMarks: int
    subjectBreakdown: Optional[dict] = None

class TemplateUpdate(BaseModel):
    templateName: Optional[str] = None
    isFavorite: Optional[bool] = None

@router.get("")
async def get_templates(request: Request):
    """Get all test templates for current user"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        user_id = user.get("user_id")
    except:
        # Return empty if not authenticated
        return []
    
    templates = await db.test_templates.find(
        {"student_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(length=50)
    
    return templates

@router.post("")
async def create_template(template: TemplateCreate, request: Request):
    """Create a new test template"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        user_id = user.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
    
    template_doc = {
        "template_id": template_id,
        "student_id": user_id,
        "template_name": template.templateName,
        "exam_type": template.examType,
        "selected_topics": [t.dict() for t in template.selectedTopics],
        "year_range": template.yearRange.dict(),
        "duration": template.duration,
        "total_questions": template.totalQuestions,
        "total_marks": template.totalMarks,
        "subject_breakdown": template.subjectBreakdown,
        "is_favorite": False,
        "usage_count": 0,
        "last_used": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None
    }
    
    await db.test_templates.insert_one(template_doc)
    template_doc.pop("_id", None)
    
    return {
        "success": True,
        "template": template_doc,
        "message": "Template saved successfully"
    }

@router.put("/{template_id}")
async def update_template(template_id: str, update: TemplateUpdate, request: Request):
    """Update a test template"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        user_id = user.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.test_templates.update_one(
        {"template_id": template_id, "student_id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"success": True, "message": "Template updated"}

@router.delete("/{template_id}")
async def delete_template(template_id: str, request: Request):
    """Delete a test template"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        user_id = user.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    result = await db.test_templates.delete_one(
        {"template_id": template_id, "student_id": user_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return {"success": True, "message": "Template deleted"}

@router.post("/{template_id}/use")
async def mark_template_used(template_id: str, request: Request):
    """Mark template as used (increment usage count)"""
    db = get_database()
    
    try:
        user = await get_current_user(request)
        user_id = user.get("user_id")
    except:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    await db.test_templates.update_one(
        {"template_id": template_id, "student_id": user_id},
        {
            "$inc": {"usage_count": 1},
            "$set": {"last_used": datetime.now(timezone.utc)}
        }
    )
    
    return {"success": True}
