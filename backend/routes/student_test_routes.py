from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
from config.database import get_database
from middleware.auth import get_current_user
import uuid
import random

router = APIRouter(prefix="/student/tests", tags=["student-tests"])


@router.get("/assigned")
async def get_assigned_tests(user=Depends(get_current_user)):
    db = get_database()
    batch = user.get("batch_id")
    if not batch:
        return {"success": True, "tests": []}

    tests = await db.teacher_tests.find(
        {"assigned_batches": batch, "status": {"$ne": "draft"}},
        {"_id": 0, "questions.correct_answer": 0, "questions.teacher_note": 0},
    ).sort("scheduled_date_time", -1).to_list(length=None)

    # Check attempt status for each test
    for test in tests:
        attempt = await db.test_attempts.find_one(
            {"test_id": test["test_id"], "student_id": user["user_id"]},
            {"_id": 0, "status": 1, "attempt_id": 1, "total_score": 1},
        )
        test["attempt_status"] = attempt.get("status") if attempt else None
        test["attempt_id"] = attempt.get("attempt_id") if attempt else None
        test["attempt_score"] = attempt.get("total_score") if attempt else None

    return {"success": True, "tests": tests}


@router.post("/{test_id}/start")
async def start_test(test_id: str, user=Depends(get_current_user)):
    db = get_database()
    test = await db.teacher_tests.find_one({"test_id": test_id})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Check if already attempted
    existing = await db.test_attempts.find_one(
        {"test_id": test_id, "student_id": user["user_id"], "status": "in_progress"}
    )
    if existing:
        # Return existing attempt
        test_data = _sanitize_test_for_student(test)
        existing.pop("_id", None)
        return {"success": True, "attempt": existing, "test": test_data}

    # Check reattempt rules
    if not test.get("allow_reattempts", False):
        submitted = await db.test_attempts.find_one(
            {"test_id": test_id, "student_id": user["user_id"], "status": "submitted"}
        )
        if submitted:
            raise HTTPException(status_code=400, detail="Already submitted. Reattempts not allowed.")

    attempt_id = f"attempt_{uuid.uuid4().hex[:12]}"
    attempt_doc = {
        "attempt_id": attempt_id,
        "test_id": test_id,
        "student_id": user["user_id"],
        "student_name": user["name"],
        "answers": [],
        "total_score": 0,
        "max_score": test.get("total_marks", 0),
        "correct_answers": 0,
        "incorrect_answers": 0,
        "unattempted": 0,
        "accuracy": 0,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "submitted_at": None,
        "time_spent": 0,
        "status": "in_progress",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.test_attempts.insert_one(attempt_doc)

    test_data = _sanitize_test_for_student(test)
    if test.get("randomize_questions"):
        random.shuffle(test_data["questions"])

    attempt_doc.pop("_id", None)
    return {"success": True, "attempt": attempt_doc, "test": test_data}


def _sanitize_test_for_student(test: dict) -> dict:
    """Remove correct answers and teacher notes from test data."""
    sanitized = {k: v for k, v in test.items() if k not in ("_id", "questions")}
    sanitized["questions"] = []
    for q in test.get("questions", []):
        sanitized["questions"].append({
            "question_number": q.get("question_number"),
            "question_text": q.get("question_text"),
            "question_image_url": q.get("question_image_url", ""),
            "options": q.get("options"),
            "marks": q.get("marks", 4),
            "negative_marks": q.get("negative_marks", -1),
            "subject": q.get("subject", ""),
        })
    return sanitized


@router.post("/attempts/{attempt_id}/submit")
async def submit_test(attempt_id: str, request: Request, user=Depends(get_current_user)):
    db = get_database()
    attempt = await db.test_attempts.find_one({"attempt_id": attempt_id, "student_id": user["user_id"]})
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.get("status") == "submitted":
        raise HTTPException(status_code=400, detail="Test already submitted")

    test = await db.teacher_tests.find_one({"test_id": attempt["test_id"]})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    body = await request.json()
    student_answers = body.get("answers", [])
    time_spent = body.get("time_spent", 0)

    # Build answer lookup from test questions
    q_map = {}
    for q in test.get("questions", []):
        q_map[q["question_number"]] = q

    processed_answers = []
    total_score = 0
    correct = 0
    incorrect = 0
    unattempted = 0

    for ans in student_answers:
        q_num = ans.get("question_number")
        selected = ans.get("selected_answer", "")
        question = q_map.get(q_num, {})
        correct_ans = question.get("correct_answer", "")
        is_correct = selected == correct_ans if selected else False
        marks = question.get("marks", 4)
        neg_marks = question.get("negative_marks", -1)

        if not selected:
            unattempted += 1
            earned = 0
        elif is_correct:
            correct += 1
            earned = marks
        else:
            incorrect += 1
            earned = neg_marks

        total_score += earned

        processed_answers.append({
            "question_number": q_num,
            "selected_answer": selected,
            "correct_answer": correct_ans,
            "is_correct": is_correct,
            "marks": earned,
            "time_taken": ans.get("time_taken", 0),
            "flagged": ans.get("flagged", False),
        })

    total_q = test.get("total_questions", len(test.get("questions", [])))
    accuracy = (correct / total_q * 100) if total_q > 0 else 0

    update = {
        "answers": processed_answers,
        "total_score": total_score,
        "correct_answers": correct,
        "incorrect_answers": incorrect,
        "unattempted": unattempted,
        "accuracy": round(accuracy, 2),
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "time_spent": time_spent,
        "status": "submitted",
    }

    await db.test_attempts.update_one({"attempt_id": attempt_id}, {"$set": update})

    result = {**attempt, **update}
    result.pop("_id", None)
    return {"success": True, "message": "Test submitted", "attempt": result}


@router.get("/results/{attempt_id}")
async def get_test_results(attempt_id: str, user=Depends(get_current_user)):
    db = get_database()
    attempt = await db.test_attempts.find_one(
        {"attempt_id": attempt_id, "student_id": user["user_id"]}, {"_id": 0}
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Results not found")

    test = await db.teacher_tests.find_one({"test_id": attempt["test_id"]}, {"_id": 0})
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Build enriched results with teacher notes for incorrect/unattempted only
    q_map = {}
    for q in test.get("questions", []):
        q_map[q["question_number"]] = q

    enriched_answers = []
    for ans in attempt.get("answers", []):
        q = q_map.get(ans["question_number"], {})
        enriched = {
            **ans,
            "question_text": q.get("question_text", ""),
            "question_image_url": q.get("question_image_url", ""),
            "options": q.get("options", {}),
            "subject": q.get("subject", ""),
            "chapter": q.get("chapter", ""),
            "topic": q.get("topic", ""),
            "teacher_note": None if ans.get("is_correct") else q.get("teacher_note", ""),
        }
        enriched_answers.append(enriched)

    attempt["answers"] = enriched_answers
    attempt["test_name"] = test.get("test_name", "")
    attempt["total_marks"] = test.get("total_marks", 0)

    return {"success": True, "attempt": attempt}
