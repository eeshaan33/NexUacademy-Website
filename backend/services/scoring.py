"""Authoritative server-side scoring for test attempts.

The client is NEVER trusted for is_correct. This module recomputes correctness
for every submitted answer by comparing the student's selected_answer against
the test's stored question data (options + correct_answers / numerical_answer).

Supports MCQ_Single, MCQ_Multiple, and Numerical (Integer/Decimal) question
types. Falls back gracefully for unknown types (marks it unattempted).
"""
from typing import Any


def _normalize_answer_list(raw) -> list[str]:
    """Return correct answers as an uppercased list of strings."""
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw.strip().upper()]
    if isinstance(raw, (list, tuple)):
        return [str(x).strip().upper() for x in raw if str(x).strip()]
    return [str(raw).strip().upper()]


def _correct_for_question(q: dict) -> tuple[list[str], Any]:
    """Extract correct answers from a stored question in a robust way.

    Returns (correct_options, numerical_answer).
    Different teacher/CSV import paths save the field under different keys:
    correct_answers (list), correct_answer (single), answer, correctAnswer.
    """
    raw = (
        q.get("correct_answers")
        or q.get("correct_answer")
        or q.get("answer")
        or q.get("correctAnswer")
    )
    return _normalize_answer_list(raw), q.get("numerical_answer") or q.get("correct_numerical")


def _score_one(q: dict, selected) -> tuple[bool, bool]:
    """Return (is_correct, is_attempted) for a single answer.

    An answer is considered attempted if `selected` has any meaningful value.
    """
    if selected is None or selected == "" or (isinstance(selected, list) and not selected):
        return False, False

    qtype = (q.get("question_type") or "").strip()
    correct_opts, numerical_ans = _correct_for_question(q)

    if qtype.startswith("Numerical"):
        try:
            val = float(str(selected).strip())
            target = float(numerical_ans) if numerical_ans is not None else None
        except (TypeError, ValueError):
            return False, True
        if target is None:
            return False, True
        rng = q.get("answer_range") or {}
        try:
            lo = float(rng.get("min")) if rng.get("min") is not None else target - 0.01
            hi = float(rng.get("max")) if rng.get("max") is not None else target + 0.01
        except (TypeError, ValueError):
            lo, hi = target - 0.01, target + 0.01
        return (lo <= val <= hi), True

    if qtype == "MCQ_Multiple":
        picked = set(_normalize_answer_list(selected))
        return (picked == set(correct_opts) and bool(correct_opts)), True

    # Default: single-answer MCQ
    picked = _normalize_answer_list(selected)
    if not picked:
        return False, False
    return (picked[0] in correct_opts and bool(correct_opts)), True


def score_attempt(questions: list[dict], client_answers: list[dict]) -> dict:
    """Recompute the entire attempt score server-side.

    - `questions`: list of question dicts stored inline on `tests.questions`.
    - `client_answers`: list of `{question_number, selected_answer, flagged?, time_taken?}`.

    Returns a dict with:
      - authoritative_answers: list mirroring client_answers but with server-set
        `is_correct` and `marks_awarded` (client-set is_correct is DISCARDED).
      - total_score, max_score, correct_answers, incorrect_answers,
        unattempted, accuracy.
    """
    by_num: dict[int, dict] = {}
    for q in questions or []:
        try:
            by_num[int(q.get("question_number"))] = q
        except (TypeError, ValueError):
            continue

    total_score = 0
    max_score = 0
    correct = 0
    incorrect = 0
    unattempted = 0

    authoritative: list[dict] = []
    seen_nums: set[int] = set()

    for ans in client_answers or []:
        try:
            qn = int(ans.get("question_number"))
        except (TypeError, ValueError):
            continue
        seen_nums.add(qn)
        q = by_num.get(qn)
        if not q:
            authoritative.append({
                "question_number": qn,
                "selected_answer": ans.get("selected_answer"),
                "is_correct": False,
                "marks_awarded": 0,
                "flagged": bool(ans.get("flagged")),
                "time_taken": int(ans.get("time_taken") or 0),
            })
            continue

        marks_pos = int(q.get("marks") or 4)
        marks_neg = -abs(int(q.get("negative_marks") or 0))  # clamp to <= 0 defensively
        max_score += marks_pos

        selected = ans.get("selected_answer")
        is_correct, is_attempted = _score_one(q, selected)

        if is_attempted:
            if is_correct:
                awarded = marks_pos
                correct += 1
            else:
                awarded = marks_neg  # already negative
                incorrect += 1
        else:
            awarded = 0
            unattempted += 1

        total_score += awarded
        authoritative.append({
            "question_number": qn,
            "selected_answer": selected,
            "is_correct": is_correct,
            "marks_awarded": awarded,
            "flagged": bool(ans.get("flagged")),
            "time_taken": int(ans.get("time_taken") or 0),
        })

    # Include unseen questions as unattempted so max_score reflects the full test
    for qn, q in by_num.items():
        if qn in seen_nums:
            continue
        marks_pos = int(q.get("marks") or 4)
        max_score += marks_pos
        unattempted += 1
        authoritative.append({
            "question_number": qn,
            "selected_answer": None,
            "is_correct": False,
            "marks_awarded": 0,
            "flagged": False,
            "time_taken": 0,
        })

    total_attempted = correct + incorrect
    accuracy = round((correct / total_attempted) * 100, 2) if total_attempted else 0.0

    return {
        "authoritative_answers": authoritative,
        "total_score": total_score,
        "max_score": max_score,
        "correct_answers": correct,
        "incorrect_answers": incorrect,
        "unattempted": unattempted,
        "accuracy": accuracy,
    }
