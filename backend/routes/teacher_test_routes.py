import io
import csv
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
from config.database import get_database
from middleware.auth import get_current_teacher
from services.push_service import notify_students_about_test
from models.requests import TestCreateRequest, QuestionAddRequest, TestUpdateRequest
import uuid

router = APIRouter(prefix="/teacher/tests", tags=["teacher-tests"])


@router.get("/")
async def get_teacher_tests(user=Depends(get_current_teacher)):
    db = get_database()
    tests = await db.teacher_tests.find(
        {"created_by_id": user["user_id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=None)
    return {"success": True, "tests": tests}


@router.post("/create")
async def create_test(payload: TestCreateRequest, user=Depends(get_current_teacher)):
    db = get_database()

    test_id = f"ttest_{uuid.uuid4().hex[:12]}"
    questions = [q.model_dump() for q in payload.questions]
    for i, q in enumerate(questions):
        q["question_number"] = i + 1

    total_marks = sum(q.get("marks", 4) for q in questions) if questions else 0

    test_doc = {
        "test_id": test_id,
        "test_name": payload.test_name,
        "exam_type": payload.exam_type,
        "test_pattern": payload.test_pattern,
        "subject": payload.subject,
        "test_type": payload.test_type,
        "chapters": payload.chapters,
        "topics": payload.topics,
        "scheduled_date_time": payload.scheduled_date_time,
        "duration": payload.duration,
        "instructions": payload.instructions,
        "allow_reattempts": payload.allow_reattempts,
        "max_attempts": payload.max_attempts,
        "show_solutions_after_submit": payload.show_solutions_after_submit,
        "show_results_immediately": payload.show_results_immediately,
        "randomize_questions": payload.randomize_questions,
        "assigned_batches": payload.assigned_batches,
        "created_by_id": user["user_id"],
        "created_by": user["name"],
        "questions": questions,
        "total_questions": len(questions),
        "total_marks": total_marks,
        "status": "scheduled" if questions else "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.teacher_tests.insert_one(test_doc)

    if test_doc["status"] == "scheduled":
        notified = await notify_students_about_test(test_doc)
        msg = f"Test published! {notified} students notified."
    else:
        msg = "Test saved as draft."

    return {
        "success": True,
        "message": msg,
        "test": {k: v for k, v in test_doc.items() if k != "_id"},
    }


@router.post("/{test_id}/add-question")
async def add_question(test_id: str, payload: QuestionAddRequest, user=Depends(get_current_teacher)):
    db = get_database()
    test = await db.teacher_tests.find_one({"test_id": test_id, "created_by_id": user["user_id"]})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    questions = test.get("questions", [])
    new_q = payload.model_dump()
    new_q["question_number"] = len(questions) + 1

    # Normalise correct_answers: fall back to legacy correct_answer
    if not new_q.get("correct_answers") and new_q.get("correct_answer"):
        new_q["correct_answers"] = [new_q["correct_answer"]]

    questions.append(new_q)
    total_marks = sum(q.get("marks", 4) for q in questions)

    await db.teacher_tests.update_one(
        {"test_id": test_id},
        {"$set": {
            "questions": questions,
            "total_questions": len(questions),
            "total_marks": total_marks,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return {
        "success": True,
        "message": "Question added",
        "question_number": new_q["question_number"],
        "total_questions": len(questions),
    }


@router.put("/{test_id}/publish")
async def publish_test(test_id: str, user=Depends(get_current_teacher)):
    db = get_database()
    test = await db.teacher_tests.find_one({"test_id": test_id, "created_by_id": user["user_id"]})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    if not test.get("questions"):
        raise HTTPException(status_code=400, detail="Cannot publish test with no questions")

    await db.teacher_tests.update_one(
        {"test_id": test_id},
        {"$set": {"status": "scheduled", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    notified = await notify_students_about_test(test)
    return {"success": True, "message": f"Test published! {notified} students notified."}


@router.put("/{test_id}")
async def update_test(test_id: str, payload: TestUpdateRequest, user=Depends(get_current_teacher)):
    db = get_database()
    existing = await db.teacher_tests.find_one({"test_id": test_id, "created_by_id": user["user_id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Test not found")

    # Only apply fields that were actually sent
    updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    await db.teacher_tests.update_one({"test_id": test_id}, {"$set": updates})
    updated = await db.teacher_tests.find_one({"test_id": test_id}, {"_id": 0})
    return {"success": True, "test": updated}


@router.delete("/{test_id}")
async def delete_test(test_id: str, user=Depends(get_current_teacher)):
    db = get_database()
    result = await db.teacher_tests.delete_one({"test_id": test_id, "created_by_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"success": True, "message": "Test deleted"}


@router.get("/{test_id}/results")
async def get_test_results(test_id: str, user=Depends(get_current_teacher)):
    db = get_database()
    test = await db.teacher_tests.find_one({"test_id": test_id, "created_by_id": user["user_id"]}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    attempts = await db.test_attempts.find(
        {"test_id": test_id}, {"_id": 0}
    ).sort("total_score", -1).to_list(length=None)

    # Enrich with per-student info (email, batch) + rank
    student_ids = [a["student_id"] for a in attempts]
    students = await db.users.find(
        {"user_id": {"$in": student_ids}}, {"_id": 0, "user_id": 1, "email": 1, "batch_id": 1, "profile_pic": 1}
    ).to_list(length=None)
    smap = {s["user_id"]: s for s in students}

    enriched = []
    for i, a in enumerate(attempts, 1):
        s = smap.get(a["student_id"], {})
        enriched.append({
            **a,
            "rank": i,
            "email": s.get("email"),
            "batch_id": s.get("batch_id"),
            "profile_pic": s.get("profile_pic"),
        })

    # Aggregate statistics
    total = len(enriched)
    avg_score = round(sum(a.get("total_score", 0) for a in enriched) / total, 2) if total else 0
    avg_accuracy = round(sum(a.get("accuracy", 0) for a in enriched) / total, 2) if total else 0
    high = max((a.get("total_score", 0) for a in enriched), default=0)
    low = min((a.get("total_score", 0) for a in enriched), default=0)

    # Per-question difficulty (how many got each question correct)
    q_stats = {}
    for q in test.get("questions", []):
        q_stats[q["question_number"]] = {
            "question_number": q["question_number"],
            "question_text": q.get("question_text", "")[:140],
            "subject": q.get("subject", ""),
            "chapter": q.get("chapter", ""),
            "correct": 0,
            "incorrect": 0,
            "skipped": 0,
        }
    for a in enriched:
        for ans in a.get("answers", []):
            row = q_stats.get(ans.get("question_number"))
            if not row:
                continue
            sel = ans.get("selected_answer")
            if sel in (None, "", []):
                row["skipped"] += 1
            elif ans.get("is_correct"):
                row["correct"] += 1
            else:
                row["incorrect"] += 1

    return {
        "success": True,
        "test": test,
        "attempts": enriched,
        "total_attempts": total,
        "stats": {
            "avg_score": avg_score,
            "avg_accuracy": avg_accuracy,
            "highest": high,
            "lowest": low,
        },
        "question_stats": list(q_stats.values()),
    }


@router.get("/{test_id}/results.csv")
async def download_test_results_csv(test_id: str, user=Depends(get_current_teacher)):
    db = get_database()
    test = await db.teacher_tests.find_one({"test_id": test_id, "created_by_id": user["user_id"]}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    attempts = await db.test_attempts.find(
        {"test_id": test_id}, {"_id": 0}
    ).sort("total_score", -1).to_list(length=None)

    student_ids = [a["student_id"] for a in attempts]
    students = await db.users.find(
        {"user_id": {"$in": student_ids}}, {"_id": 0, "user_id": 1, "email": 1, "batch_id": 1}
    ).to_list(length=None)
    smap = {s["user_id"]: s for s in students}

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "Rank", "Student Name", "Email", "Batch", "Score",
        "Max Score", "Accuracy %", "Correct", "Incorrect",
        "Unattempted", "Time Spent (sec)", "Submitted At", "Status",
    ])
    for i, a in enumerate(attempts, 1):
        s = smap.get(a["student_id"], {})
        writer.writerow([
            i,
            a.get("student_name", ""),
            s.get("email", ""),
            s.get("batch_id", ""),
            a.get("total_score", 0),
            a.get("max_score", 0),
            a.get("accuracy", 0),
            a.get("correct_answers", 0),
            a.get("incorrect_answers", 0),
            a.get("unattempted", 0),
            a.get("time_spent", 0),
            a.get("submitted_at", ""),
            a.get("status", ""),
        ])
    buf.seek(0)

    safe_name = "".join(c if c.isalnum() else "_" for c in test.get("test_name", "test"))[:60]
    filename = f"{safe_name}_results.csv"

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/stats")
async def get_test_stats(user=Depends(get_current_teacher)):
    db = get_database()
    total = await db.teacher_tests.count_documents({"created_by_id": user["user_id"]})
    scheduled = await db.teacher_tests.count_documents({"created_by_id": user["user_id"], "status": "scheduled"})
    draft = await db.teacher_tests.count_documents({"created_by_id": user["user_id"], "status": "draft"})
    return {"success": True, "total": total, "scheduled": scheduled, "draft": draft}
