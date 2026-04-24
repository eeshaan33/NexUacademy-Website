"""
Student-facing "My Analytics" endpoints.
Aggregates data from test_attempts + user_activity + question_attempts.
"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from config.database import get_database
from middleware.auth import get_current_user

router = APIRouter(prefix="/student/analytics", tags=["student-analytics"])


@router.get("/overview")
async def overview(user=Depends(get_current_user)):
    db = get_database()
    uid = user["user_id"]

    attempts = await db.test_attempts.find(
        {"student_id": uid, "status": "submitted"}, {"_id": 0}
    ).sort("submitted_at", -1).to_list(length=None)

    total_tests = len(attempts)
    total_correct = sum(a.get("correct_answers", 0) for a in attempts)
    total_incorrect = sum(a.get("incorrect_answers", 0) for a in attempts)
    total_unattempted = sum(a.get("unattempted", 0) for a in attempts)

    avg_accuracy = round(
        sum(a.get("accuracy", 0) for a in attempts) / total_tests, 2
    ) if total_tests else 0

    # Best & worst test
    best = max(attempts, key=lambda a: a.get("accuracy", 0)) if attempts else None
    worst = min(attempts, key=lambda a: a.get("accuracy", 0)) if attempts else None

    async def _enrich_name(attempt):
        if not attempt:
            return None
        name = attempt.get("test_name")
        if not name:
            test_doc = await db.teacher_tests.find_one(
                {"test_id": attempt.get("test_id")}, {"_id": 0, "test_name": 1}
            )
            name = (test_doc or {}).get("test_name") or attempt.get("test_id")
        return {
            "test_name": name,
            "accuracy": attempt.get("accuracy"),
            "score": attempt.get("total_score"),
            "max_score": attempt.get("max_score"),
            "attempt_id": attempt.get("attempt_id"),
        }

    best_info = await _enrich_name(best)
    worst_info = await _enrich_name(worst)

    # Rank helper (based on batch peers' last accuracy)
    peers = await db.users.find(
        {"role": "student", "batch_id": user.get("batch_id")},
        {"_id": 0, "user_id": 1}
    ).to_list(length=None)

    peer_ids = [p["user_id"] for p in peers] or [uid]
    peer_attempts = await db.test_attempts.aggregate([
        {"$match": {"student_id": {"$in": peer_ids}, "status": "submitted"}},
        {"$group": {"_id": "$student_id", "avg_acc": {"$avg": "$accuracy"}}},
        {"$sort": {"avg_acc": -1}},
    ]).to_list(length=None)

    rank = next((i + 1 for i, p in enumerate(peer_attempts) if p["_id"] == uid), None)

    return {
        "success": True,
        "total_tests": total_tests,
        "total_questions_attempted": total_correct + total_incorrect,
        "total_correct": total_correct,
        "total_incorrect": total_incorrect,
        "total_unattempted": total_unattempted,
        "avg_accuracy": avg_accuracy,
        "batch_rank": rank,
        "batch_size": len(peer_attempts),
        "best_test": best_info,
        "worst_test": worst_info,
    }


@router.get("/heatmap")
async def subject_chapter_heatmap(user=Depends(get_current_user)):
    """Accuracy per (subject, chapter) combining test answers and question attempts."""
    db = get_database()
    uid = user["user_id"]

    attempts = await db.test_attempts.find(
        {"student_id": uid, "status": "submitted"}, {"_id": 0}
    ).to_list(length=None)

    cells = defaultdict(lambda: {"correct": 0, "total": 0})

    for a in attempts:
        # Need the test to know subject/chapter per question
        test = await db.teacher_tests.find_one(
            {"test_id": a.get("test_id")}, {"_id": 0, "questions": 1}
        )
        q_map = {q["question_number"]: q for q in (test or {}).get("questions", [])}
        for ans in a.get("answers", []):
            q = q_map.get(ans.get("question_number"), {})
            subject = q.get("subject") or "Unknown"
            chapter = q.get("chapter") or "General"
            key = (subject, chapter)
            cells[key]["total"] += 1
            if ans.get("is_correct"):
                cells[key]["correct"] += 1

    # Mix in question_attempts from PYQ section (if any)
    async for qa in db.question_attempts.find({"user_id": uid}, {"_id": 0}):
        subject = qa.get("subject") or "Unknown"
        chapter = qa.get("chapter") or "General"
        key = (subject, chapter)
        cells[key]["total"] += 1
        if qa.get("is_correct"):
            cells[key]["correct"] += 1

    data = []
    for (subject, chapter), stats in cells.items():
        acc = (stats["correct"] / stats["total"] * 100) if stats["total"] else 0
        data.append({
            "subject": subject,
            "chapter": chapter,
            "attempted": stats["total"],
            "correct": stats["correct"],
            "accuracy": round(acc, 1),
        })
    data.sort(key=lambda d: (d["subject"], -d["attempted"]))
    return {"success": True, "heatmap": data}


@router.get("/activity")
async def thirty_day_activity(user=Depends(get_current_user)):
    """30-day chart showing questions solved / accuracy per day."""
    db = get_database()
    uid = user["user_id"]

    start_day = (datetime.now(timezone.utc) - timedelta(days=29)).date()
    buckets = {}
    for i in range(30):
        d = (start_day + timedelta(days=i)).isoformat()
        buckets[d] = {"date": d, "solved": 0, "correct": 0}

    # user_activity daily roll-ups (from PYQ flow)
    activities = await db.user_activity.find(
        {"user_id": uid, "date": {"$gte": start_day.isoformat()}},
        {"_id": 0}
    ).to_list(length=100)
    for a in activities:
        d = a.get("date")
        if d in buckets:
            buckets[d]["solved"] += a.get("questions_solved", 0)
            buckets[d]["correct"] += a.get("correct_answers", 0)

    # test_attempts
    attempts = await db.test_attempts.find(
        {"student_id": uid, "status": "submitted"}, {"_id": 0}
    ).to_list(length=None)
    for a in attempts:
        submitted = a.get("submitted_at")
        if isinstance(submitted, str):
            try:
                submitted = datetime.fromisoformat(submitted.replace("Z", "+00:00"))
            except Exception:
                continue
        if not submitted:
            continue
        d = submitted.date().isoformat()
        if d in buckets:
            buckets[d]["solved"] += a.get("correct_answers", 0) + a.get("incorrect_answers", 0)
            buckets[d]["correct"] += a.get("correct_answers", 0)

    series = list(buckets.values())
    return {"success": True, "activity": series}


@router.get("/leaderboard")
async def leaderboard(user=Depends(get_current_user)):
    """Leaderboard based on average accuracy across a student's batch."""
    db = get_database()
    batch_id = user.get("batch_id")
    if not batch_id:
        return {"success": True, "leaderboard": [], "batch_id": None}

    peers = await db.users.find(
        {"role": "student", "batch_id": batch_id},
        {"_id": 0, "user_id": 1, "name": 1, "profile_pic": 1}
    ).to_list(length=None)
    peer_map = {p["user_id"]: p for p in peers}

    pipeline = [
        {"$match": {"student_id": {"$in": list(peer_map.keys())}, "status": "submitted"}},
        {"$group": {
            "_id": "$student_id",
            "avg_accuracy": {"$avg": "$accuracy"},
            "tests": {"$sum": 1},
            "total_score": {"$sum": "$total_score"},
        }},
        {"$sort": {"avg_accuracy": -1, "tests": -1}},
        {"$limit": 25},
    ]
    rows = await db.test_attempts.aggregate(pipeline).to_list(length=None)

    board = []
    for i, r in enumerate(rows, 1):
        p = peer_map.get(r["_id"], {})
        board.append({
            "rank": i,
            "user_id": r["_id"],
            "name": p.get("name", "—"),
            "profile_pic": p.get("profile_pic"),
            "avg_accuracy": round(r.get("avg_accuracy") or 0, 2),
            "tests": r.get("tests"),
            "total_score": r.get("total_score", 0),
            "is_me": r["_id"] == user["user_id"],
        })
    return {"success": True, "leaderboard": board, "batch_id": batch_id}
