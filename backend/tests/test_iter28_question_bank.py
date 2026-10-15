"""Iteration 28: Question Bank + Smart Test Creation E2E backend tests.

Covers:
- Feature flag surface in /auth/me
- 403 access boundary for non-allowlisted teacher
- Topic/subtopic create-or-return idempotency
- Question creation (MCQ_Single with image, Numerical_Decimal)
- Tree endpoint counts
- Per-batch available/record-assignments smart exclusion
- Delete protection + force
- Public storage URL reachability
"""
import io
import os
import struct
import zlib
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://nexu-qbank.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

NITIN = ("nitin@nexuacademy.com", "nitin@123")
OTHER = ("teacher@test.com", "password123")


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"login {email} failed: {r.status_code} {r.text}"
    tok = r.json().get("access_token") or r.json().get("token")
    assert tok, f"no token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def nitin_headers():
    return {"Authorization": f"Bearer {_login(*NITIN)}"}


@pytest.fixture(scope="module")
def other_headers():
    return {"Authorization": f"Bearer {_login(*OTHER)}"}


def _tiny_png_bytes():
    # 1x1 red PNG constructed by hand (no PIL dependency)
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = b"\x00" + bytes([255, 0, 0])
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


# ---- 1. /auth/me feature flag ------------------------------------------------
def test_me_feature_flag_true_for_nitin(nitin_headers):
    r = requests.get(f"{API}/auth/me", headers=nitin_headers, timeout=30)
    assert r.status_code == 200
    body = r.json()
    user = body.get("user", body)
    assert user.get("features", {}).get("question_bank") is True, user


def test_me_feature_flag_false_for_other(other_headers):
    r = requests.get(f"{API}/auth/me", headers=other_headers, timeout=30)
    assert r.status_code == 200
    body = r.json()
    user = body.get("user", body)
    assert user.get("features", {}).get("question_bank") is False, user


# ---- 2. Access control -------------------------------------------------------
def test_topics_403_for_other(other_headers):
    r = requests.get(f"{API}/teacher/topics", headers=other_headers, timeout=30)
    assert r.status_code == 403, r.text


def test_topics_200_for_nitin(nitin_headers):
    r = requests.get(f"{API}/teacher/topics", headers=nitin_headers, timeout=30)
    assert r.status_code == 200
    assert "topics" in r.json()


# ---- 3. Topic + Subtopic create-or-return -----------------------------------
@pytest.fixture(scope="module")
def topic_id(nitin_headers):
    suffix = uuid.uuid4().hex[:6]
    name = f"Thermodynamics_{suffix}"
    r = requests.post(f"{API}/teacher/topics", headers=nitin_headers,
                      json={"name": name, "subject": "Chemistry"}, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["created"] is True
    tid = data["topic"]["id"]
    # duplicate lowercase -> same id, created=False
    r2 = requests.post(f"{API}/teacher/topics", headers=nitin_headers,
                       json={"name": name.lower(), "subject": "Chemistry"}, timeout=30)
    assert r2.status_code == 200
    assert r2.json()["created"] is False
    assert r2.json()["topic"]["id"] == tid
    return tid


@pytest.fixture(scope="module")
def subtopic_id(nitin_headers, topic_id):
    suffix = uuid.uuid4().hex[:6]
    name = f"Free Energy {suffix}"
    r = requests.post(f"{API}/teacher/subtopics", headers=nitin_headers,
                      json={"topic_id": topic_id, "name": name}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert data["created"] is True
    sid = data["subtopic"]["id"]
    r2 = requests.post(f"{API}/teacher/subtopics", headers=nitin_headers,
                       json={"topic_id": topic_id, "name": name.lower()}, timeout=30)
    assert r2.json()["created"] is False
    assert r2.json()["subtopic"]["id"] == sid
    return sid


# ---- 4. Question creation ----------------------------------------------------
@pytest.fixture(scope="module")
def question_ids(nitin_headers, topic_id, subtopic_id):
    ids = []
    # MCQ_Single with image
    files = {"question_image": ("q.png", _tiny_png_bytes(), "image/png")}
    data = {
        "topic_id": topic_id,
        "subtopic_id": subtopic_id,
        "question_text": "TEST_ Which law describes entropy?",
        "question_type": "MCQ_Single",
        "options_text": '{"A":"First","B":"Second","C":"Third","D":"Zeroth"}',
        "correct_answers": '["B"]',
        "marks": "4",
        "negative_marks": "-1",
    }
    r = requests.post(f"{API}/teacher/question-bank",
                      headers={"Authorization": nitin_headers["Authorization"]},
                      data=data, files=files, timeout=60)
    assert r.status_code == 200, r.text
    q1 = r.json()["question"]
    assert q1["id"]
    assert q1.get("options"), q1
    assert q1.get("question_image_url"), "expected image URL populated"
    ids.append(q1)

    # Numerical_Decimal
    data2 = {
        "topic_id": topic_id,
        "subtopic_id": subtopic_id,
        "question_text": "TEST_ Compute delta G",
        "question_type": "Numerical_Decimal",
        "numerical_answer": "5.75",
        "answer_range": '{"min":5.7,"max":5.8}',
        "marks": "4",
        "negative_marks": "-1",
    }
    r2 = requests.post(f"{API}/teacher/question-bank",
                       headers={"Authorization": nitin_headers["Authorization"]},
                       data=data2, timeout=30)
    assert r2.status_code == 200, r2.text
    q2 = r2.json()["question"]
    assert float(q2["numerical_answer"]) == 5.75
    ids.append(q2)
    return ids


# ---- 5. Public storage URL reachability -------------------------------------
def test_public_image_url_reachable(question_ids):
    url = question_ids[0]["question_image_url"]
    r = requests.get(url, timeout=30)
    assert r.status_code == 200, f"{url} -> {r.status_code}"
    assert r.headers.get("content-type", "").startswith("image/")


# ---- 6. Tree endpoint --------------------------------------------------------
def test_tree_counts(nitin_headers, topic_id, subtopic_id, question_ids):
    r = requests.get(f"{API}/teacher/question-bank/tree", headers=nitin_headers, timeout=30)
    assert r.status_code == 200
    tree = r.json()["tree"]
    t = next((x for x in tree if x["id"] == topic_id), None)
    assert t, "topic missing in tree"
    assert t["question_count"] >= 2
    s = next((x for x in t["subtopics"] if x["id"] == subtopic_id), None)
    assert s and s["question_count"] >= 2


# ---- 7. Per-batch availability + record-assignments -------------------------
def test_available_and_record_assignments(nitin_headers, topic_id, subtopic_id, question_ids):
    q1_id = question_ids[0]["id"]

    def _available(batches):
        params = [("topic_ids", topic_id), ("subtopic_ids", subtopic_id)]
        for b in batches:
            params.append(("batch_codes", b))
        return requests.get(f"{API}/teacher/question-bank/available",
                            headers=nitin_headers, params=params, timeout=30).json()

    a1 = _available(["NEX2027"])
    assert len(a1["questions"]) >= 2
    assert a1["hidden_count"] == 0

    # record Q1 -> NEX2027
    r = requests.post(f"{API}/teacher/question-bank/record-assignments",
                      headers=nitin_headers,
                      json={"question_ids": [q1_id], "batch_codes": ["NEX2027"]}, timeout=30)
    assert r.status_code == 200
    assert r.json()["recorded"] >= 1

    a2 = _available(["NEX2027"])
    q_ids2 = [q["id"] for q in a2["questions"]]
    assert q1_id not in q_ids2, "Q1 should be hidden for NEX2027"
    assert a2["hidden_count"] >= 1

    # NEX2028 unaffected
    a3 = _available(["NEX2028"])
    q_ids3 = [q["id"] for q in a3["questions"]]
    assert q1_id in q_ids3

    # Multi-batch call: fresh_for / used_for arrays
    a4 = _available(["NEX2027", "NEX2028"])
    q1 = next((q for q in a4["questions"] if q["id"] == q1_id), None)
    assert q1, "Q1 should still appear (fresh for NEX2028)"
    assert q1["used_for"] == ["NEX2027"]
    assert q1["fresh_for"] == ["NEX2028"]


# ---- 8. Delete protection ---------------------------------------------------
def test_delete_protection_and_force(nitin_headers, question_ids):
    q1_id = question_ids[0]["id"]
    # already assigned -> 409
    r = requests.delete(f"{API}/teacher/question-bank/{q1_id}", headers=nitin_headers, timeout=30)
    assert r.status_code == 409, r.text
    # force
    r2 = requests.delete(f"{API}/teacher/question-bank/{q1_id}?force=true",
                         headers=nitin_headers, timeout=30)
    assert r2.status_code == 200, r2.text
    # verify gone
    r3 = requests.get(f"{API}/teacher/question-bank/{q1_id}", headers=nitin_headers, timeout=30)
    assert r3.status_code == 404


# ---- 9. Cleanup: delete Q2, subtopic, topic ---------------------------------
def test_cleanup(nitin_headers, question_ids):
    q2_id = question_ids[1]["id"]
    r = requests.delete(f"{API}/teacher/question-bank/{q2_id}?force=true",
                        headers=nitin_headers, timeout=30)
    assert r.status_code == 200
