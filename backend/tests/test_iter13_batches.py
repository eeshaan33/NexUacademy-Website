"""
Iteration 13 — Backend tests for batches, admission flow with batch_code, profile,
teacher class scheduling notifications, students-by-batch, assigned tests.
"""
import os
import uuid
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@nexuacademy.com", "password": "nexuacademy123"}
TEACHER = {"email": "teacher@test.com", "password": "password123"}
STUDENT = {"email": "student@test.com", "password": "password123"}


def _login_session(creds):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=creds, timeout=20)
    assert r.status_code == 200, f"Login failed {creds['email']}: {r.status_code} {r.text}"
    body = r.json()
    token = body.get("token") or body.get("access_token")
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    return s


@pytest.fixture(scope="module")
def admin_session():
    return _login_session(ADMIN)


@pytest.fixture(scope="module")
def teacher_session():
    return _login_session(TEACHER)


@pytest.fixture(scope="module")
def student_session():
    return _login_session(STUDENT)


# ---------- batches ----------
class TestBatches:
    def test_get_batches_list_with_codes(self):
        r = requests.get(f"{API}/batches/", timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        codes = {b.get("code") for b in body["batches"]}
        for c in ["JEEM2027", "JEEM2028", "JEEM2029", "JEEA2027", "JEEA2028"]:
            assert c in codes, f"missing predefined code {c}; got {codes}"

    def test_get_batch_by_code_valid(self):
        r = requests.get(f"{API}/batches/by-code/JEEM2027", timeout=15)
        assert r.status_code == 200
        b = r.json()["batch"]
        assert b["code"] == "JEEM2027"

    def test_get_batch_by_code_invalid(self):
        r = requests.get(f"{API}/batches/by-code/NOPECODE", timeout=15)
        assert r.status_code == 404

    def test_create_batch_admin_auto_code(self, admin_session):
        name = f"TEST_Batch_{uuid.uuid4().hex[:6]}"
        r = admin_session.post(f"{API}/batches/", json={"name": name, "year": 2027}, timeout=15)
        assert r.status_code == 200, r.text
        b = r.json()["batch"]
        assert b["code"] and b["code"].isalnum()
        admin_session.delete(f"{API}/batches/{name}", timeout=15)

    def test_create_batch_admin_custom_code(self, admin_session):
        name = f"TEST_Batch_{uuid.uuid4().hex[:6]}"
        custom = f"TST{uuid.uuid4().hex[:5].upper()}"
        r = admin_session.post(
            f"{API}/batches/", json={"name": name, "year": 2027, "code": custom}, timeout=15
        )
        assert r.status_code == 200
        assert r.json()["batch"]["code"] == custom
        admin_session.delete(f"{API}/batches/{name}", timeout=15)

    def test_create_batch_rejects_non_alphanumeric(self, admin_session):
        name = f"TEST_Batch_{uuid.uuid4().hex[:6]}"
        r = admin_session.post(
            f"{API}/batches/",
            json={"name": name, "year": 2027, "code": "BAD-CODE!"},
            timeout=15,
        )
        assert r.status_code == 400

    def test_create_batch_rejects_duplicate_code(self, admin_session):
        name = f"TEST_Batch_{uuid.uuid4().hex[:6]}"
        r = admin_session.post(
            f"{API}/batches/", json={"name": name, "year": 2027, "code": "JEEM2027"}, timeout=15
        )
        assert r.status_code == 400

    def test_predefined_batch_cannot_be_deleted(self, admin_session):
        r = admin_session.delete(f"{API}/batches/JEE Mains 2027", timeout=15)
        assert r.status_code == 400

    def test_create_batch_unauthenticated(self):
        r = requests.post(f"{API}/batches/", json={"name": "X", "year": 2027}, timeout=15)
        assert r.status_code in (401, 403)


# ---------- admission flow ----------
class TestAdmission:
    def test_full_admission_with_valid_batch_code(self):
        unique = uuid.uuid4().hex[:8]
        email = f"newstudent_{unique}@test.com"
        payload = {
            "student_name": f"TEST_Student_{unique}",
            "father_name": "TEST_Father",
            "mother_name": "TEST_Mother",
            "date_of_birth": "2008-05-15",
            "gender": "Male",
            "contact_number": "9999999999",
            "email": email,
            "password": "password123",
            "address": "123 Test Lane",
            "city": "TestCity",
            "state": "TS",
            "pincode": "560001",
            "course_applying": "JEE Mains 2027",
            "batch_code": "JEEM2027",
        }
        r = requests.post(f"{API}/admissions/submit", json=payload, timeout=25)
        assert r.status_code == 200, r.text
        u = r.json()["user"]
        assert u["roll_number"].startswith("NXU-")
        assert u["batch_id"] == "JEE Mains 2027"

    def test_admission_invalid_batch_code(self):
        unique = uuid.uuid4().hex[:8]
        payload = {
            "student_name": "TEST_Bad",
            "father_name": "F",
            "mother_name": "M",
            "date_of_birth": "2008-05-15",
            "gender": "Male",
            "contact_number": "9999999999",
            "email": f"bad_{unique}@test.com",
            "password": "password123",
            "address": "x",
            "city": "x",
            "state": "x",
            "pincode": "560001",
            "course_applying": "JEE Mains 2027",
            "batch_code": "NOPE12345",
        }
        r = requests.post(f"{API}/admissions/submit", json=payload, timeout=20)
        assert r.status_code == 400


# ---------- profile ----------
class TestProfileMe:
    def test_student_me_returns_profile(self, student_session):
        r = student_session.get(f"{API}/admissions/me", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        u = body["user"]
        assert u["email"] == STUDENT["email"]
        assert u.get("batch_id"), "expected backfilled batch_id"
        assert u.get("roll_number"), "expected backfilled roll_number"
        assert u["roll_number"].startswith("NXU-")

    def test_teacher_me_forbidden(self, teacher_session):
        r = teacher_session.get(f"{API}/admissions/me", timeout=15)
        assert r.status_code == 403


# ---------- teacher students by batch ----------
class TestTeacherStudents:
    def test_all_students_endpoint(self, teacher_session):
        r = teacher_session.get(f"{API}/teacher/students", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        students = body.get("students", body) if isinstance(body, dict) else body
        assert isinstance(students, list)
        assert len(students) > 0

    def test_filter_students_by_batch(self, teacher_session):
        r = teacher_session.get(
            f"{API}/teacher/students", params={"batch": "JEE Mains 2027"}, timeout=15
        )
        assert r.status_code == 200
        body = r.json()
        students = body.get("students", body) if isinstance(body, dict) else body
        assert len(students) > 0, "Expected >0 students in JEE Mains 2027 after backfill"


# ---------- teacher creates class -> notifies students ----------
class TestClassScheduleNotify:
    @pytest.fixture(scope="class")
    def created_class(self, teacher_session):
        unique = uuid.uuid4().hex[:6]
        payload = {
            "title": f"TEST_NotifyClass_{unique}",
            "subject": "Physics",
            "meeting_link": "https://meet.example.com/test",
            "scheduled_date": "2026-08-12",
            "scheduled_time": "10:00",
            "duration": 60,
            "assigned_batches": ["JEE Mains 2027"],
            "description": "iter13 test class",
        }
        r = teacher_session.post(f"{API}/teacher/classes/create", json=payload, timeout=25)
        assert r.status_code == 200, r.text
        return {"unique": unique, "body": r.json(), "payload": payload}

    def test_response_contains_notified_count(self, created_class):
        body = created_class["body"]
        msg = (body.get("message") or "").lower()
        notified = (
            body.get("students_notified")
            or body.get("notified_count")
            or body.get("notified")
            or 0
        )
        assert (isinstance(notified, int) and notified > 0) or "notif" in msg, (
            f"Expected notified>0; body={body}"
        )

    def test_student_sees_notification(self, created_class, student_session):
        time.sleep(1)
        r = student_session.get(f"{API}/notifications/", timeout=15)
        if r.status_code == 404:
            r = student_session.get(f"{API}/notifications", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        notifs = body.get("notifications") if isinstance(body, dict) else body
        assert isinstance(notifs, list)
        unique = created_class["unique"]
        found = any(
            unique in (n.get("title", "") + " " + n.get("message", ""))
            for n in notifs[:50]
        )
        assert found, f"new class notification not found. First 3: {notifs[:3]}"

    def test_student_my_classes_includes_new(self, created_class, student_session):
        r = student_session.get(f"{API}/student/classes/my-classes", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        classes = body.get("classes") if isinstance(body, dict) else body
        assert isinstance(classes, list)
        unique = created_class["unique"]
        found = any(unique in (c.get("title", "")) for c in classes)
        assert found, "Newly created class not visible in student my-classes"


# ---------- student assigned tests ----------
class TestStudentAssigned:
    def test_assigned_tests_endpoint(self, student_session):
        r = student_session.get(f"{API}/student/tests/assigned", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        tests = body.get("tests") if isinstance(body, dict) else body
        assert isinstance(tests, list)
