"""Iteration 19 — Test Time Guard.

Server must reject POST /api/student/tests/attempts/{id}/submit when
(now - started_at) > test.duration + SUBMIT_GRACE_SECONDS (=60s), auto-closing
the stale attempt with status='expired'.
"""
import asyncio
import os
import sys
import uuid

import asyncpg
import pytest
import requests

BACKEND_DIR = "/app/backend"
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# load DATABASE_URL from backend/.env
from dotenv import load_dotenv
load_dotenv("/app/backend/.env")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://neet-jee-prep-55.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
DATABASE_URL = os.environ["DATABASE_URL"]

TEACHER = {"email": "teacher@test.com", "password": "password123"}
STUDENT = {"email": "student@test.com", "password": "password123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login {creds['email']} failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def h(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT)


@pytest.fixture(scope="module")
def teacher_token():
    return _login(TEACHER)


def _make_test(teacher_token, duration_minutes, name_suffix=""):
    questions = [
        {"question_number": 1, "question_type": "MCQ_Single", "question_text": "1+1?",
         "options": ["A) 2", "B) 3", "C) 4", "D) 5"], "correct_answers": ["A"],
         "marks": 4, "negative_marks": -1},
        {"question_number": 2, "question_type": "MCQ_Single", "question_text": "2+2?",
         "options": ["A) 3", "B) 4", "C) 5", "D) 6"], "correct_answers": ["B"],
         "marks": 4, "negative_marks": -1},
    ]
    payload = {
        "test_name": f"TEST_timeguard_{uuid.uuid4().hex[:6]}{name_suffix}",
        "subject": "Physics",
        "test_type": "chapter",
        "exam_type": "JEE Main",
        "duration": duration_minutes,
        "total_questions": 2,
        "total_marks": 8,
        "assigned_batches": ["JEEM2027"],
        "questions": questions,
        "status": "scheduled",
    }
    r = requests.post(f"{API}/teacher/tests/create", headers=h(teacher_token),
                      json=payload, timeout=30)
    assert r.status_code == 200, f"create test failed: {r.status_code} {r.text}"
    return r.json()["test"]


def _start_attempt(student_token, test_id):
    r = requests.post(f"{API}/student/tests/{test_id}/start",
                      headers=h(student_token), json={}, timeout=20)
    assert r.status_code == 200, f"start failed: {r.status_code} {r.text}"
    return r.json()["attempt"]["attempt_id"]


async def _backdate_started_at(attempt_id, seconds_ago):
    conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)
    try:
        await conn.execute(
            "UPDATE test_attempts SET started_at = NOW() - ($1 || ' seconds')::interval WHERE attempt_id = $2",
            str(seconds_ago), attempt_id,
        )
    finally:
        await conn.close()


async def _fetch_attempt(attempt_id):
    conn = await asyncpg.connect(DATABASE_URL, statement_cache_size=0)
    try:
        row = await conn.fetchrow(
            "SELECT attempt_id, status, submitted_at, total_score FROM test_attempts WHERE attempt_id = $1",
            attempt_id,
        )
        return dict(row) if row else None
    finally:
        await conn.close()


def _cleanup_test(teacher_token, test_id):
    try:
        requests.delete(f"{API}/teacher/tests/{test_id}",
                        headers=h(teacher_token), timeout=15)
    except Exception:
        pass


# ------------------- Happy path (regression) -------------------
def test_happy_path_60min_submit_succeeds(student_token, teacher_token):
    """Duration 60 min, submit immediately — must succeed with server score."""
    t = _make_test(teacher_token, duration_minutes=60, name_suffix="_happy")
    try:
        attempt_id = _start_attempt(student_token, t["test_id"])
        answers = [
            {"question_number": 1, "selected_answer": "A"},
            {"question_number": 2, "selected_answer": "B"},
        ]
        r = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                          headers=h(student_token),
                          json={"answers": answers, "time_spent": 10}, timeout=30)
        assert r.status_code == 200, r.text
        att = r.json()["attempt"]
        assert att["status"] == "submitted"
        assert att["total_score"] == 8
        assert att["correct_answers"] == 2
    finally:
        _cleanup_test(teacher_token, t["test_id"])


# ------------------- Expired path -------------------
def test_expired_submit_rejected_with_400(student_token, teacher_token):
    """Duration=1min, backdate started_at by 5min → submit MUST 400 with 'expired'
    detail; attempt row status MUST flip to 'expired' + submitted_at set."""
    # Min duration on create is 15 min. Use 15; grace=60s → cutoff 960s.
    t = _make_test(teacher_token, duration_minutes=15, name_suffix="_expired")
    try:
        attempt_id = _start_attempt(student_token, t["test_id"])
        # Backdate 20 minutes = 1200s > 960s (well past grace).
        asyncio.get_event_loop().run_until_complete(
            _backdate_started_at(attempt_id, 1200)
        )
        answers = [{"question_number": 1, "selected_answer": "A"},
                   {"question_number": 2, "selected_answer": "B"}]
        r = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                          headers=h(student_token),
                          json={"answers": answers, "time_spent": 10}, timeout=30)
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text}"
        detail = (r.json().get("detail") or "").lower()
        assert "expired" in detail or "test time expired" in detail, \
            f"detail missing 'expired': {r.text}"

        # DB check: row must be status='expired' with submitted_at set
        row = asyncio.get_event_loop().run_until_complete(_fetch_attempt(attempt_id))
        assert row is not None
        assert row["status"] == "expired", f"status={row['status']}"
        assert row["submitted_at"] is not None, "submitted_at must be set on auto-close"

        # Follow-up: re-submit still 400
        r2 = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                           headers=h(student_token),
                           json={"answers": answers, "time_spent": 10}, timeout=30)
        assert r2.status_code == 400, f"second submit expected 400 got {r2.status_code}: {r2.text}"
        detail2 = (r2.json().get("detail") or "").lower()
        assert "expired" in detail2

        # Autosave on expired: currently returns 200 skipped — must not error
        r3 = requests.put(f"{API}/student/tests/attempts/{attempt_id}/autosave",
                          headers=h(student_token),
                          json={"answers": answers}, timeout=15)
        assert r3.status_code == 200, r3.text
    finally:
        _cleanup_test(teacher_token, t["test_id"])


# ------------------- Grace window: inside grace succeeds -------------------
def test_grace_window_inside_succeeds(student_token, teacher_token):
    """Duration=1min, backdate started_at by 60+30=90s (30s inside grace) →
    submit MUST 200 with server-authoritative score."""
    # duration=15min → 900s; grace 60s → cutoff 960s. Backdate 930s (30s inside grace).
    t = _make_test(teacher_token, duration_minutes=15, name_suffix="_grace_in")
    try:
        attempt_id = _start_attempt(student_token, t["test_id"])
        asyncio.get_event_loop().run_until_complete(
            _backdate_started_at(attempt_id, 930)  # 30s inside grace
        )
        answers = [{"question_number": 1, "selected_answer": "A"},
                   {"question_number": 2, "selected_answer": "B"}]
        r = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                          headers=h(student_token),
                          json={"answers": answers, "time_spent": 90}, timeout=30)
        assert r.status_code == 200, f"expected 200 got {r.status_code}: {r.text}"
        att = r.json()["attempt"]
        assert att["status"] == "submitted"
        assert att["total_score"] == 8
    finally:
        _cleanup_test(teacher_token, t["test_id"])


# ------------------- Grace window: outside grace rejected -------------------
def test_grace_window_outside_rejected(student_token, teacher_token):
    """Duration=1min, backdate started_at by 60+90=150s (30s past grace) →
    submit MUST 400."""
    # duration=15min → cutoff 960s. Backdate 990s (30s past grace).
    t = _make_test(teacher_token, duration_minutes=15, name_suffix="_grace_out")
    try:
        attempt_id = _start_attempt(student_token, t["test_id"])
        asyncio.get_event_loop().run_until_complete(
            _backdate_started_at(attempt_id, 990)
        )
        answers = [{"question_number": 1, "selected_answer": "A"},
                   {"question_number": 2, "selected_answer": "B"}]
        r = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                          headers=h(student_token),
                          json={"answers": answers, "time_spent": 150}, timeout=30)
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text}"
        detail = (r.json().get("detail") or "").lower()
        assert "expired" in detail
    finally:
        _cleanup_test(teacher_token, t["test_id"])


# ------------------- Idempotency preserved -------------------
def test_idempotent_resubmit_after_valid_submit(student_token, teacher_token):
    """Submit normally; second submit → 200 with status='submitted', resubmitted:false,
    score not re-written."""
    t = _make_test(teacher_token, duration_minutes=60, name_suffix="_idempo19")
    try:
        attempt_id = _start_attempt(student_token, t["test_id"])
        good = [{"question_number": 1, "selected_answer": "A"},
                {"question_number": 2, "selected_answer": "B"}]
        r1 = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                           headers=h(student_token),
                           json={"answers": good, "time_spent": 30}, timeout=30)
        assert r1.status_code == 200
        att1 = r1.json()["attempt"]
        assert att1["total_score"] == 8

        # Second submit with wrong answers
        wrong = [{"question_number": 1, "selected_answer": "X"},
                 {"question_number": 2, "selected_answer": "X"}]
        r2 = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                           headers=h(student_token),
                           json={"answers": wrong, "time_spent": 60}, timeout=30)
        assert r2.status_code == 200, r2.text
        body2 = r2.json()
        att2 = body2["attempt"]
        assert att2["status"] == "submitted"
        assert att2["total_score"] == 8  # unchanged
        assert body2.get("resubmitted") is False
    finally:
        _cleanup_test(teacher_token, t["test_id"])
