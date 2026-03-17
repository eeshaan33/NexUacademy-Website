from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import datetime, timezone, timedelta
from config.database import get_database
from middleware.auth import get_current_teacher

router = APIRouter(prefix="/teacher/students", tags=["teacher-students"])


@router.get("/")
async def get_students(
    batch_id: str = Query(None),
    course: str = Query(None),
    user=Depends(get_current_teacher),
):
    db = get_database()
    query = {"role": "student"}
    if batch_id:
        query["batch_id"] = batch_id
    if course:
        query["course"] = course

    students = await db.users.find(query, {"_id": 0, "password": 0}).sort("name", 1).to_list(length=None)
    return {"success": True, "students": students, "count": len(students)}


@router.get("/{student_id}/analytics")
async def get_student_analytics(student_id: str, user=Depends(get_current_teacher)):
    db = get_database()
    student = await db.users.find_one({"user_id": student_id, "role": "student"}, {"_id": 0, "password": 0})
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Test attempts
    attempts = await db.test_attempts.find(
        {"student_id": student_id}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=20)

    total_tests = len(attempts)
    avg_score = 0
    if total_tests > 0:
        scores = []
        for a in attempts:
            max_s = a.get("max_score", 1)
            if max_s > 0:
                scores.append((a.get("total_score", 0) / max_s) * 100)
        avg_score = sum(scores) / len(scores) if scores else 0

    # Questions solved last 7 days
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    week_stats = await db.question_analytics.find(
        {"student_id": student_id, "date": {"$gte": seven_days_ago}}
    ).to_list(length=None)
    questions_this_week = sum(s.get("questions_solved", 0) for s in week_stats)

    # Daily activity last 30 days
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    daily_activity = await db.question_analytics.find(
        {"student_id": student_id, "date": {"$gte": thirty_days_ago}}, {"_id": 0}
    ).sort("date", 1).to_list(length=None)

    total_solved = sum(d.get("questions_solved", 0) for d in daily_activity)
    total_correct = sum(d.get("questions_correct", 0) for d in daily_activity)
    overall_accuracy = (total_correct / total_solved * 100) if total_solved > 0 else 0

    return {
        "success": True,
        "student": student,
        "analytics": {
            "total_tests_attempted": total_tests,
            "average_score": round(avg_score, 2),
            "questions_this_week": questions_this_week,
            "overall_accuracy": round(overall_accuracy, 2),
            "test_attempts": attempts,
            "daily_activity": daily_activity,
        },
    }
