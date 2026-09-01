"""Iteration 17 — Zoom live-class end-to-end regression tests (Supabase).

Covers:
- Teacher create/start/end/delete class + owner guards
- Student list (batch scoping) / join (403 non-batch, 400 not-live, 200 live)
- Raise-hand lifecycle (idempotent) + teacher lower-hand
- zoom_start_url must NOT leak in create response
- Regression: auth login for admin/teacher/student
"""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # Fallback to reading frontend/.env directly (tests run in same container)
    from pathlib import Path
    env = Path("/app/frontend/.env").read_text().splitlines()
    for line in env:
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip()
            break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = ("admin@nexuacademy.com", "nexuacademy123")
TEACHER = ("teacher@test.com", "password123")
STUDENT = ("student@test.com", "password123")


# ---------- helpers ----------
def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"login {email} failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


def _h(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def admin_token():
    return _login(*ADMIN)


@pytest.fixture(scope="module")
def teacher_token():
    return _login(*TEACHER)


@pytest.fixture(scope="module")
def student_token():
    return _login(*STUDENT)


@pytest.fixture(scope="module")
def second_teacher_token():
    """Sign up a second teacher on the fly (idempotent-ish; reuse if exists)."""
    email = "teacher2_iter17@nexuacademy.com"
    password = "password123"
    # try login first
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code == 200:
        return r.json()["access_token"]
    # sign up
    r = requests.post(
        f"{API}/auth/signup",
        json={
            "email": email,
            "password": password,
            "name": "Teacher Two Iter17",
            "role": "teacher",
        },
        timeout=30,
    )
    if r.status_code == 200:
        return r.json()["access_token"]
    # Might be registered but signin didn't work – try login again
    r2 = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r2.status_code == 200:
        return r2.json()["access_token"]
    pytest.skip(f"Cannot obtain second teacher token: signup={r.status_code} {r.text[:200]}")


# Track created class ids to guarantee module cleanup even if a test fails
_created_class_ids: list[tuple[str, str]] = []  # (class_id, owner_token)


@pytest.fixture(scope="module", autouse=True)
def _cleanup(admin_token):
    yield
    for cid, _ in _created_class_ids:
        try:
            requests.delete(f"{API}/teacher/live-classes/{cid}", headers=_h(admin_token), timeout=20)
        except Exception:
            pass


def _create_class(token, title_suffix="", batches=None):
    batches = batches or ["JEEM2027"]
    # future date, tomorrow 10:00
    payload = {
        "title": f"TEST_Iter17_LiveClass_{title_suffix or uuid.uuid4().hex[:6]}",
        "subject": "Physics",
        "chapter": "Kinematics",
        "topic": "Projectile Motion",
        "description": "Zoom E2E test",
        "scheduled_date": "2027-01-15",
        "scheduled_time": "10:00",
        "duration": 60,
        "assigned_batches": batches,
    }
    r = requests.post(f"{API}/teacher/live-classes/create", headers=_h(token), json=payload, timeout=60)
    return r


# ---------- auth regression ----------
class TestAuth:
    def test_admin_login(self, admin_token):
        assert admin_token and len(admin_token) > 20

    def test_teacher_login(self, teacher_token):
        assert teacher_token and len(teacher_token) > 20

    def test_student_login(self, student_token):
        assert student_token and len(student_token) > 20


# ---------- teacher create ----------
class TestTeacherCreate:
    def test_create_live_class_returns_zoom_fields_no_start_url(self, teacher_token):
        r = _create_class(teacher_token, "create")
        assert r.status_code == 200, f"create failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body.get("success") is True
        cls = body["class"]
        assert cls.get("class_id")
        assert cls.get("zoom_meeting_id"), "zoom_meeting_id missing"
        assert "zoom_meeting_password" in cls
        assert cls.get("zoom_join_url", "").startswith("http") or cls.get("meeting_link", "").startswith("http")
        # zoom_start_url must NOT leak
        assert "zoom_start_url" not in cls, "zoom_start_url MUST NOT be exposed to client"
        assert cls.get("is_live") in (False, None)
        _created_class_ids.append((cls["class_id"], teacher_token))

    def test_create_no_batches_400(self, teacher_token):
        payload = {
            "title": "TEST_no_batch",
            "subject": "Physics",
            "scheduled_date": "2027-01-15",
            "scheduled_time": "10:00",
            "duration": 60,
            "assigned_batches": [],
        }
        r = requests.post(f"{API}/teacher/live-classes/create", headers=_h(teacher_token), json=payload, timeout=30)
        assert r.status_code == 400

    def test_create_invalid_date_400(self, teacher_token):
        payload = {
            "title": "TEST_bad_date",
            "subject": "Physics",
            "scheduled_date": "not-a-date",
            "scheduled_time": "10:00",
            "duration": 60,
            "assigned_batches": ["JEEM2027"],
        }
        r = requests.post(f"{API}/teacher/live-classes/create", headers=_h(teacher_token), json=payload, timeout=30)
        assert r.status_code == 400

    def test_student_cannot_create(self, student_token):
        r = _create_class(student_token, "student_forbid")
        assert r.status_code == 403


# ---------- teacher start / owner guard / signature ----------
class TestTeacherStart:
    @pytest.fixture(scope="class")
    def class_id(self, teacher_token):
        r = _create_class(teacher_token, "start")
        assert r.status_code == 200
        cid = r.json()["class"]["class_id"]
        _created_class_ids.append((cid, teacher_token))
        return cid

    def test_non_owner_teacher_403(self, class_id, second_teacher_token):
        r = requests.post(f"{API}/teacher/live-classes/{class_id}/start", headers=_h(second_teacher_token), timeout=30)
        assert r.status_code == 403, f"expected 403, got {r.status_code} {r.text[:200]}"

    def test_owner_can_start(self, class_id, teacher_token):
        r = requests.post(f"{API}/teacher/live-classes/{class_id}/start", headers=_h(teacher_token), timeout=45)
        assert r.status_code == 200, f"start failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body.get("success") is True
        assert body.get("signature") and len(body["signature"]) > 40, "SDK signature missing"
        assert body.get("sdk_key"), "sdk_key missing"
        assert body.get("meeting_number"), "meeting_number missing"
        # zak may be None if scope missing — best-effort
        assert "zak" in body

    def test_start_404_for_bogus_id(self, teacher_token):
        r = requests.post(f"{API}/teacher/live-classes/does-not-exist/start", headers=_h(teacher_token), timeout=30)
        assert r.status_code == 404


# ---------- student list + join ----------
class TestStudentJoin:
    @pytest.fixture(scope="class")
    def live_class_id(self, teacher_token):
        """Create + start a class that student's batch (JEEM2027) can access."""
        r = _create_class(teacher_token, "student_join", batches=["JEEM2027"])
        assert r.status_code == 200
        cid = r.json()["class"]["class_id"]
        _created_class_ids.append((cid, teacher_token))
        return cid

    @pytest.fixture(scope="class")
    def foreign_class_id(self, teacher_token):
        """Class NOT in student's batch — student must get 403."""
        r = _create_class(teacher_token, "foreign", batches=["NEX2028"])
        assert r.status_code == 200
        cid = r.json()["class"]["class_id"]
        _created_class_ids.append((cid, teacher_token))
        return cid

    def test_student_list_returns_only_own_batch(self, student_token, live_class_id, foreign_class_id):
        r = requests.get(f"{API}/student/live-classes/", headers=_h(student_token), timeout=30)
        assert r.status_code == 200
        classes = r.json().get("classes", [])
        ids = {c["class_id"] for c in classes}
        assert live_class_id in ids, "student's batch class missing from list"
        assert foreign_class_id not in ids, "foreign-batch class MUST NOT appear in student list"
        for c in classes:
            assert c.get("status") != "cancelled"

    def test_join_before_live_returns_400(self, student_token, live_class_id):
        r = requests.get(f"{API}/student/live-classes/{live_class_id}/join", headers=_h(student_token), timeout=30)
        assert r.status_code == 400, f"expected 400 not-live, got {r.status_code} {r.text[:200]}"

    def test_join_foreign_batch_returns_403(self, student_token, foreign_class_id):
        r = requests.get(f"{API}/student/live-classes/{foreign_class_id}/join", headers=_h(student_token), timeout=30)
        assert r.status_code == 403

    def test_join_after_start_returns_signature(self, teacher_token, student_token, live_class_id):
        # Start the class as teacher
        s = requests.post(f"{API}/teacher/live-classes/{live_class_id}/start", headers=_h(teacher_token), timeout=45)
        assert s.status_code == 200
        # Now join as student
        r = requests.get(f"{API}/student/live-classes/{live_class_id}/join", headers=_h(student_token), timeout=30)
        assert r.status_code == 200, f"student join failed: {r.status_code} {r.text[:200]}"
        body = r.json()
        assert body.get("signature") and len(body["signature"]) > 40
        assert body.get("sdk_key")
        assert body.get("meeting_number")
        assert "password" in body
        assert body.get("user_name")


# ---------- raise-hand lifecycle ----------
class TestRaiseHand:
    @pytest.fixture(scope="class")
    def live_class_id(self, teacher_token):
        r = _create_class(teacher_token, "raisehand", batches=["JEEM2027"])
        assert r.status_code == 200
        cid = r.json()["class"]["class_id"]
        _created_class_ids.append((cid, teacher_token))
        # start it
        s = requests.post(f"{API}/teacher/live-classes/{cid}/start", headers=_h(teacher_token), timeout=45)
        assert s.status_code == 200
        return cid

    def test_raise_and_visible_to_teacher(self, teacher_token, student_token, live_class_id):
        r = requests.post(f"{API}/student/live-classes/{live_class_id}/raise-hand",
                          headers=_h(student_token), timeout=30)
        assert r.status_code == 200
        # Idempotent second call
        r2 = requests.post(f"{API}/student/live-classes/{live_class_id}/raise-hand",
                           headers=_h(student_token), timeout=30)
        assert r2.status_code == 200

        # Teacher lists participants → raised_hands has exactly 1 row for this student
        p = requests.get(f"{API}/teacher/live-classes/{live_class_id}/participants",
                         headers=_h(teacher_token), timeout=30)
        assert p.status_code == 200, f"participants: {p.status_code} {p.text[:200]}"
        body = p.json()
        assert body.get("is_live") is True
        raised = body.get("raised_hands", [])
        student_rows = [r for r in raised if "student" in (r.get("student_name") or "").lower()
                        or r.get("student_id")]
        # At least 1 raised hand present (this student)
        assert len(raised) >= 1
        # No duplicate for same student (idempotency)
        ids = [r["student_id"] for r in raised]
        assert len(ids) == len(set(ids)), f"duplicate raised_hands: {ids}"

    def test_teacher_lower_hand_removes_row(self, teacher_token, student_token, live_class_id):
        # get student id from raised hands
        p = requests.get(f"{API}/teacher/live-classes/{live_class_id}/participants",
                         headers=_h(teacher_token), timeout=30)
        raised = p.json().get("raised_hands", [])
        assert raised, "no raised hand to lower"
        student_id = raised[0]["student_id"]

        r = requests.post(f"{API}/teacher/live-classes/{live_class_id}/lower-hand/{student_id}",
                          headers=_h(teacher_token), timeout=30)
        assert r.status_code == 200

        p2 = requests.get(f"{API}/teacher/live-classes/{live_class_id}/participants",
                          headers=_h(teacher_token), timeout=30)
        raised2 = p2.json().get("raised_hands", [])
        assert student_id not in [r["student_id"] for r in raised2]


# ---------- end class ----------
class TestEndClass:
    def test_end_flips_is_live_and_clears_raised(self, teacher_token, student_token):
        # Create + start + raise-hand + end
        c = _create_class(teacher_token, "end", batches=["JEEM2027"])
        assert c.status_code == 200
        cid = c.json()["class"]["class_id"]
        _created_class_ids.append((cid, teacher_token))

        s = requests.post(f"{API}/teacher/live-classes/{cid}/start", headers=_h(teacher_token), timeout=45)
        assert s.status_code == 200

        rh = requests.post(f"{API}/student/live-classes/{cid}/raise-hand",
                           headers=_h(student_token), timeout=30)
        assert rh.status_code == 200

        e = requests.post(f"{API}/teacher/live-classes/{cid}/end", headers=_h(teacher_token), timeout=30)
        assert e.status_code == 200

        # participants: is_live=False, raised_hands=[]
        p = requests.get(f"{API}/teacher/live-classes/{cid}/participants",
                         headers=_h(teacher_token), timeout=30)
        assert p.status_code == 200
        body = p.json()
        assert body.get("is_live") is False
        assert body.get("raised_hands") == []


# ---------- delete class + owner guard ----------
class TestDeleteClass:
    def test_non_owner_teacher_403(self, teacher_token, second_teacher_token):
        c = _create_class(teacher_token, "del_owner")
        assert c.status_code == 200
        cid = c.json()["class"]["class_id"]
        _created_class_ids.append((cid, teacher_token))

        r = requests.delete(f"{API}/teacher/live-classes/{cid}",
                            headers=_h(second_teacher_token), timeout=30)
        assert r.status_code == 403

    def test_owner_can_delete(self, teacher_token):
        c = _create_class(teacher_token, "del_ok")
        assert c.status_code == 200
        cid = c.json()["class"]["class_id"]
        r = requests.delete(f"{API}/teacher/live-classes/{cid}",
                            headers=_h(teacher_token), timeout=30)
        assert r.status_code == 200
        # confirm deletion
        p = requests.get(f"{API}/teacher/live-classes/{cid}/participants",
                         headers=_h(teacher_token), timeout=30)
        assert p.status_code == 404

    def test_admin_can_delete_others_class(self, teacher_token, admin_token):
        c = _create_class(teacher_token, "del_admin")
        assert c.status_code == 200
        cid = c.json()["class"]["class_id"]
        r = requests.delete(f"{API}/teacher/live-classes/{cid}",
                            headers=_h(admin_token), timeout=30)
        assert r.status_code == 200
