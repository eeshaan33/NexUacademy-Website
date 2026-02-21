from fastapi import APIRouter, Request
from config.database import get_database
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from collections import defaultdict
import os
from middleware.auth import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/analytics", tags=["analytics"])

class QuestionAttempt(BaseModel):
    question_id: str
    selected_answer: str
    is_correct: bool
    time_taken: Optional[int] = 0

@router.post("/record-attempt")
async def record_question_attempt(attempt: QuestionAttempt, request: Request):
    """
    Record a single question attempt for progress tracking.
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Get question details
    question = await db.questions.find_one(
        {"question_id": attempt.question_id},
        {"_id": 0, "subject": 1, "chapter": 1, "topic": 1}
    )
    
    if not question:
        return {"error": "Question not found"}
    
    # Create attempt record
    attempt_doc = {
        "user_id": user["user_id"],
        "question_id": attempt.question_id,
        "subject": question.get("subject"),
        "chapter": question.get("chapter"),
        "topic": question.get("topic"),
        "selected_answer": attempt.selected_answer,
        "is_correct": attempt.is_correct,
        "time_taken": attempt.time_taken,
        "attempted_at": datetime.now(timezone.utc)
    }
    
    await db.question_attempts.insert_one(attempt_doc)
    
    # Update user stats
    today = datetime.now(timezone.utc).date().isoformat()
    
    # Update or create daily activity record
    await db.user_activity.update_one(
        {"user_id": user["user_id"], "date": today},
        {
            "$inc": {
                "questions_solved": 1,
                "correct_answers": 1 if attempt.is_correct else 0
            },
            "$setOnInsert": {"user_id": user["user_id"], "date": today}
        },
        upsert=True
    )
    
    return {"success": True, "message": "Attempt recorded"}

@router.get("/dashboard")
async def get_dashboard_analytics(request: Request):
    """
    Get overall performance dashboard data.
    """
    db = get_database()
    
    try:
        user = await get_current_user(request)
        user_id = user["user_id"]
    except:
        # Return empty stats for unauthenticated users
        return {
            "total_questions_solved": 0,
            "tests_taken": 0,
            "average_accuracy": 0,
            "current_streak": 0
        }
    
    # Get total questions solved from question_attempts
    total_attempts = await db.question_attempts.count_documents({"user_id": user_id})
    correct_attempts = await db.question_attempts.count_documents({"user_id": user_id, "is_correct": True})
    
    # Calculate accuracy
    accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
    
    # Get tests taken
    tests_taken = await db.test_attempts.count_documents({"student_id": user_id, "submitted_at": {"$ne": None}})
    
    # Calculate streak from user_activity
    streak = await calculate_streak(db, user_id)
    
    return {
        "total_questions_solved": total_attempts,
        "tests_taken": tests_taken,
        "average_accuracy": round(accuracy, 1),
        "current_streak": streak
    }

async def calculate_streak(db, user_id):
    """Calculate consecutive days streak."""
    # Get all activity dates sorted descending
    activities = await db.user_activity.find(
        {"user_id": user_id},
        {"_id": 0, "date": 1}
    ).sort("date", -1).to_list(length=100)
    
    if not activities:
        return 0
    
    streak = 0
    today = datetime.now(timezone.utc).date()
    expected_date = today
    
    for activity in activities:
        activity_date = datetime.fromisoformat(activity["date"]).date() if isinstance(activity["date"], str) else activity["date"]
        
        if activity_date == expected_date:
            streak += 1
            expected_date = expected_date - timedelta(days=1)
        elif activity_date == expected_date - timedelta(days=1):
            # Allow for checking yesterday if today hasn't been recorded yet
            streak += 1
            expected_date = activity_date - timedelta(days=1)
        else:
            break
    
    return streak

@router.get("/subject-wise")
async def get_subject_wise_performance(request: Request):
    """
    Get subject-wise performance.
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Get all test attempts with answers
    attempts = await db.test_attempts.find(
        {"student_id": user["user_id"], "submitted_at": {"$ne": None}},
        {"_id": 0}
    ).to_list(length=None)
    
    # Aggregate by subject
    subject_stats = defaultdict(lambda: {"correct": 0, "total": 0, "time": 0})
    
    for attempt in attempts:
        for answer in attempt.get("answers", []):
            # Get question to find subject
            question = await db.questions.find_one(
                {"question_id": answer["question_id"]},
                {"_id": 0, "subject": 1}
            )
            if question:
                subject = question["subject"]
                subject_stats[subject]["total"] += 1
                if answer.get("is_correct"):
                    subject_stats[subject]["correct"] += 1
                subject_stats[subject]["time"] += answer.get("time_taken", 0)
    
    # Calculate accuracy for each subject
    result = {}
    for subject, stats in subject_stats.items():
        result[subject] = {
            "total_attempted": stats["total"],
            "correct": stats["correct"],
            "accuracy": (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0,
            "avg_time_per_question": stats["time"] / stats["total"] if stats["total"] > 0 else 0
        }
    
    return result

@router.get("/chapter-wise")
async def get_chapter_wise_performance(request: Request):
    """
    Get chapter-wise performance with heatmap data.
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Get all test attempts
    attempts = await db.test_attempts.find(
        {"student_id": user["user_id"], "submitted_at": {"$ne": None}},
        {"_id": 0}
    ).to_list(length=None)
    
    # Aggregate by chapter
    chapter_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    
    for attempt in attempts:
        for answer in attempt.get("answers", []):
            question = await db.questions.find_one(
                {"question_id": answer["question_id"]},
                {"_id": 0, "subject": 1, "chapter": 1}
            )
            if question:
                key = f"{question['subject']}|{question['chapter']}"
                chapter_stats[key]["total"] += 1
                if answer.get("is_correct"):
                    chapter_stats[key]["correct"] += 1
    
    # Format for heatmap
    heatmap_data = []
    for key, stats in chapter_stats.items():
        subject, chapter = key.split("|")
        accuracy = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        heatmap_data.append({
            "subject": subject,
            "chapter": chapter,
            "attempted": stats["total"],
            "accuracy": accuracy
        })
    
    return {"heatmap_data": heatmap_data}

@router.get("/weak-topics")
async def get_weak_topics(request: Request):
    """
    Get weak topics (accuracy < 50%).
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Get all test attempts
    attempts = await db.test_attempts.find(
        {"student_id": user["user_id"], "submitted_at": {"$ne": None}},
        {"_id": 0}
    ).to_list(length=None)
    
    # Aggregate by topic
    topic_stats = defaultdict(lambda: {"correct": 0, "total": 0, "subject": "", "chapter": ""})
    
    for attempt in attempts:
        for answer in attempt.get("answers", []):
            question = await db.questions.find_one(
                {"question_id": answer["question_id"]},
                {"_id": 0, "subject": 1, "chapter": 1, "topic": 1}
            )
            if question:
                topic = question["topic"]
                topic_stats[topic]["total"] += 1
                topic_stats[topic]["subject"] = question["subject"]
                topic_stats[topic]["chapter"] = question["chapter"]
                if answer.get("is_correct"):
                    topic_stats[topic]["correct"] += 1
    
    # Find weak topics
    weak_topics = []
    for topic, stats in topic_stats.items():
        accuracy = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        if accuracy < 50 and stats["total"] >= 3:  # At least 3 attempts
            weak_topics.append({
                "topic": topic,
                "subject": stats["subject"],
                "chapter": stats["chapter"],
                "accuracy": accuracy,
                "attempted": stats["total"]
            })
    
    # Sort by accuracy (worst first)
    weak_topics.sort(key=lambda x: x["accuracy"])
    
    return {"weak_topics": weak_topics[:10]}  # Top 10 weak topics

@router.get("/progress")
async def get_progress_over_time(request: Request):
    """
    Get progress over last 30 days.
    """
    db = get_database()
    user = await get_current_user(request)
    
    # Get attempts from last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    attempts = await db.test_attempts.find(
        {
            "student_id": user["user_id"],
            "submitted_at": {"$gte": thirty_days_ago, "$ne": None}
        },
        {"_id": 0}
    ).sort("submitted_at", 1).to_list(length=None)
    
    # Group by date
    progress = []
    for attempt in attempts:
        submitted = attempt.get("submitted_at")
        if isinstance(submitted, str):
            submitted = datetime.fromisoformat(submitted)
        
        progress.append({
            "date": submitted.date().isoformat(),
            "score": attempt.get("score", 0),
            "accuracy": attempt.get("accuracy", 0),
            "questions_attempted": len(attempt.get("answers", []))
        })
    
    return {"progress": progress}
