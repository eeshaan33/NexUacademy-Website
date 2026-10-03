"""Backend tests for the Feb 2026 refactor:
- Question Bank fixed folder tree + 15 MB total image cap + difficulty
  Easy/Moderate/Difficult.
- Test Analysis Dashboard endpoints (analysis + error-tag).
"""
import io
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://nexu-qbank.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

TEACHER_EMAIL = "nitinsaini.iitkgp@gmail.com"
TEACHER_PASS = "nitin@123"
STUDENT_EMAIL = "student@test.com"
STUDENT_PASS = "password123"


def _login(email: str, password: str):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"login failed {email}: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("token") or data.get("access_token") or (data.get("session") or {}).get("access_token")
    assert tok, f"no token in login response: {data}"
    return tok, data


@pytest.fixture(scope="module")
def teacher_token():
    return _login(TEACHER_EMAIL, TEACHER_PASS)[0]


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT_EMAIL, STUDENT_PASS)[0]


def _h(tok):
    return {"Authorization": f"Bearer {tok}"}


# ---------- Folders ----------------------------------------------------------
def test_folders_auth_required():
    r = requests.get(f"{API}/teacher/qb/folders", timeout=15)
    assert r.status_code in (401, 403), r.status_code


def test_folders_forbidden_for_student(student_token):
    r = requests.get(f"{API}/teacher/qb/folders", headers=_h(student_token), timeout=15)
    assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text[:200]}"


def test_folders_tree_shape(teacher_token):
    r = requests.get(f"{API}/teacher/qb/folders", headers=_h(teacher_token), timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["success"] is True
    roots = {n["name"] for n in data["folders"]}
    assert {"PYQ", "Non-PYQ"}.issubset(roots), f"roots={roots}"

    # Walk to PYQ > JEE > JEE Mains > Physics
    def find(nodes, name):
        for n in nodes:
            if n["name"] == name:
                return n
        return None

    pyq = find(data["folders"], "PYQ")
    jee = find(pyq["children"], "JEE")
    assert jee is not None
    mains = find(jee["children"], "JEE Mains")
    adv = find(jee["children"], "JEE Advanced")
    assert mains and adv
    phy = find(mains["children"], "Physics")
    assert phy and phy["is_leaf"]

    neet = find(pyq["children"], "NEET")
    assert neet
    neet_subs = {c["name"] for c in neet["children"]}
    assert {"Physics", "Chemistry", "Biology"}.issubset(neet_subs)

    oly = find(pyq["children"], "Olympiads")
    assert oly
    oly_subs = {c["name"] for c in oly["children"]}
    assert {"NSEP", "NSEC", "NSEB", "NSEA", "NSEJS"}.issubset(oly_subs)

    non = find(data["folders"], "Non-PYQ")
    non_subs = {c["name"] for c in non["children"]}
    assert {"Physics", "Chemistry", "Maths", "Biology"}.issubset(non_subs)

    # Expose leaf id for subsequent tests
    pytest.jee_mains_physics_id = phy["id"]


# ---------- Difficulty validation -------------------------------------------
def test_difficulty_rejects_legacy_hard(teacher_token):
    folder_id = getattr(pytest, "jee_mains_physics_id", None)
    assert folder_id, "pre-req folder tree test must run first"
    files = {}
    data = {
        "folder_id": folder_id,
        "question_text": "TEST_ difficulty validation",
        "question_type": "MCQ_Single",
        "options_text": '{"A":"a","B":"b","C":"c","D":"d"}',
        "correct_answers": '["A"]',
        "difficulty": "Hard",
        "marks": 4,
        "negative_marks": -1,
    }
    r = requests.post(f"{API}/teacher/question-bank", headers=_h(teacher_token), data=data, files=files, timeout=30)
    assert r.status_code == 400, f"expected 400 got {r.status_code} {r.text[:300]}"
    body = r.json()
    detail = str(body.get("detail", "")).lower()
    assert "easy" in detail and "moderate" in detail and "difficult" in detail, body


# ---------- 15 MB image cap --------------------------------------------------
def test_image_cap_rejects_16mb_upload(teacher_token):
    folder_id = getattr(pytest, "jee_mains_physics_id", None)
    assert folder_id
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (16 * 1024 * 1024)  # ~16 MB
    files = {"question_image": ("big.png", io.BytesIO(big), "image/png")}
    data = {
        "folder_id": folder_id,
        "question_text": "TEST_ oversized image",
        "question_type": "MCQ_Single",
        "options_text": '{"A":"a","B":"b","C":"c","D":"d"}',
        "correct_answers": '["A"]',
        "difficulty": "Moderate",
    }
    r = requests.post(f"{API}/teacher/question-bank", headers=_h(teacher_token), data=data, files=files, timeout=120)
    assert r.status_code == 400, f"expected 400 got {r.status_code} {r.text[:300]}"
    detail = str(r.json().get("detail", "")).lower()
    assert "15 mb" in detail or "exceeds" in detail, detail


# ---------- Create question happy path --------------------------------------
def test_create_question_moderate_in_jee_mains_physics(teacher_token):
    folder_id = getattr(pytest, "jee_mains_physics_id", None)
    assert folder_id
    data = {
        "folder_id": folder_id,
        "question_text": f"TEST_ auto {uuid.uuid4().hex[:6]}",
        "question_type": "MCQ_Single",
        "options_text": '{"A":"a","B":"b","C":"c","D":"d"}',
        "correct_answers": '["A"]',
        "difficulty": "Moderate",
        "marks": 4,
        "negative_marks": -1,
    }
    r = requests.post(f"{API}/teacher/question-bank", headers=_h(teacher_token), data=data, timeout=30)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] and body["question"]["difficulty"] == "Moderate"
    assert body["question"]["folder_id"] == folder_id
    pytest.created_qid = body["question"]["id"]


def test_list_questions_shows_created(teacher_token):
    folder_id = getattr(pytest, "jee_mains_physics_id", None)
    r = requests.get(f"{API}/teacher/question-bank", params={"folder_id": folder_id}, headers=_h(teacher_token), timeout=30)
    assert r.status_code == 200
    ids = [q["id"] for q in r.json()["questions"]]
    assert getattr(pytest, "created_qid", None) in ids


# ---------- Analysis endpoint auth / errors ---------------------------------
def test_analysis_bad_attempt_returns_404(student_token):
    bad_id = "00000000-0000-0000-0000-000000000000"
    r = requests.get(f"{API}/student/tests/attempts/{bad_id}/analysis", headers=_h(student_token), timeout=20)
    assert r.status_code == 404, f"got {r.status_code} {r.text[:200]}"


def test_error_tag_bad_attempt(student_token):
    bad_id = "00000000-0000-0000-0000-000000000000"
    r = requests.post(
        f"{API}/student/tests/attempts/{bad_id}/error-tag",
        headers=_h(student_token),
        json={"question_number": 1, "error_tag": "Conceptual Mistake"},
        timeout=20,
    )
    assert r.status_code in (403, 404), r.status_code


def test_error_tag_unknown_tag_rejected(student_token):
    # Try first on a bogus attempt; if 404, we still need to assert unknown-tag.
    # Find a real attempt owned by this student if any.
    attempts_resp = requests.get(f"{API}/student/tests/attempts", headers=_h(student_token), timeout=20)
    aid = None
    if attempts_resp.status_code == 200:
        js = attempts_resp.json()
        items = js.get("attempts") or js.get("items") or (js if isinstance(js, list) else [])
        for a in items:
            if a.get("status") == "submitted":
                aid = a.get("attempt_id") or a.get("id")
                break
    if not aid:
        pytest.skip("no submitted attempt available to test unknown tag")
    r = requests.post(
        f"{API}/student/tests/attempts/{aid}/error-tag",
        headers=_h(student_token),
        json={"question_number": 1, "error_tag": "NOT_A_TAG"},
        timeout=20,
    )
    assert r.status_code == 400, r.text
    assert "unknown error tag" in r.json().get("detail", "").lower()
