"""Comprehensive Test Analysis Dashboard for students.

Everything is computed server-side with aggressive null/zero guards so the
UI never has to defend against partial data. One endpoint returns the full
9-section payload the dashboard renders.

Also exposes an endpoint to set/replace a self-reported error tag per
question — tags are stored in `attempt_error_tags` with a (attempt, qnum)
uniqueness constraint.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from config.database import get_pool
from middleware.auth import get_current_user
from services.pg_utils import json_safe

router = APIRouter(prefix="/student/tests", tags=["test-analysis"])

ALLOWED_ERROR_TAGS = {
    "Conceptual Mistake",
    "Factual / NCERT Mistake",
    "Calculation Error",
    "Silly / Careless Mistake",
    "Misread Question",
    "Blind Guessing",
    "Time-Pressure Error",
}
CARELESS_TAGS = {"Silly / Careless Mistake", "Misread Question", "Calculation Error"}
TIME_TRAP_THRESHOLD = 150  # seconds


def _safe_pct(num, denom) -> float:
    if not denom:
        return 0.0
    return round((float(num) / float(denom)) * 100, 2)


def _bucket(label: str) -> Dict[str, Any]:
    return {
        "label": label,
        "attempted": 0, "correct": 0, "incorrect": 0, "unattempted": 0,
        "marks_scored": 0, "max_marks": 0, "negative_marks": 0,
        "time_spent": 0,
    }


def _accuracy_label(acc: float) -> str:
    if acc > 80: return "Strong"
    if acc >= 50: return "Moderate"
    return "Weak"


def _ensure_aware(dt):
    if dt and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("/attempts/{attempt_id}/analysis")
async def get_attempt_analysis(attempt_id: str, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        attempt = await conn.fetchrow(
            "SELECT * FROM test_attempts WHERE attempt_id = $1", attempt_id
        )
        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found")
        if str(attempt["student_id"]) != str(user["user_id"]) and user.get("role") not in ("teacher", "admin"):
            raise HTTPException(status_code=403, detail="Not your attempt")
        test = await conn.fetchrow(
            "SELECT test_id, test_name, duration, exam_type, test_pattern, "
            "assigned_batches, questions FROM tests WHERE test_id = $1",
            attempt["test_id"],
        )
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")

        prev_attempt = await conn.fetchrow(
            """SELECT total_score, accuracy, correct_answers, incorrect_answers,
                      unattempted, max_score, time_spent, test_id, submitted_at
                 FROM test_attempts
                WHERE student_id = $1 AND status = 'submitted'
                  AND submitted_at < $2
                ORDER BY submitted_at DESC LIMIT 1""",
            user["user_id"], _ensure_aware(attempt["submitted_at"]) or datetime.now(timezone.utc),
        )
        batch_attempts = await conn.fetch(
            """SELECT attempt_id, student_id, total_score
                 FROM test_attempts
                WHERE test_id = $1 AND status = 'submitted'""",
            attempt["test_id"],
        )
        error_rows = await conn.fetch(
            "SELECT question_number, error_tag FROM attempt_error_tags WHERE attempt_id = $1",
            attempt_id,
        )

    questions = test["questions"] or []
    if isinstance(questions, str):
        import json as _j
        try: questions = _j.loads(questions)
        except Exception: questions = []
    q_by_num: Dict[int, Dict[str, Any]] = {}
    for q in questions:
        try:
            q_by_num[int(q.get("question_number"))] = q
        except (TypeError, ValueError):
            continue

    answers = attempt["answers"] or []
    if isinstance(answers, str):
        import json as _j
        try: answers = _j.loads(answers)
        except Exception: answers = []

    error_tag_map = {int(r["question_number"]): r["error_tag"] for r in error_rows}

    # ---------------- 1. Overall / 2. Subject-wise / 4. Topic buckets --------
    overall = _bucket("Overall")
    by_subject: Dict[str, Dict[str, Any]] = {}
    by_topic: Dict[str, Dict[str, Any]] = {}
    by_difficulty: Dict[str, Dict[str, Any]] = {d: _bucket(d) for d in ("Easy", "Moderate", "Difficult", "Hard", "Medium")}
    by_qtype: Dict[str, Dict[str, Any]] = {}

    per_question_detail: List[Dict[str, Any]] = []
    time_traps: List[Dict[str, Any]] = []

    for ans in answers:
        try:
            qn = int(ans.get("question_number"))
        except (TypeError, ValueError):
            continue
        q = q_by_num.get(qn, {})
        subject = (q.get("subject") or ans.get("subject") or "Unspecified").strip() or "Unspecified"
        topic = (q.get("chapter") or q.get("topic") or "Unspecified").strip() or "Unspecified"
        difficulty = (q.get("difficulty") or ans.get("difficulty") or "Moderate").strip() or "Moderate"
        qtype = (q.get("question_type") or ans.get("question_type") or "MCQ_Single")
        time_taken = int(ans.get("time_taken") or 0)
        selected = ans.get("selected_answer")
        marks_pos = int(q.get("marks") or 4)
        marks_awarded = int(ans.get("marks_awarded") or 0)

        attempted = not (selected is None or selected == "" or (isinstance(selected, list) and not selected))
        is_correct = bool(ans.get("is_correct"))

        for b in (
            overall,
            by_subject.setdefault(subject, _bucket(subject)),
            by_topic.setdefault(topic, {**_bucket(topic), "subject": subject}),
            by_difficulty.setdefault(difficulty, _bucket(difficulty)),
            by_qtype.setdefault(qtype, _bucket(qtype)),
        ):
            b["max_marks"] += marks_pos
            b["time_spent"] += time_taken
            if attempted:
                b["attempted"] += 1
                if is_correct:
                    b["correct"] += 1
                    b["marks_scored"] += marks_awarded
                else:
                    b["incorrect"] += 1
                    if marks_awarded < 0:
                        b["negative_marks"] += abs(marks_awarded)
                        b["marks_scored"] += marks_awarded  # keep running net
            else:
                b["unattempted"] += 1

        is_time_trap = time_taken > TIME_TRAP_THRESHOLD
        detail = {
            "question_number": qn,
            "subject": subject, "topic": topic,
            "difficulty": difficulty, "question_type": qtype,
            "time_taken": time_taken,
            "attempted": attempted,
            "is_correct": is_correct,
            "selected": selected,
            "marks_awarded": marks_awarded,
            "max_marks": marks_pos,
            "is_time_trap": is_time_trap,
            "error_tag": error_tag_map.get(qn),
            "question_text": q.get("question_text") or "",
        }
        per_question_detail.append(detail)
        if is_time_trap:
            time_traps.append(detail)

    # Drop empty difficulty bins that nobody used
    by_difficulty = {k: v for k, v in by_difficulty.items() if v["attempted"] or v["unattempted"]}

    # Finalize per-bucket derived metrics
    def _finalize(b: Dict[str, Any]) -> Dict[str, Any]:
        total = b["attempted"] + b["unattempted"]
        b["total"] = total
        b["attempt_rate"] = _safe_pct(b["attempted"], total)
        b["accuracy"] = _safe_pct(b["correct"], b["attempted"])
        return b

    def _finalize_topic(t: Dict[str, Any]) -> Dict[str, Any]:
        _finalize(t)
        t["strength"] = _accuracy_label(t["accuracy"])
        return t

    overall = _finalize(overall)
    subjects_list = [_finalize(b) for b in by_subject.values()]
    difficulty_list = [_finalize(b) for b in by_difficulty.values()]
    qtype_list = [_finalize(b) for b in by_qtype.values()]
    topics_list = [_finalize_topic(t) for t in by_topic.values()]

    # ---------------- 3. Rank + Percentile ----------------------------------
    scores_sorted = sorted(
        [int(r["total_score"] or 0) for r in batch_attempts], reverse=True
    )
    total_takers = len(scores_sorted) or 1
    my_score = int(attempt["total_score"] or 0)
    rank = 1
    for s in scores_sorted:
        if s > my_score:
            rank += 1
    percentile = round(((total_takers - rank + 1) / total_takers) * 100, 2) if total_takers else 0.0

    # ---------------- 5. Error tagging summary ------------------------------
    error_summary: Dict[str, int] = {t: 0 for t in ALLOWED_ERROR_TAGS}
    total_tagged = 0
    for tag in error_tag_map.values():
        if tag in error_summary:
            error_summary[tag] += 1
            total_tagged += 1
    error_breakdown = [
        {"tag": t, "count": c, "percent": _safe_pct(c, total_tagged)}
        for t, c in error_summary.items()
    ]
    careless_count = sum(error_summary.get(t, 0) for t in CARELESS_TAGS)
    careless_percent = _safe_pct(careless_count, max(total_tagged, 1))

    # ---------------- 6. Previous-test delta --------------------------------
    def _delta(curr, prev):
        if prev is None:
            return None
        try:
            d = round(float(curr) - float(prev), 2)
            return {"delta": d, "direction": "up" if d > 0 else "down" if d < 0 else "flat", "previous": prev}
        except (TypeError, ValueError):
            return None

    prev = json_safe(prev_attempt) if prev_attempt else None
    comparison = None
    if prev:
        comparison = {
            "score": _delta(my_score, prev.get("total_score")),
            "accuracy": _delta(overall["accuracy"], prev.get("accuracy")),
            "negative_marks": _delta(overall["negative_marks"], None),  # computed only on current
            "attempt_rate": _delta(overall["attempt_rate"], None),
            "previous_test_id": prev.get("test_id"),
            "previous_submitted_at": prev.get("submitted_at"),
        }

    # ---------------- 7. Top 3 issues + Next-test goal ----------------------
    weak_topics = sorted(
        [t for t in topics_list if t["attempted"] > 0 and t["accuracy"] < 60],
        key=lambda t: (t["negative_marks"] * -1, t["accuracy"]),
    )[:3]
    top_issues = [
        {
            "topic": t["label"], "subject": t.get("subject", ""),
            "accuracy": t["accuracy"], "negative_marks": t["negative_marks"],
            "incorrect": t["incorrect"], "time_spent": t["time_spent"],
        }
        for t in weak_topics
    ]
    worst_subject = min(subjects_list, key=lambda s: s["accuracy"]) if subjects_list else None
    next_goals: List[str] = []
    if overall["negative_marks"] > 0:
        next_goals.append(
            f"Reduce negative marks by at least {max(2, int(overall['negative_marks'] * 0.3))}"
        )
    if worst_subject and worst_subject["accuracy"] < 80:
        target = min(80, int(worst_subject["accuracy"]) + 10)
        next_goals.append(f"Improve accuracy in {worst_subject['label']} to {target}%")
    if overall["attempt_rate"] < 80:
        next_goals.append(f"Lift overall attempt rate from {overall['attempt_rate']}% to 85%+")
    if not next_goals:
        next_goals.append("Great run — hold this baseline and attempt a mock from a new chapter.")

    # ---------------- 8. Section-wise time + remaining ----------------------
    duration_sec = int(test["duration"] or 0) * 60
    used_time = int(attempt["time_spent"] or 0)
    remaining = max(duration_sec - used_time, 0)

    return {
        "success": True,
        "attempt": {
            "attempt_id": attempt_id,
            "test_id": attempt["test_id"],
            "test_name": test["test_name"],
            "exam_type": test["exam_type"],
            "duration_minutes": test["duration"],
            "submitted_at": json_safe({"x": attempt["submitted_at"]})["x"],
            "time_spent": used_time,
            "remaining_time": remaining,
        },
        "summary": {
            "total_score": my_score,
            "max_score": int(attempt["max_score"] or 0),
            "correct": overall["correct"],
            "incorrect": overall["incorrect"],
            "unattempted": overall["unattempted"],
            "total_questions": overall["total"],
            "attempt_rate": overall["attempt_rate"],
            "accuracy": overall["accuracy"],
            "negative_marks": overall["negative_marks"],
            "percent_score": _safe_pct(my_score, max(int(attempt["max_score"] or 0), 1)),
        },
        "rank": {
            "rank": rank,
            "total_takers": total_takers,
            "percentile": percentile,
        },
        "by_subject": subjects_list,
        "by_topic": topics_list,
        "by_difficulty": difficulty_list,
        "by_question_type": qtype_list,
        "time_analysis": {
            "total_time_spent": used_time,
            "remaining_time": remaining,
            "time_traps": time_traps,
            "trap_threshold_seconds": TIME_TRAP_THRESHOLD,
            "per_subject": [
                {"subject": s["label"], "time_spent": s["time_spent"],
                 "avg_per_question": round(s["time_spent"] / max(s["total"], 1), 2)}
                for s in subjects_list
            ],
        },
        "errors": {
            "allowed_tags": sorted(ALLOWED_ERROR_TAGS),
            "breakdown": error_breakdown,
            "total_tagged": total_tagged,
            "untagged_incorrect": overall["incorrect"] - total_tagged if overall["incorrect"] > total_tagged else 0,
            "careless_percent": careless_percent,
        },
        "comparison": comparison,
        "action_points": {
            "top_issues": top_issues,
            "next_goals": next_goals,
        },
        "per_question": per_question_detail,
    }


class ErrorTagBody(BaseModel):
    question_number: int
    error_tag: Optional[str] = None  # pass null to clear


@router.post("/attempts/{attempt_id}/error-tag")
async def set_error_tag(attempt_id: str, body: ErrorTagBody, user=Depends(get_current_user)):
    pool = get_pool()
    async with pool.acquire() as conn:
        a = await conn.fetchrow(
            "SELECT student_id FROM test_attempts WHERE attempt_id = $1", attempt_id
        )
        if not a:
            raise HTTPException(status_code=404, detail="Attempt not found")
        if str(a["student_id"]) != str(user["user_id"]):
            raise HTTPException(status_code=403, detail="Not your attempt")

        if body.error_tag is None or body.error_tag == "":
            await conn.execute(
                "DELETE FROM attempt_error_tags WHERE attempt_id = $1 AND question_number = $2",
                attempt_id, body.question_number,
            )
            return {"success": True, "cleared": True}

        if body.error_tag not in ALLOWED_ERROR_TAGS:
            raise HTTPException(status_code=400, detail="Unknown error tag")

        await conn.execute(
            """INSERT INTO attempt_error_tags (attempt_id, question_number, error_tag)
               VALUES ($1, $2, $3)
               ON CONFLICT (attempt_id, question_number)
               DO UPDATE SET error_tag = EXCLUDED.error_tag, updated_at = NOW()""",
            attempt_id, body.question_number, body.error_tag,
        )
    return {"success": True, "error_tag": body.error_tag}
