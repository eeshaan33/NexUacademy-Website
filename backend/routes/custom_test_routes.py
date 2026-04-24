"""Custom Test Routes - Pydantic-validated with resume-session support."""
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import random

from config.database import get_database
from middleware.auth import get_current_user
from models.requests import (
    CustomTestCreateRequest,
    CustomTestSubmissionRequest,
    SaveProgressRequest,
)

router = APIRouter(prefix="/custom-tests", tags=["custom-tests"])

SESSION_GRACE_MINUTES = 30  # extra buffer beyond duration before a session auto-expires


# ---------- Helpers ----------

async def _get_active_session(db, user_id: str, test_id: str):
    """Return an active (not submitted, not expired) session for this user+test."""
    doc = await db.test_sessions.find_one({
        "user_id": user_id,
        "test_id": test_id,
        "status": "active",
    }, {"_id": 0})
    if not doc:
        return None
    # Normalise expires_at to tz-aware UTC
    exp = doc.get("expires_at")
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
    elif exp and exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    doc["expires_at"] = exp
    if exp and exp <= datetime.now(timezone.utc):
        await db.test_sessions.update_one(
            {"session_id": doc["session_id"]}, {"$set": {"status": "expired"}}
        )
        return None
    return doc


async def _expire_orphan_sessions(db, user_id: str):
    now = datetime.now(timezone.utc)
    # Pull active sessions and filter python-side to avoid naive/aware mismatch
    async for s in db.test_sessions.find(
        {"user_id": user_id, "status": "active"}, {"_id": 0, "session_id": 1, "expires_at": 1}
    ):
        exp = s.get("expires_at")
        if isinstance(exp, str):
            try:
                exp = datetime.fromisoformat(exp.replace("Z", "+00:00"))
            except Exception:
                continue
        if exp and exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp and exp <= now:
            await db.test_sessions.update_one(
                {"session_id": s["session_id"]}, {"$set": {"status": "expired"}}
            )


# ---------- Question counts & syllabus ----------

@router.get("/question-counts")
async def get_question_counts(examType: Optional[str] = None):
    db = get_database()
    match_query = {"exam_type": examType} if examType and examType != "Mixed" else {}
    pipeline = [
        {"$match": match_query} if match_query else {"$match": {}},
        {"$group": {"_id": {"subject": "$subject", "chapter": "$chapter", "topic": "$topic"},
                    "count": {"$sum": 1}}},
    ]
    results = await db.questions.aggregate(pipeline).to_list(length=1000)
    return {f"{r['_id']['subject']}-{r['_id']['chapter']}-{r['_id']['topic']}": r["count"] for r in results}


@router.get("/syllabus")
async def get_syllabus():
    db = get_database()
    pipeline = [
        {"$group": {"_id": {"subject": "$subject", "chapter": "$chapter"},
                    "topics": {"$addToSet": "$topic"},
                    "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    results = await db.questions.aggregate(pipeline).to_list(length=500)

    syllabus = {s: {"Class11": [], "Class12": []} for s in ("Physics", "Chemistry", "Mathematics")}
    class11_chapters = {
        "Physics": ["Units and Measurements", "Motion in a Straight Line", "Motion in a Plane",
                    "Laws of Motion", "Work, Energy and Power", "System of Particles",
                    "Gravitation", "Mechanical Properties", "Thermal Properties",
                    "Thermodynamics", "Kinetic Theory", "Oscillations", "Waves"],
        "Chemistry": ["Some Basic Concepts", "Structure of Atom", "Classification of Elements",
                      "Chemical Bonding", "States of Matter", "Thermodynamics", "Equilibrium",
                      "Redox Reactions", "Hydrogen", "s-Block Elements", "Organic Chemistry",
                      "Hydrocarbons", "Environmental Chemistry"],
        "Mathematics": ["Sets", "Relations and Functions", "Trigonometric Functions",
                        "Complex Numbers", "Linear Inequalities", "Permutation and Combination",
                        "Binomial Theorem", "Sequence and Series", "Straight Lines", "Conic Sections",
                        "Introduction to 3D", "Limits and Derivatives", "Statistics", "Probability"],
    }

    for r in results:
        subject, chapter = r["_id"]["subject"], r["_id"]["chapter"]
        if subject not in syllabus:
            continue
        data = {"chapter": chapter,
                "topics": [t for t in r["topics"] if t],
                "questionCount": r["count"]}
        is_c11 = any(c11 in chapter for c11 in class11_chapters.get(subject, []))
        (syllabus[subject]["Class11"] if is_c11 else syllabus[subject]["Class12"]).append(data)

    return syllabus


# ---------- Generate ----------

@router.post("/generate")
async def generate_custom_test(payload: CustomTestCreateRequest, user=Depends(get_current_user)):
    db = get_database()
    all_selected, insufficient = [], []

    for t in payload.selectedTopics:
        query = {
            "subject": t.subject, "chapter": t.chapter,
            "year": {"$gte": payload.yearRange.start, "$lte": payload.yearRange.end},
        }
        if t.topic and t.topic != t.chapter:
            query["topic"] = t.topic
        if payload.examType != "Mixed":
            query["exam_type"] = payload.examType
        if t.difficulty != "Mixed":
            query["difficulty"] = t.difficulty

        pool = await db.questions.find(query, {"_id": 0}).to_list(length=t.questionCount * 3)
        if len(pool) < t.questionCount:
            insufficient.append({"topic": t.topic or t.chapter, "subject": t.subject,
                                 "available": len(pool), "requested": t.questionCount})
            selected = pool
        else:
            random.shuffle(pool)
            selected = pool[:t.questionCount]
        all_selected.extend(selected)

    if not all_selected:
        raise HTTPException(status_code=400, detail="No questions found for the given criteria")

    random.shuffle(all_selected)
    test_id = f"test_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    test_questions = [{
        "questionNumber": i,
        "question_id": q.get("question_id"),
        "questionText": q.get("question_text") or q.get("questionText"),
        "options": q.get("options"),
        "correctAnswer": q.get("correct_answer") or q.get("correctAnswer"),
        "questionType": q.get("question_type") or q.get("questionType", "MCQ"),
        "subject": q.get("subject"),
        "chapter": q.get("chapter"),
        "topic": q.get("topic"),
        "marks": 4,
        "negativeMarks": -1,
        "year": q.get("year"),
        "difficulty": q.get("difficulty"),
    } for i, q in enumerate(all_selected, 1)]

    subject_breakdown = {"Physics": 0, "Chemistry": 0, "Mathematics": 0}
    for q in test_questions:
        subject_breakdown[q["subject"]] = subject_breakdown.get(q["subject"], 0) + 1

    test_doc = {
        "test_id": test_id,
        "test_name": f"Custom Test - {now.strftime('%d %b %Y %I:%M %p')}",
        "test_type": "custom",
        "exam_type": payload.examType,
        "created_by": user["user_id"],
        "created_by_name": user.get("name", "Student"),
        "duration": payload.duration,
        "total_questions": len(test_questions),
        "total_marks": len(test_questions) * 4,
        "questions": test_questions,
        "subject_breakdown": subject_breakdown,
        "year_range": payload.yearRange.model_dump(),
        "status": "ready",
        "created_at": now,
        "starts_at": now,
        "ends_at": now + timedelta(minutes=payload.duration + SESSION_GRACE_MINUTES),
    }
    await db.tests.insert_one(test_doc)

    resp = {
        "success": True, "test_id": test_id,
        "test_name": test_doc["test_name"],
        "total_questions": len(test_questions),
        "total_marks": test_doc["total_marks"],
        "duration": payload.duration,
        "subject_breakdown": subject_breakdown,
    }
    if insufficient:
        resp["warnings"] = insufficient
        resp["message"] = f"Test created with {len(test_questions)} questions (some topics had fewer than requested)."
    else:
        resp["message"] = "Test generated successfully"
    return resp


# ---------- Fetch test (answers stripped) ----------

@router.get("/{test_id}")
async def get_test(test_id: str, user=Depends(get_current_user)):
    db = get_database()
    test = await db.tests.find_one({"test_id": test_id}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    for q in test.get("questions", []):
        q.pop("correctAnswer", None)
    return test


# ---------- Session: start / active / save / discard ----------

@router.post("/{test_id}/start-session")
async def start_or_resume_session(test_id: str, user=Depends(get_current_user)):
    """Create (or resume) an in-progress session. Returns remaining time + saved answers."""
    db = get_database()
    test = await db.tests.find_one({"test_id": test_id}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    await _expire_orphan_sessions(db, user["user_id"])
    existing = await _get_active_session(db, user["user_id"], test_id)
    now = datetime.now(timezone.utc)

    if existing:
        expires_at = existing["expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        remaining_seconds = max(0, int((expires_at - now).total_seconds()))
        return {
            "success": True,
            "resumed": True,
            "session_id": existing["session_id"],
            "remaining_seconds": remaining_seconds,
            "answers": existing.get("answers", {}),
            "current_question": existing.get("current_question", 1),
            "started_at": existing.get("started_at"),
        }

    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    duration = int(test.get("duration", 60))
    expires_at = now + timedelta(minutes=duration)
    session_doc = {
        "session_id": session_id,
        "test_id": test_id,
        "user_id": user["user_id"],
        "started_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "last_saved_at": now.isoformat(),
        "answers": {},
        "current_question": 1,
        "status": "active",
    }
    await db.test_sessions.insert_one(session_doc)

    return {
        "success": True,
        "resumed": False,
        "session_id": session_id,
        "remaining_seconds": duration * 60,
        "answers": {},
        "current_question": 1,
        "started_at": session_doc["started_at"],
    }


@router.get("/{test_id}/active-session")
async def peek_active_session(test_id: str, user=Depends(get_current_user)):
    db = get_database()
    await _expire_orphan_sessions(db, user["user_id"])
    existing = await _get_active_session(db, user["user_id"], test_id)
    if not existing:
        return {"active": False}
    expires_at = existing["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    remaining = max(0, int((expires_at - datetime.now(timezone.utc)).total_seconds()))
    return {
        "active": True,
        "session_id": existing["session_id"],
        "remaining_seconds": remaining,
        "answered_count": len(existing.get("answers", {})),
        "started_at": existing.get("started_at"),
    }


@router.post("/{test_id}/save-progress")
async def save_progress(test_id: str, payload: SaveProgressRequest, user=Depends(get_current_user)):
    db = get_database()
    existing = await _get_active_session(db, user["user_id"], test_id)
    if not existing:
        raise HTTPException(status_code=404, detail="No active session — start one first")

    updates = {
        "answers": payload.answers,
        "last_saved_at": datetime.now(timezone.utc).isoformat(),
    }
    if payload.current_question is not None:
        updates["current_question"] = payload.current_question

    await db.test_sessions.update_one(
        {"session_id": existing["session_id"]},
        {"$set": updates},
    )
    return {"success": True, "saved_at": updates["last_saved_at"]}


@router.post("/{test_id}/discard-session")
async def discard_session(test_id: str, user=Depends(get_current_user)):
    db = get_database()
    res = await db.test_sessions.update_many(
        {"user_id": user["user_id"], "test_id": test_id, "status": "active"},
        {"$set": {"status": "discarded", "discarded_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"success": True, "discarded": res.modified_count}


# ---------- Submit (consumes active session) ----------

@router.post("/{test_id}/submit")
async def submit_test(test_id: str, submission: CustomTestSubmissionRequest,
                      user=Depends(get_current_user)):
    db = get_database()
    test = await db.tests.find_one({"test_id": test_id})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    correct = incorrect = unattempted = total_marks = 0
    q_results = []
    for q in test.get("questions", []):
        q_num = q["questionNumber"]
        correct_ans = q.get("correctAnswer", "")
        user_ans = submission.answers.get(str(q_num), "")
        row = {"questionNumber": q_num, "userAnswer": user_ans,
               "correctAnswer": correct_ans, "marks": 0, "status": "unattempted"}
        if not user_ans:
            unattempted += 1
        elif user_ans == correct_ans:
            correct += 1
            row["marks"] = q.get("marks", 4)
            row["status"] = "correct"
            total_marks += q.get("marks", 4)
        else:
            incorrect += 1
            row["marks"] = q.get("negativeMarks", -1)
            row["status"] = "incorrect"
            total_marks += q.get("negativeMarks", -1)
        q_results.append(row)

    max_marks = test.get("total_marks", len(test.get("questions", [])) * 4)
    percentage = round((total_marks / max_marks) * 100, 2) if max_marks > 0 else 0
    attempted = correct + incorrect
    accuracy = round((correct / attempted) * 100, 2) if attempted else 0

    attempt_id = f"attempt_{uuid.uuid4().hex[:12]}"
    attempt_doc = {
        "attempt_id": attempt_id,
        "test_id": test_id,
        "user_id": user["user_id"],
        "answers": submission.answers,
        "time_spent": submission.timeSpent,
        "correct": correct, "incorrect": incorrect, "unattempted": unattempted,
        "total_marks": total_marks, "max_marks": max_marks,
        "percentage": percentage, "accuracy": accuracy,
        "question_results": q_results,
        "submitted_at": datetime.now(timezone.utc),
    }
    await db.test_attempts.insert_one(attempt_doc)

    # Close active session (if any)
    await db.test_sessions.update_many(
        {"user_id": user["user_id"], "test_id": test_id, "status": "active"},
        {"$set": {"status": "submitted", "attempt_id": attempt_id}},
    )

    # Update user progress
    await db.user_progress.update_one(
        {"user_id": user["user_id"]},
        {"$inc": {"tests_taken": 1, "total_questions_attempted": attempted, "total_correct": correct},
         "$set": {"last_test_date": datetime.now(timezone.utc)}},
        upsert=True,
    )

    return {
        "success": True, "attempt_id": attempt_id,
        "results": {
            "correct": correct, "incorrect": incorrect, "unattempted": unattempted,
            "totalMarks": total_marks, "maxMarks": max_marks,
            "percentage": percentage, "accuracy": accuracy,
            "timeSpent": submission.timeSpent,
        },
        "questionResults": q_results,
    }


# ---------- History ----------

@router.get("/history/mine")
async def get_my_test_history(user=Depends(get_current_user), limit: int = Query(20, ge=1, le=100)):
    db = get_database()
    attempts = await db.test_attempts.find(
        {"user_id": user["user_id"]}, {"_id": 0}
    ).sort("submitted_at", -1).limit(limit).to_list(length=limit)

    # Also expose any in-progress sessions as "resumable" entries so the FE can surface them
    await _expire_orphan_sessions(db, user["user_id"])
    resumable = await db.test_sessions.find(
        {"user_id": user["user_id"], "status": "active"},
        {"_id": 0}
    ).to_list(length=20)

    test_ids = {a["test_id"] for a in attempts} | {s["test_id"] for s in resumable}
    tests = await db.tests.find(
        {"test_id": {"$in": list(test_ids)}},
        {"_id": 0, "test_id": 1, "test_name": 1, "exam_type": 1, "subject_breakdown": 1,
         "duration": 1, "total_questions": 1, "total_marks": 1}
    ).to_list(length=None)
    tmap = {t["test_id"]: t for t in tests}

    for a in attempts:
        t = tmap.get(a["test_id"]) or {}
        a["test_name"] = t.get("test_name")
        a["exam_type"] = t.get("exam_type")
        a["subject_breakdown"] = t.get("subject_breakdown")

    resumable_out = []
    for s in resumable:
        t = tmap.get(s["test_id"]) or {}
        expires = s["expires_at"]
        if isinstance(expires, str):
            expires = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if expires and expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        remaining = max(0, int((expires - datetime.now(timezone.utc)).total_seconds())) if expires else 0
        resumable_out.append({
            "test_id": s["test_id"],
            "test_name": t.get("test_name", s["test_id"]),
            "exam_type": t.get("exam_type"),
            "remaining_seconds": remaining,
            "answered_count": len(s.get("answers", {})),
            "total_questions": t.get("total_questions"),
            "started_at": s.get("started_at"),
        })

    return {"attempts": attempts, "resumable": resumable_out}
