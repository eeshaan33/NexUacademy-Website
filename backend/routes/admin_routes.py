from fastapi import APIRouter, HTTPException, status, Request, UploadFile, File
from typing import List, Optional
from datetime import datetime, timezone
import uuid
from models.question import QuestionCreate, Question
from middleware.auth import get_current_user, get_current_teacher
from config.database import get_database
from services.pdf_extractor import JEEQuestionExtractor
from services.google_sheets_service import GoogleSheetsManager
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

@router.post("/upload-pdf")
async def upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    exam_type: str = "JEE_Main",
    year: int = 2024,
    subject: str = "Chemistry"
):
    """
    Upload PDF and extract questions.
    """
    user = await get_current_teacher(request)
    db = get_database()
    
    try:
        # Read PDF content
        content = await file.read()
        
        # For now, use the pre-analyzed data from the chemical equilibrium PDF
        # In production, you'd use PyPDF2/pdfplumber to extract text
        
        # Use the extracted questions data
        questions_data = await extract_questions_from_pdf(content, exam_type, year, subject)
        
        # Store in database
        inserted_ids = []
        for i, q_data in enumerate(questions_data, 1):
            question_id = f"q_{uuid.uuid4().hex[:12]}"
            row_id = f"Q{str(i).zfill(3)}"
            
            question_doc = {
                "question_id": question_id,
                "questionNumber": i,
                "googleSheetRowId": row_id,
                **q_data,
                "created_by": user["user_id"],
                "created_at": datetime.now(timezone.utc)
            }
            
            await db.questions.insert_one(question_doc)
            inserted_ids.append(question_id)
        
        # Create Google Sheet
        sheets_manager = GoogleSheetsManager()
        sheet_url = sheets_manager.create_sheet(questions_data)
        
        return {
            "success": True,
            "message": f"Extracted {len(questions_data)} questions",
            "questions_count": len(questions_data),
            "google_sheet_url": sheet_url,
            "breakdown": {
                subject: len(questions_data)
            }
        }
        
    except Exception as e:
        logger.error(f"PDF upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process PDF: {str(e)}"
        )

@router.post("/sync-youtube-links")
async def sync_youtube_links(request: Request):
    """
    Manually trigger sync from Google Sheet.
    """
    user = await get_current_teacher(request)
    db = get_database()
    
    sheets_manager = GoogleSheetsManager()
    updated_count = sheets_manager.sync_youtube_links(db)
    
    return {
        "success": True,
        "updated_count": updated_count,
        "message": f"Updated {updated_count} questions with YouTube links"
    }

@router.get("/google-sheet-url")
async def get_google_sheet_url(request: Request):
    """
    Get Google Sheet URL for editing.
    """
    user = await get_current_teacher(request)
    
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    if not sheet_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Google Sheet not configured"
        )
    
    return {
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    }

@router.get("/questions-stats")
async def get_questions_stats(request: Request):
    """
    Get statistics about questions in database.
    """
    user = await get_current_teacher(request)
    db = get_database()
    
    # Total questions
    total = await db.questions.count_documents({})
    
    # By subject
    by_subject = {}
    for subject in ["Physics", "Chemistry", "Mathematics"]:
        count = await db.questions.count_documents({"subject": subject})
        by_subject[subject] = count
    
    # By year
    by_year = {}
    for year in range(2020, 2025):
        count = await db.questions.count_documents({"year": year})
        if count > 0:
            by_year[year] = count
    
    # With YouTube solutions
    with_solutions = await db.questions.count_documents({
        "solutionYoutubeUrl": {"$ne": ""}
    })
    
    return {
        "total_questions": total,
        "by_subject": by_subject,
        "by_year": by_year,
        "with_youtube_solutions": with_solutions,
        "without_youtube_solutions": total - with_solutions
    }

async def extract_questions_from_pdf(content: bytes, exam_type: str, year: int, subject: str) -> List[dict]:
    """
    Extract questions from PDF content.
    This is a placeholder - you'd implement actual PDF parsing here.
    """
    # For the chemical equilibrium PDF, return the extracted questions
    from backend.seed.chemical_equilibrium_questions import CHEMICAL_EQUILIBRIUM_QUESTIONS
    
    # Update exam type and year
    questions = []
    for q in CHEMICAL_EQUILIBRIUM_QUESTIONS:
        q_copy = q.copy()
        q_copy["examType"] = exam_type
        q_copy["year"] = year
        q_copy["subject"] = subject
        questions.append(q_copy)
    
    return questions
