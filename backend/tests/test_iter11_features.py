"""Iteration 11 — tests for:
  (1) Bookmarks overhaul (snapshot + source + by-question delete + ids)
  (2) Pydantic validation on teacher test + class write endpoints
  (3) Custom Test Builder flow (syllabus -> generate -> fetch -> submit)
Regression: existing teacher test create (legacy CreateTest payload) still works.
"""
import os
import pytest
import requests

def _load_base():
    # Try env, then frontend/.env as fallback
    url = os.environ.get("REACT_APP_BACKEND_URL")
    if not url:
        try:
            with open("/app/frontend/.env") as f:
                for line in f:
                    if line.startswith("REACT_APP_BACKEND_URL="):
                        url = line.split("=", 1)[1].strip()
                        break
        except Exception:
            pass
    if not url:
        raise RuntimeError("REACT_APP_BACKEND_URL not set")
    return url.rstrip("/")


BASE = _load_base()
API = f"{BASE}/api"

STUDENT = {"email": "student@test.com", "password": "password123"}
TEACHER = {"email": "teacher@test.com", "password": "password123"}
SAMPLE_TEST_ID = "ttest_a430b6a6c893"


# ---------- fixtures ----------

def _login(creds):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=creds, timeout=15)
    assert r.status_code == 200, f"Login failed ({creds['email']}): {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def student_session():
    return _login(STUDENT)


@pytest.fixture(scope="module")
def teacher_session():
    return _login(TEACHER)


# ---------- (1) Bookmarks ----------

class TestBookmarksPyq:
    PYQ_QID = "TEST_pyq_iter11_q1"

    def test_cleanup_first(self, student_session):
        # ensure clean slate
        student_session.delete(
            f"{API}/bookmarks/by-question",
            params={"source": "pyq", "question_id": self.PYQ_QID},
            timeout=10,
        )

    def test_create_pyq_bookmark(self, student_session):
        payload = {
            "source": "pyq",
            "question_id": self.PYQ_QID,
            "snapshot": {
                "question_text": "TEST iter11 pyq question",
                "subject": "Physics",
                "chapter": "Kinematics",
                "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
                "correct_answers": ["A"],
            },
        }
        r = student_session.post(f"{API}/bookmarks/", json=payload, timeout=10)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["success"] is True
        bm = data["bookmark"]
        assert bm["source"] == "pyq"
        assert bm["question_id"] == self.PYQ_QID
        assert bm["snapshot"]["question_text"] == "TEST iter11 pyq question"
        assert bm["snapshot"]["subject"] == "Physics"

    def test_duplicate_returns_400(self, student_session):
        r = student_session.post(
            f"{API}/bookmarks/",
            json={"source": "pyq", "question_id": self.PYQ_QID, "snapshot": {"question_text": "x"}},
            timeout=10,
        )
        assert r.status_code == 400
        assert "already" in r.text.lower()

    def test_ids_endpoint_contains_qid(self, student_session):
        r = student_session.get(f"{API}/bookmarks/ids", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "pyq_question_ids" in data and "test_question_keys" in data
        assert self.PYQ_QID in data["pyq_question_ids"]

    def test_list_returns_snapshot(self, student_session):
        r = student_session.get(f"{API}/bookmarks/", timeout=10)
        assert r.status_code == 200
        bms = r.json()["bookmarks"]
        mine = [b for b in bms if b.get("question_id") == self.PYQ_QID]
        assert len(mine) == 1
        assert mine[0]["snapshot"]["question_text"] == "TEST iter11 pyq question"

    def test_delete_by_question(self, student_session):
        r = student_session.delete(
            f"{API}/bookmarks/by-question",
            params={"source": "pyq", "question_id": self.PYQ_QID},
            timeout=10,
        )
        assert r.status_code == 200
        # confirm gone
        r2 = student_session.get(f"{API}/bookmarks/ids", timeout=10)
        assert self.PYQ_QID not in r2.json()["pyq_question_ids"]

    def test_delete_nonexistent_returns_404(self, student_session):
        r = student_session.delete(
            f"{API}/bookmarks/by-question",
            params={"source": "pyq", "question_id": self.PYQ_QID},
            timeout=10,
        )
        assert r.status_code == 404


class TestBookmarksTestAttempt:
    QNUM = 99

    def test_cleanup_first(self, student_session):
        student_session.delete(
            f"{API}/bookmarks/by-question",
            params={"source": "test_attempt", "test_id": SAMPLE_TEST_ID, "question_number": self.QNUM},
            timeout=10,
        )

    def test_create_test_attempt_bookmark(self, student_session):
        payload = {
            "source": "test_attempt",
            "test_id": SAMPLE_TEST_ID,
            "question_number": self.QNUM,
            "snapshot": {
                "question_text": "TEST iter11 attempt q",
                "subject": "Physics",
            },
        }
        r = student_session.post(f"{API}/bookmarks/", json=payload, timeout=10)
        assert r.status_code == 200, r.text
        bm = r.json()["bookmark"]
        assert bm["source"] == "test_attempt"
        assert bm["test_id"] == SAMPLE_TEST_ID
        assert bm["question_number"] == self.QNUM

    def test_ids_endpoint_contains_key(self, student_session):
        r = student_session.get(f"{API}/bookmarks/ids", timeout=10)
        assert r.status_code == 200
        assert f"{SAMPLE_TEST_ID}::{self.QNUM}" in r.json()["test_question_keys"]

    def test_delete_by_question(self, student_session):
        r = student_session.delete(
            f"{API}/bookmarks/by-question",
            params={"source": "test_attempt", "test_id": SAMPLE_TEST_ID, "question_number": self.QNUM},
            timeout=10,
        )
        assert r.status_code == 200


# ---------- (2) Pydantic validation on teacher endpoints ----------

class TestTeacherPydanticValidation:
    def test_create_test_missing_subject_returns_422(self, teacher_session):
        payload = {
            "test_name": "TEST iter11 missing subject",
            "exam_type": "JEE_Main",
            # subject missing
            "scheduled_date_time": "2026-12-01T10:00:00Z",
            "duration": 180,
            "assigned_batches": ["JEE Mains 2027"],
        }
        r = teacher_session.post(f"{API}/teacher/tests/create", json=payload, timeout=10)
        assert r.status_code == 422, r.text
        detail = r.json()["detail"]
        # Pydantic loc should include 'body' and 'subject'
        found = any(
            "subject" in (d.get("loc") or []) for d in detail
        )
        assert found, f"Expected 'subject' in loc: {detail}"

    def test_create_test_invalid_duration_returns_422(self, teacher_session):
        payload = {
            "test_name": "TEST bad duration",
            "exam_type": "JEE_Main",
            "subject": "Physics",
            "scheduled_date_time": "2026-12-01T10:00:00Z",
            "duration": 0,  # invalid, gt=0
            "assigned_batches": ["JEE Mains 2027"],
        }
        r = teacher_session.post(f"{API}/teacher/tests/create", json=payload, timeout=10)
        assert r.status_code == 422, r.text

    def test_create_test_legacy_payload_still_succeeds(self, teacher_session):
        payload = {
            "test_name": "TEST iter11 legacy payload",
            "exam_type": "JEE_Main",
            "test_pattern": "JEE_Main_Pattern",
            "subject": "Physics",
            "test_type": "Full Length",
            "scheduled_date_time": "2026-12-15T10:00:00Z",
            "duration": 180,
            "assigned_batches": ["JEE Mains 2027"],
            "questions": [],
        }
        r = teacher_session.post(f"{API}/teacher/tests/create", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["success"] is True
        created_test_id = data["test"]["test_id"]
        assert data["test"]["subject"] == "Physics"
        assert data["test"]["duration"] == 180
        # cleanup
        teacher_session.delete(f"{API}/teacher/tests/{created_test_id}", timeout=10)

    def test_add_question_missing_text_returns_422(self, teacher_session):
        # First create a draft test to attach a question to
        tcreate = {
            "test_name": "TEST iter11 draft",
            "exam_type": "JEE_Main",
            "subject": "Physics",
            "scheduled_date_time": "2026-12-15T10:00:00Z",
            "duration": 60,
            "assigned_batches": ["JEE Mains 2027"],
            "questions": [],
        }
        cr = teacher_session.post(f"{API}/teacher/tests/create", json=tcreate, timeout=10)
        assert cr.status_code == 200, cr.text
        tid = cr.json()["test"]["test_id"]

        # Bad add-question payload (no question_text)
        bad = {"question_type": "MCQ_Single", "options": {"A": "a"}}
        r = teacher_session.post(f"{API}/teacher/tests/{tid}/add-question", json=bad, timeout=10)
        assert r.status_code == 422, r.text

        # Valid with legacy correct_answer
        good = {
            "question_text": "What is 1+1?",
            "question_type": "MCQ_Single",
            "options": {"A": "1", "B": "2", "C": "3", "D": "4"},
            "correct_answer": "B",
            "marks": 4,
            "negative_marks": -1,
        }
        r2 = teacher_session.post(f"{API}/teacher/tests/{tid}/add-question", json=good, timeout=10)
        assert r2.status_code == 200, r2.text

        teacher_session.delete(f"{API}/teacher/tests/{tid}", timeout=10)

    def test_class_create_missing_required_returns_422(self, teacher_session):
        payload = {"title": "TEST class iter11"}  # missing subject/meeting_link/etc.
        r = teacher_session.post(f"{API}/teacher/classes/create", json=payload, timeout=10)
        assert r.status_code == 422, r.text

    def test_class_create_valid_payload_succeeds(self, teacher_session):
        payload = {
            "title": "TEST iter11 class",
            "subject": "Physics",
            "chapter": "Kinematics",
            "meeting_link": "https://zoom.us/j/123456789",
            "meeting_platform": "Zoom",
            "scheduled_date": "2026-12-25",
            "scheduled_time": "10:00",
            "duration": 60,
            "description": "Test class",
            "assigned_batches": ["JEE Mains 2027"],
        }
        r = teacher_session.post(f"{API}/teacher/classes/create", json=payload, timeout=10)
        assert r.status_code in (200, 201), r.text
        body = r.json()
        # cleanup - find class_id
        cid = (body.get("class") or {}).get("class_id") or body.get("class_id")
        if cid:
            teacher_session.delete(f"{API}/teacher/classes/{cid}", timeout=10)


# ---------- (3) Custom Test Builder ----------

class TestCustomTestBuilder:
    generated_test_id = None

    def test_syllabus(self, student_session):
        r = student_session.get(f"{API}/custom-tests/syllabus", timeout=10)
        assert r.status_code == 200, r.text
        data = r.json()
        for subj in ["Physics", "Chemistry", "Mathematics"]:
            assert subj in data, f"Missing subject {subj} in syllabus: {list(data.keys())}"
            node = data[subj]
            assert "Class11" in node and "Class12" in node
            assert isinstance(node["Class11"], list)
            assert isinstance(node["Class12"], list)

    def test_generate(self, student_session):
        # Pull syllabus to build a selection
        syll = student_session.get(f"{API}/custom-tests/syllabus", timeout=10).json()
        phys_c11 = syll["Physics"]["Class11"]
        chem_c11 = syll["Chemistry"]["Class11"]
        assert phys_c11 and chem_c11, "Syllabus empty — cannot build selection"
        phys_ch = phys_c11[0]["chapter"]
        chem_ch = chem_c11[0]["chapter"]

        payload = {
            "examType": "JEE_Main",
            "yearRange": {"start": 2018, "end": 2024},
            "duration": 60,
            "totalQuestions": 6,
            "totalMarks": 24,
            "selectedTopics": [
                {"subject": "Physics", "chapter": phys_ch, "topic": phys_ch, "questionCount": 3, "difficulty": "Mixed"},
                {"subject": "Chemistry", "chapter": chem_ch, "topic": chem_ch, "questionCount": 3, "difficulty": "Mixed"},
            ],
        }
        r = student_session.post(f"{API}/custom-tests/generate", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        tid = data.get("test_id") or (data.get("test") or {}).get("test_id")
        assert tid, f"No test_id in response: {data}"
        TestCustomTestBuilder.generated_test_id = tid

    def test_get_custom_test_no_correct_answer_leak(self, student_session):
        tid = TestCustomTestBuilder.generated_test_id
        if not tid:
            pytest.skip("generate did not produce a test_id")
        r = student_session.get(f"{API}/custom-tests/{tid}", timeout=10)
        assert r.status_code == 200, r.text
        data = r.json()
        questions = data.get("questions") or (data.get("test") or {}).get("questions") or []
        assert len(questions) > 0, "no questions returned"
        for q in questions:
            assert "correctAnswer" not in q, f"correctAnswer leaked: {q.keys()}"
            assert "correct_answers" not in q, f"correct_answers leaked: {q.keys()}"
            assert "correct_answer" not in q, f"correct_answer leaked: {q.keys()}"

    def test_submit_custom_test(self, student_session):
        tid = TestCustomTestBuilder.generated_test_id
        if not tid:
            pytest.skip("generate did not produce a test_id")
        # Submit with no answers (all skipped) — just check route responds & computes marks
        payload = {"answers": {}, "timeSpent": 120}
        r = student_session.post(f"{API}/custom-tests/{tid}/submit", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        # Should contain some form of marks/score info
        text = str(data).lower()
        assert any(k in text for k in ["marks", "score", "correct", "accuracy"]), f"No scoring fields: {data}"
