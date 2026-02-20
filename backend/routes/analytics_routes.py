from fastapi import APIRouter, Request
from config.database import get_database
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from collections import defaultdict
import os
from middleware.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])

db = get_database()

@router.get("/dashboard")
async def get_dashboard_analytics(request: Request):
    """
    Get overall performance dashboard data.
    """
    user = await get_current_user(request)
    
    # Get all test attempts
    attempts = await db.test_attempts.find(
        {"student_id": user["user_id"], "submitted_at": {"$ne": None}},
        {"_id": 0}
    ).to_list(length=None)
    
    # Calculate stats
    total_tests = len(attempts)
    total_questions = sum(len(a.get("answers", [])) for a in attempts)
    avg_score = sum(a.get("score", 0) for a in attempts) / total_tests if total_tests > 0 else 0
    avg_accuracy = sum(a.get("accuracy", 0) for a in attempts) / total_tests if total_tests > 0 else 0
    
    # Calculate streak (simplified)
    streak = 0
    if attempts:
        last_date = None
        for attempt in sorted(attempts, key=lambda x: x.get("submitted_at", datetime.min), reverse=True):
            submitted = attempt.get("submitted_at")
            if isinstance(submitted, str):
                submitted = datetime.fromisoformat(submitted)
            
            if last_date is None:
                streak = 1
                last_date = submitted.date()
            else:
                diff = (last_date - submitted.date()).days
                if diff == 1:
                    streak += 1
                    last_date = submitted.date()
                else:
                    break
    
    return {
        "total_questions_solved": total_questions,
        "tests_taken": total_tests,
        "average_score": round(avg_score, 2),
        "average_accuracy": round(avg_accuracy, 2),
        "current_streak": streak
    }

@router.get("/subject-wise")
async def get_subject_wise_performance(request: Request):
    """
    Get subject-wise performance.
    """
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
