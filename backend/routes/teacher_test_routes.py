from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
from config.database import get_database
from middleware.auth import get_current_teacher
from services.push_service import notify_students_about_test
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
async def create_test(request: Request, user=Depends(get_current_teacher)):
    db = get_database()
    body = await request.json()

    required = ["test_name", "exam_type", "subject", "test_type", "scheduled_date_time", "duration", "assigned_batches"]
    for field in required:
        if not body.get(field):
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    test_id = f"ttest_{uuid.uuid4().hex[:12]}"
    batches = body["assigned_batches"] if isinstance(body["assigned_batches"], list) else [body["assigned_batches"]]
    questions = body.get("questions", [])

    # Number questions
    for i, q in enumerate(questions):
        q["question_number"] = i + 1

    total_marks = sum(q.get("marks", 4) for q in questions) if questions else 0

    test_doc = {
        "test_id": test_id,
        "test_name": body["test_name"],
        "exam_type": body["exam_type"],
        "subject": body["subject"],
        "test_type": body["test_type"],
        "chapters": body.get("chapters", []),
        "topics": body.get("topics", []),
        "scheduled_date_time": body["scheduled_date_time"],
        "duration": int(body["duration"]),
        "instructions": body.get("instructions", ""),
        "allow_reattempts": body.get("allow_reattempts", False),
        "max_attempts": int(body.get("max_attempts", 1)),
        "show_solutions_after_submit": body.get("show_solutions_after_submit", True),
        "show_results_immediately": body.get("show_results_immediately", True),
        "randomize_questions": body.get("randomize_questions", False),
        "assigned_batches": batches,
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
async def add_question(test_id: str, request: Request, user=Depends(get_current_teacher)):
    db = get_database()
    test = await db.teacher_tests.find_one({"test_id": test_id, "created_by_id": user["user_id"]})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    body = await request.json()
    questions = test.get("questions", [])

    new_q = {
        "question_number": len(questions) + 1,
        "question_text": body["question_text"],
        "question_image_url": body.get("question_image_url", ""),
        "options": body["options"],
        "correct_answer": body["correct_answer"],
        "marks": body.get("marks", 4),
        "negative_marks": body.get("negative_marks", -1),
        "subject": body.get("subject", ""),
        "chapter": body.get("chapter", ""),
        "topic": body.get("topic", ""),
        "difficulty": body.get("difficulty", "Medium"),
        "teacher_note": body.get("teacher_note", ""),
    }
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
async def update_test(test_id: str, request: Request, user=Depends(get_current_teacher)):
    db = get_database()
    existing = await db.teacher_tests.find_one({"test_id": test_id, "created_by_id": user["user_id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Test not found")

    body = await request.json()
    body["updated_at"] = datetime.now(timezone.utc).isoformat()
    body.pop("_id", None)
    body.pop("test_id", None)

    await db.teacher_tests.update_one({"test_id": test_id}, {"$set": body})
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

    return {"success": True, "test": test, "attempts": attempts, "total_attempts": len(attempts)}


@router.get("/stats")
async def get_test_stats(user=Depends(get_current_teacher)):
    db = get_database()
    total = await db.teacher_tests.count_documents({"created_by_id": user["user_id"]})
    scheduled = await db.teacher_tests.count_documents({"created_by_id": user["user_id"], "status": "scheduled"})
    draft = await db.teacher_tests.count_documents({"created_by_id": user["user_id"], "status": "draft"})
    return {"success": True, "total": total, "scheduled": scheduled, "draft": draft}
