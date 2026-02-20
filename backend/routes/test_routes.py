from fastapi import APIRouter, HTTPException, status, Request
from config.database import get_database
from typing import List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import uuid
from models.test import TestCreate, Test, TestAttemptCreate, TestAttempt, AnswerSubmission
from middleware.auth import get_current_user, get_current_teacher

router = APIRouter(prefix="/tests", tags=["tests"])

db = get_database()

@router.post("/", response_model=Test)
async def create_test(
    test_data: TestCreate,
    request: Request
):
    """
    Create a new test (teacher or student for custom tests).
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Teachers can create assigned tests, students can only create custom tests
    if test_data.assigned_to and user["role"] != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can create assigned tests"
        )
    
    test_id = f"test_{uuid.uuid4().hex[:12]}"
    test_doc = test_data.model_dump()
    test_doc.update({
        "test_id": test_id,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc)
    })
    
    # If student creates test, mark as custom
    if user["role"] == "student":
        test_doc["is_custom"] = True
    
    await db.tests.insert_one(test_doc)
    test_doc.pop("_id", None)
    
    return test_doc

@router.get("/assigned")
async def get_assigned_tests(request: Request):
    """
    Get tests assigned to current user.
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Find tests assigned to this user or their batch
    filter_query = {
        "$or": [
            {"assigned_to": user["user_id"]},
        ]
    }
    
    if user.get("batch_id"):
        filter_query["$or"].append({"assigned_to": user["batch_id"]})
    
    tests = await db.tests.find(
        filter_query,
        {"_id": 0}
    ).sort("scheduled_date_time", -1).to_list(length=100)
    
    return {"tests": tests}

@router.get("/custom")
async def get_custom_tests(request: Request):
    """
    Get custom tests created by current user.
    """
    db = get_database()
    user = await get_current_user(request)
    
    tests = await db.tests.find(
        {"created_by": user["user_id"], "is_custom": True},
        {"_id": 0}
    ).sort("created_at", -1).to_list(length=100)
    
    return {"tests": tests}

@router.get("/{test_id}")
async def get_test(test_id: str, request: Request):
    """
    Get test details.
    """
    db = get_database()
    user = await get_current_user(request)
    
    test = await db.tests.find_one(
        {"test_id": test_id},
        {"_id": 0}
    )
    
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    # Get questions for this test
    questions = await db.questions.find(
        {"question_id": {"$in": test["questions"]}},
        {"_id": 0}
    ).to_list(length=None)
    
    test["question_details"] = questions
    
    return test

@router.post("/start/{test_id}")
async def start_test(test_id: str, request: Request):
    """
    Start a test attempt.
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Check if test exists
    test = await db.tests.find_one({"test_id": test_id})
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test not found"
        )
    
    # Create attempt
    attempt_id = f"attempt_{uuid.uuid4().hex[:12]}"
    attempt_doc = {
        "attempt_id": attempt_id,
        "test_id": test_id,
        "student_id": user["user_id"],
        "answers": [],
        "score": 0,
        "total_marks": test["total_marks"],
        "accuracy": 0.0,
        "time_spent": 0,
        "started_at": datetime.now(timezone.utc),
        "submitted_at": None,
        "rank": None
    }
    
    await db.test_attempts.insert_one(attempt_doc)
    attempt_doc.pop("_id", None)
    
    return attempt_doc

@router.put("/answer/{attempt_id}")
async def save_answer(attempt_id: str, answer: AnswerSubmission, request: Request):
    """
    Save/update answer during test.
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Get attempt
    attempt = await db.test_attempts.find_one({"attempt_id": attempt_id})
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test attempt not found"
        )
    
    if attempt["student_id"] != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Get the question to verify answer
    question = await db.questions.find_one({"question_id": answer.question_id})
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check if answer is correct
    answer.is_correct = (answer.selected_answer == question["correct_answer"])
    
    # Update or add answer
    answers = attempt.get("answers", [])
    answer_dict = answer.model_dump()
    
    # Check if answer for this question already exists
    existing_idx = next((i for i, a in enumerate(answers) if a["question_id"] == answer.question_id), None)
    
    if existing_idx is not None:
        answers[existing_idx] = answer_dict
    else:
        answers.append(answer_dict)
    
    await db.test_attempts.update_one(
        {"attempt_id": attempt_id},
        {"$set": {"answers": answers}}
    )
    
    return {"message": "Answer saved", "is_correct": answer.is_correct}

@router.post("/submit/{attempt_id}")
async def submit_test(attempt_id: str, request: Request):
    """
    Submit test and calculate score.
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Get attempt
    attempt = await db.test_attempts.find_one({"attempt_id": attempt_id})
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test attempt not found"
        )
    
    if attempt["student_id"] != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Calculate score
    score = 0
    correct_count = 0
    
    for answer in attempt.get("answers", []):
        if answer["is_correct"]:
            question = await db.questions.find_one({"question_id": answer["question_id"]})
            score += question.get("marks", 4)
            correct_count += 1
        else:
            question = await db.questions.find_one({"question_id": answer["question_id"]})
            score += question.get("negative_marks", -1)
    
    # Calculate accuracy
    total_questions = len(attempt.get("answers", []))
    accuracy = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    # Calculate time spent
    started_at = attempt["started_at"]
    if isinstance(started_at, str):
        started_at = datetime.fromisoformat(started_at)
    time_spent = int((datetime.now(timezone.utc) - started_at).total_seconds())
    
    # Update attempt
    await db.test_attempts.update_one(
        {"attempt_id": attempt_id},
        {
            "$set": {
                "score": score,
                "accuracy": accuracy,
                "time_spent": time_spent,
                "submitted_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {
        "attempt_id": attempt_id,
        "score": score,
        "accuracy": accuracy,
        "time_spent": time_spent,
        "message": "Test submitted successfully"
    }

@router.get("/results/{attempt_id}")
async def get_test_results(attempt_id: str, request: Request):
    """
    Get detailed test results.
    """
    db = get_database()
    user = await get_current_user(request)
    
    attempt = await db.test_attempts.find_one(
        {"attempt_id": attempt_id},
        {"_id": 0}
    )
    
    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test attempt not found"
        )
    
    if attempt["student_id"] != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Get test details
    test = await db.tests.find_one(
        {"test_id": attempt["test_id"]},
        {"_id": 0}
    )
    
    # Get question details with user answers
    question_ids = [a["question_id"] for a in attempt.get("answers", [])]
    questions = await db.questions.find(
        {"question_id": {"$in": question_ids}},
        {"_id": 0}
    ).to_list(length=None)
    
    # Merge answers with questions
    question_map = {q["question_id"]: q for q in questions}
    detailed_answers = []
    
    for answer in attempt.get("answers", []):
        q = question_map.get(answer["question_id"])
        if q:
            detailed_answers.append({
                **answer,
                "question_text": q["question_text"],
                "correct_answer": q["correct_answer"],
                "subject": q["subject"],
                "chapter": q["chapter"],
                "topic": q["topic"],
                "marks": q["marks"],
                "solution_youtube_url": q["solution_youtube_url"],
                "solution_timestamp": q["solution_timestamp"]
            })
    
    return {
        "attempt": attempt,
        "test": test,
        "detailed_answers": detailed_answers
    }
