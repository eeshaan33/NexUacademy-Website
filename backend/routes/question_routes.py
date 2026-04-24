from fastapi import APIRouter, HTTPException, status, Query, Request, Depends
from typing import List, Optional
from datetime import datetime, timezone
import uuid
import csv
import io
from models.question import QuestionCreate, Question
from models.requests import BulkImportRequest, BulkQuestionImport
from middleware.auth import get_current_user, get_current_teacher
from config.syllabus import JEE_SYLLABUS
from config.database import get_database

router = APIRouter(prefix="/questions", tags=["questions"])


async def _require_admin(request: Request):
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


@router.post("/", response_model=Question)
async def create_question(question_data: QuestionCreate, request: Request):
    """Create a new question (teacher only)."""
    db = get_database()
    user = await get_current_teacher(request)
    question_id = f"q_{uuid.uuid4().hex[:12]}"
    question_doc = question_data.model_dump()
    question_doc.update({
        "question_id": question_id,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc),
    })
    await db.questions.insert_one(question_doc)
    question_doc.pop("_id", None)
    return question_doc


@router.get("/")
async def get_questions(
    exam_type: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
    chapter: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    difficulty: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),
):
    """Get questions with filters."""
    db = get_database()
    filter_query = {}
    for k, v in (("exam_type", exam_type), ("subject", subject), ("chapter", chapter),
                 ("topic", topic), ("year", year), ("difficulty", difficulty)):
        if v:
            filter_query[k] = v

    total = await db.questions.count_documents(filter_query)
    skip = (page - 1) * limit
    questions = await db.questions.find(filter_query, {"_id": 0}).skip(skip).limit(limit).to_list(length=limit)
    return {"questions": questions, "total": total, "page": page, "pages": (total + limit - 1) // limit}


@router.get("/syllabus")
async def get_syllabus():
    return JEE_SYLLABUS


@router.get("/syllabus/{subject}")
async def get_subject_syllabus(subject: str):
    if subject not in JEE_SYLLABUS:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {subject: JEE_SYLLABUS[subject]}


@router.get("/chapters/{subject}")
async def get_chapters(subject: str, class_level: Optional[str] = Query(None)):
    if subject not in JEE_SYLLABUS:
        raise HTTPException(status_code=404, detail="Subject not found")
    if class_level:
        if class_level not in ["Class11", "Class12"]:
            raise HTTPException(status_code=400, detail="class_level must be Class11 or Class12")
        return {class_level: JEE_SYLLABUS[subject][class_level]}
    return JEE_SYLLABUS[subject]


@router.get("/stats")
async def question_stats():
    """Admin overview of PYQ bank: total, by exam, by subject, by year."""
    db = get_database()
    total = await db.questions.count_documents({})

    async def _agg(field):
        return await db.questions.aggregate([
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]).to_list(length=100)

    return {
        "total": total,
        "by_exam": await _agg("exam_type"),
        "by_subject": await _agg("subject"),
        "by_year": await _agg("year"),
        "by_difficulty": await _agg("difficulty"),
    }


@router.post("/bulk-import")
async def bulk_import(payload: BulkImportRequest, request: Request):
    """Admin-only: import many questions at once."""
    admin = await _require_admin(request)
    db = get_database()

    if payload.replace_existing:
        await db.questions.delete_many({})

    inserted, skipped = 0, 0
    for q in payload.questions:
        doc = q.model_dump()
        doc["question_id"] = f"q_{uuid.uuid4().hex[:12]}"
        doc["created_by"] = admin["user_id"]
        doc["created_at"] = datetime.now(timezone.utc)
        # Store in both shapes for compatibility with existing readers
        doc["question_text"] = q.question_text
        doc["questionText"] = q.question_text
        doc["questionType"] = "MCQ_Single"
        doc["correctAnswer"] = q.correct_answer
        try:
            await db.questions.insert_one(doc)
            inserted += 1
        except Exception:
            skipped += 1

    return {"success": True, "inserted": inserted, "skipped": skipped,
            "total": await db.questions.count_documents({})}


@router.post("/bulk-import/csv")
async def bulk_import_csv(request: Request):
    """Admin-only: parse pasted CSV body and import.

    Expected headers:
      exam_type,subject,chapter,topic,year,difficulty,question_text,
      option_a,option_b,option_c,option_d,correct_answer[,solution_youtube_url,solution_timestamp]
    """
    admin = await _require_admin(request)
    db = get_database()

    body = (await request.body()).decode("utf-8", errors="ignore")
    if not body.strip():
        raise HTTPException(status_code=400, detail="Empty CSV")

    try:
        reader = csv.DictReader(io.StringIO(body))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    inserted, errors = 0, []
    for idx, row in enumerate(reader, start=2):
        try:
            q_dict = {
                "exam_type": row["exam_type"].strip(),
                "subject": row["subject"].strip(),
                "chapter": row["chapter"].strip(),
                "topic": row.get("topic", "").strip(),
                "year": int(row["year"]),
                "difficulty": row.get("difficulty", "Medium").strip() or "Medium",
                "question_text": row["question_text"].strip(),
                "question_image_url": row.get("question_image_url", "").strip(),
                "options": {
                    "A": row["option_a"].strip(),
                    "B": row["option_b"].strip(),
                    "C": row["option_c"].strip(),
                    "D": row["option_d"].strip(),
                },
                "correct_answer": row["correct_answer"].strip().upper(),
                "marks": int(row.get("marks") or 4),
                "negative_marks": int(row.get("negative_marks") or -1),
                "solution_youtube_url": row.get("solution_youtube_url", ""),
                "solution_timestamp": int(row.get("solution_timestamp") or 0),
            }
            validated = BulkQuestionImport(**q_dict)
            doc = validated.model_dump()
            doc["question_id"] = f"q_{uuid.uuid4().hex[:12]}"
            doc["created_by"] = admin["user_id"]
            doc["created_at"] = datetime.now(timezone.utc)
            doc["question_text"] = validated.question_text
            doc["questionText"] = validated.question_text
            doc["questionType"] = "MCQ_Single"
            doc["correctAnswer"] = validated.correct_answer
            await db.questions.insert_one(doc)
            inserted += 1
        except Exception as e:
            errors.append({"row": idx, "error": str(e)[:200]})

    return {"success": True, "inserted": inserted, "errors": errors[:50],
            "total": await db.questions.count_documents({})}


@router.post("/seed-sample")
async def seed_sample_pack(request: Request, count: int = Query(30, ge=5, le=200)):
    """Admin convenience — seed a small sample pack covering core chapters
    so the PYQ section and custom tests have immediate content."""
    admin = await _require_admin(request)
    db = get_database()

    samples = [
        # Physics
        ("JEE_Main", "Physics", "Kinematics", "1D motion", 2022, "Medium",
         "A particle moves with constant acceleration. If it covers 40 m in the 4th second, what is the acceleration (starting from rest)?",
         {"A": "4 m/s²", "B": "8 m/s²", "C": "10 m/s²", "D": "16 m/s²"}, "C"),
        ("JEE_Main", "Physics", "Thermodynamics", "First law", 2021, "Easy",
         "Which process has ΔU = 0 for an ideal gas?",
         {"A": "Adiabatic", "B": "Isobaric", "C": "Isochoric", "D": "Isothermal"}, "D"),
        ("JEE_Main", "Physics", "Optics", "Ray optics", 2020, "Hard",
         "A convex lens of focal length 20 cm forms a real image at 30 cm. The object distance is:",
         {"A": "12 cm", "B": "60 cm", "C": "50 cm", "D": "30 cm"}, "B"),
        ("JEE_Advanced", "Physics", "Electrostatics", "Coulomb's law", 2023, "Hard",
         "Two point charges +q and -q separated by 2a. Field at midpoint on the perpendicular bisector of distance d is:",
         {"A": "zero", "B": "kq/d²", "C": "2kq/d²", "D": "2kqa/(d²+a²)^(3/2)"}, "D"),
        ("JEE_Main", "Physics", "Gravitation", "Orbital mechanics", 2022, "Medium",
         "Escape velocity from Earth's surface is:",
         {"A": "7.9 km/s", "B": "11.2 km/s", "C": "9.8 km/s", "D": "15 km/s"}, "B"),
        # Chemistry
        ("JEE_Main", "Chemistry", "Chemical Bonding", "Hybridization", 2022, "Easy",
         "Hybridization of carbon in CO2 is:",
         {"A": "sp", "B": "sp²", "C": "sp³", "D": "dsp²"}, "A"),
        ("JEE_Main", "Chemistry", "Thermodynamics", "Entropy", 2021, "Medium",
         "ΔS for the reaction N2 + 3H2 → 2NH3 is:",
         {"A": "Positive", "B": "Negative", "C": "Zero", "D": "Cannot be determined"}, "B"),
        ("JEE_Advanced", "Chemistry", "Organic Chemistry", "Aromaticity", 2023, "Hard",
         "Which of the following is NOT aromatic?",
         {"A": "Benzene", "B": "Cyclopentadienyl anion", "C": "Cyclooctatetraene", "D": "Pyridine"}, "C"),
        ("JEE_Main", "Chemistry", "States of Matter", "Gas laws", 2020, "Easy",
         "At constant T, PV is constant — this is:",
         {"A": "Charles law", "B": "Boyle's law", "C": "Avogadro's law", "D": "Gay-Lussac's law"}, "B"),
        ("JEE_Main", "Chemistry", "Equilibrium", "Le Chatelier", 2022, "Medium",
         "Increasing pressure on N2+3H2↔2NH3 shifts equilibrium:",
         {"A": "Left", "B": "Right", "C": "No change", "D": "Depends on T"}, "B"),
        # Mathematics
        ("JEE_Main", "Mathematics", "Trigonometric Functions", "Identities", 2022, "Easy",
         "sin²θ + cos²θ equals:",
         {"A": "0", "B": "1", "C": "2", "D": "sin 2θ"}, "B"),
        ("JEE_Main", "Mathematics", "Complex Numbers", "Modulus", 2021, "Medium",
         "|3 + 4i| =",
         {"A": "5", "B": "7", "C": "25", "D": "1"}, "A"),
        ("JEE_Advanced", "Mathematics", "Calculus", "Limits", 2023, "Hard",
         "lim(x→0) sin(x)/x =",
         {"A": "0", "B": "1", "C": "∞", "D": "Does not exist"}, "B"),
        ("JEE_Main", "Mathematics", "Conic Sections", "Parabola", 2020, "Medium",
         "Focus of the parabola y² = 8x is:",
         {"A": "(2, 0)", "B": "(-2, 0)", "C": "(0, 2)", "D": "(0, -2)"}, "A"),
        ("JEE_Main", "Mathematics", "Probability", "Independent events", 2022, "Easy",
         "Probability of getting heads in 2 coin tosses:",
         {"A": "1/4", "B": "1/2", "C": "3/4", "D": "1"}, "C"),
    ]

    # Repeat to reach count
    inserted = 0
    now = datetime.now(timezone.utc)
    for i in range(count):
        s = samples[i % len(samples)]
        exam_type, subject, chapter, topic, year, difficulty, qtext, options, correct = s
        # Add variance: slightly permute year
        adj_year = min(2024, max(2015, year + (i // len(samples))))
        doc = {
            "question_id": f"q_seed_{uuid.uuid4().hex[:10]}",
            "exam_type": exam_type,
            "subject": subject,
            "chapter": chapter,
            "topic": topic,
            "year": adj_year,
            "difficulty": difficulty,
            "question_text": qtext,
            "questionText": qtext,
            "question_image_url": "",
            "options": options,
            "correct_answer": correct,
            "correctAnswer": correct,
            "questionType": "MCQ_Single",
            "marks": 4,
            "negative_marks": -1,
            "solution_youtube_url": "",
            "solution_timestamp": 0,
            "created_by": admin["user_id"],
            "created_at": now,
        }
        await db.questions.insert_one(doc)
        inserted += 1

    return {"success": True, "inserted": inserted,
            "total": await db.questions.count_documents({})}


@router.get("/{question_id}")
async def get_question(question_id: str):
    db = get_database()
    q = await db.questions.find_one({"question_id": question_id}, {"_id": 0})
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


@router.delete("/{question_id}")
async def delete_question(question_id: str, request: Request):
    db = get_database()
    await get_current_teacher(request)
    res = await db.questions.delete_one({"question_id": question_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question deleted successfully"}


@router.delete("/bulk/all")
async def delete_all_questions(request: Request, confirm: str = Query("")):
    """Admin-only: wipe entire PYQ bank. Require ?confirm=WIPE to proceed."""
    await _require_admin(request)
    if confirm != "WIPE":
        raise HTTPException(status_code=400, detail="Pass ?confirm=WIPE to confirm destructive delete")
    db = get_database()
    res = await db.questions.delete_many({})
    return {"success": True, "deleted": res.deleted_count}
