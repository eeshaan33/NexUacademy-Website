"""End-to-end backend tests for the Supabase migration (iteration 14).

Covers: Auth, Batches, Admissions, Classes, Live Classes (Zoom), Tests, Announcements,
Notifications, Questions (option-images), Upload.

Environment: uses REACT_APP_BACKEND_URL. Seed users created by backend startup:
- admin@nexuacademy.com / nexuacademy123
- teacher@test.com / password123
- student@test.com / password123 (batch JEEM2027)
"""
import io
import os
import time
import uuid

import pytest
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@nexuacademy.com", "password": "nexuacademy123"}
TEACHER = {"email": "teacher@test.com", "password": "password123"}
STUDENT = {"email": "student@test.com", "password": "password123"}

# Shared state across tests
STATE = {}


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"login failed for {email}: {r.status_code} {r.text}"
    d = r.json()
    return d["access_token"], d["user"]


def _h(token):
    return {"Authorization": f"Bearer {token}"}


# ----------------- AUTH -----------------
class TestAuth:
    def test_admin_login(self):
        tok, u = _login(**ADMIN)
        STATE["admin_token"] = tok
        STATE["admin_user"] = u
        assert u["role"] == "admin"
        assert isinstance(tok, str) and len(tok) > 20

    def test_teacher_login(self):
        tok, u = _login(**TEACHER)
        STATE["teacher_token"] = tok
        STATE["teacher_user"] = u
        assert u["role"] == "teacher"

    def test_student_login(self):
        tok, u = _login(**STUDENT)
        STATE["student_token"] = tok
        STATE["student_user"] = u
        assert u["role"] == "student"
        assert u.get("batch_id") == "JEEM2027", f"expected batch JEEM2027, got {u.get('batch_id')}"

    def test_bad_password_returns_401(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN["email"], "password": "wrong"})
        assert r.status_code == 401
        assert "Invalid" in r.json().get("detail", "")

    def test_me_endpoint(self):
        r = requests.get(f"{API}/auth/me", headers=_h(STATE["student_token"]))
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["user"]["email"] == STUDENT["email"]
        assert d["user"]["role"] == "student"

    def test_google_url(self):
        r = requests.get(f"{API}/auth/google/url")
        assert r.status_code == 200
        d = r.json()
        assert "supabase.co/auth/v1/authorize?provider=google" in d["url"]


# ----------------- BATCHES -----------------
class TestBatches:
    def test_public_list_has_three_predefined(self):
        r = requests.get(f"{API}/batches/")
        assert r.status_code == 200
        codes = {b["code"] for b in r.json()["batches"]}
        for c in ("JEEM2027", "NEX2027", "NEX2028"):
            assert c in codes, f"missing predefined batch {c}"

    def test_by_code_ok(self):
        r = requests.get(f"{API}/batches/by-code/JEEM2027")
        assert r.status_code == 200
        assert r.json()["batch"]["code"] == "JEEM2027"

    def test_by_code_not_found(self):
        r = requests.get(f"{API}/batches/by-code/WRONGXYZ")
        assert r.status_code == 404
        assert "not recognised" in r.json()["detail"].lower()

    def test_admin_create_and_delete_custom_batch(self):
        code = f"TEST{uuid.uuid4().hex[:6].upper()}"
        r = requests.post(
            f"{API}/batches/",
            json={"name": f"TestBatch {code}", "year": 2027, "code": code},
            headers=_h(STATE["admin_token"]),
        )
        assert r.status_code == 200, r.text
        assert r.json()["batch"]["code"] == code
        # Duplicate
        r2 = requests.post(
            f"{API}/batches/",
            json={"name": f"TestBatch {code} v2", "year": 2027, "code": code},
            headers=_h(STATE["admin_token"]),
        )
        assert r2.status_code == 400
        # Non-alphanumeric
        r3 = requests.post(
            f"{API}/batches/",
            json={"name": f"TestBad{uuid.uuid4().hex[:4]}", "year": 2027, "code": "BAD-CODE"},
            headers=_h(STATE["admin_token"]),
        )
        assert r3.status_code == 400
        # Delete
        rd = requests.delete(f"{API}/batches/{code}", headers=_h(STATE["admin_token"]))
        assert rd.status_code == 200

    def test_cannot_delete_predefined(self):
        r = requests.delete(f"{API}/batches/JEEM2027", headers=_h(STATE["admin_token"]))
        assert r.status_code == 400


# ----------------- ADMISSIONS -----------------
class TestAdmissions:
    def test_admission_invalid_batch(self):
        payload = _mk_admission_payload(batch_code="WRONGXYZ")
        r = requests.post(f"{API}/admissions/submit", json=payload)
        assert r.status_code == 400
        assert "not recognised" in r.json()["detail"].lower()

    def test_admission_creates_user_and_roll(self):
        payload = _mk_admission_payload(batch_code="JEEM2027")
        r = requests.post(f"{API}/admissions/submit", json=payload)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["user"]["roll_number"].startswith("NXU-")
        assert d["user"]["batch_id"] == "JEEM2027"
        assert d.get("access_token")
        STATE["new_student_token"] = d["access_token"]
        STATE["new_student_email"] = payload["email"]

    def test_admission_me(self):
        r = requests.get(f"{API}/admissions/me", headers=_h(STATE["new_student_token"]))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["admission"]["batch_id"] == "JEEM2027"
        assert d["batch"]["code"] == "JEEM2027"


def _mk_admission_payload(batch_code):
    uniq = uuid.uuid4().hex[:8]
    return {
        "student_name": f"TEST Student {uniq}",
        "father_name": "TF",
        "mother_name": "TM",
        "date_of_birth": "2008-01-01",
        "gender": "male",
        "contact_number": "9999999999",
        "email": f"TEST_{uniq}@example.com",
        "password": "TestPass123!",
        "address": "1 Test Rd",
        "city": "Delhi",
        "state": "DL",
        "pincode": "110001",
        "course_applying": "JEE Mains",
        "batch_code": batch_code,
    }


# ----------------- CLASSES + BATCH ISOLATION -----------------
class TestClassesAndTests:
    def test_teacher_creates_class_for_jeem2027(self):
        r = requests.post(
            f"{API}/teacher/classes/create",
            json={
                "title": "TEST Physics Kinematics",
                "subject": "Physics",
                "scheduled_date": "2027-01-01",
                "scheduled_time": "10:00",
                "duration": 60,
                "assigned_batches": ["JEEM2027"],
            },
            headers=_h(STATE["teacher_token"]),
        )
        assert r.status_code == 200, r.text
        cls = r.json()["class"]
        STATE["class_id"] = cls["class_id"]
        assert "JEEM2027" in cls["assigned_batches"]

    def test_jeem2027_student_sees_class(self):
        r = requests.get(f"{API}/student/classes/my-classes", headers=_h(STATE["student_token"]))
        assert r.status_code == 200
        ids = [c["class_id"] for c in r.json()["classes"]]
        assert STATE["class_id"] in ids

    def test_teacher_creates_test_for_jeem2027(self):
        r = requests.post(
            f"{API}/teacher/tests/create",
            json={
                "test_name": "TEST JEE Physics Q1",
                "subject": "Physics",
                "duration": 30,
                "total_questions": 1,
                "total_marks": 4,
                "assigned_batches": ["JEEM2027"],
                "questions": [{"q": "1+1?", "answer": "2"}],
            },
            headers=_h(STATE["teacher_token"]),
        )
        assert r.status_code == 200, r.text
        STATE["test_id"] = r.json()["test"]["test_id"]

    def test_student_sees_assigned_test(self):
        r = requests.get(f"{API}/student/tests/assigned", headers=_h(STATE["student_token"]))
        assert r.status_code == 200
        ids = [t["test_id"] for t in r.json()["tests"]]
        assert STATE["test_id"] in ids

    def test_start_attempt_and_resume_same(self):
        r1 = requests.post(f"{API}/student/tests/{STATE['test_id']}/start",
                           headers=_h(STATE["student_token"]))
        assert r1.status_code == 200, r1.text
        att1 = r1.json()["attempt"]["attempt_id"]
        r2 = requests.post(f"{API}/student/tests/{STATE['test_id']}/start",
                           headers=_h(STATE["student_token"]))
        assert r2.status_code == 200
        assert r2.json()["attempt"]["attempt_id"] == att1
        assert r2.json()["resumed"] is True

    def test_nex2028_student_isolation(self):
        # Create a fresh student via admissions in NEX2028 and verify isolation
        payload = _mk_admission_payload(batch_code="NEX2028")
        r = requests.post(f"{API}/admissions/submit", json=payload)
        assert r.status_code == 200, r.text
        tok = r.json()["access_token"]
        STATE["nex_student_token"] = tok
        rc = requests.get(f"{API}/student/classes/my-classes", headers=_h(tok))
        assert rc.status_code == 200
        assert STATE["class_id"] not in [c["class_id"] for c in rc.json()["classes"]]
        rt = requests.get(f"{API}/student/tests/assigned", headers=_h(tok))
        assert rt.status_code == 200
        assert STATE["test_id"] not in [t["test_id"] for t in rt.json()["tests"]]


# ----------------- LIVE CLASSES (Zoom) -----------------
class TestLiveClasses:
    def test_teacher_creates_zoom_class(self):
        r = requests.post(
            f"{API}/teacher/live-classes/create",
            json={
                "title": "TEST Live Chemistry",
                "subject": "Chemistry",
                "scheduled_date": "2027-02-01",
                "scheduled_time": "11:00",
                "duration": 30,
                "assigned_batches": ["JEEM2027"],
            },
            headers=_h(STATE["teacher_token"]),
            timeout=60,
        )
        if r.status_code == 502:
            pytest.skip(f"Zoom API unavailable: {r.text}")
        assert r.status_code == 200, r.text
        cls = r.json()["class"]
        assert cls.get("zoom_meeting_id")
        STATE["live_class_id"] = cls["class_id"]

    def test_student_join_fails_when_not_live(self):
        if "live_class_id" not in STATE:
            pytest.skip("no live class")
        r = requests.get(f"{API}/student/live-classes/{STATE['live_class_id']}/join",
                         headers=_h(STATE["student_token"]))
        assert r.status_code == 400
        assert "not started" in r.json()["detail"].lower() or "wait" in r.json()["detail"].lower()

    def test_teacher_start_returns_signature(self):
        if "live_class_id" not in STATE:
            pytest.skip("no live class")
        r = requests.post(f"{API}/teacher/live-classes/{STATE['live_class_id']}/start",
                          headers=_h(STATE["teacher_token"]), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("signature") and d.get("sdk_key") and d.get("meeting_number")

    def test_student_join_returns_signature(self):
        if "live_class_id" not in STATE:
            pytest.skip("no live class")
        r = requests.get(f"{API}/student/live-classes/{STATE['live_class_id']}/join",
                         headers=_h(STATE["student_token"]))
        assert r.status_code == 200, r.text
        assert r.json().get("signature")

    def test_raise_and_lower_hand(self):
        if "live_class_id" not in STATE:
            pytest.skip("no live class")
        cid = STATE["live_class_id"]
        r = requests.post(f"{API}/student/live-classes/{cid}/raise-hand",
                          headers=_h(STATE["student_token"]))
        assert r.status_code == 200
        # teacher sees it
        rp = requests.get(f"{API}/teacher/live-classes/{cid}/participants",
                          headers=_h(STATE["teacher_token"]))
        assert rp.status_code == 200
        raised = rp.json()["raised_hands"]
        assert any(h["student_id"] == str(STATE["student_user"]["user_id"]) for h in raised)
        # teacher lowers
        sid = STATE["student_user"]["user_id"]
        rl = requests.post(f"{API}/teacher/live-classes/{cid}/lower-hand/{sid}",
                           headers=_h(STATE["teacher_token"]))
        assert rl.status_code == 200
        rp2 = requests.get(f"{API}/teacher/live-classes/{cid}/participants",
                           headers=_h(STATE["teacher_token"]))
        assert not any(h["student_id"] == str(sid) for h in rp2.json()["raised_hands"])

    def test_zzz_cleanup_live_class(self):
        if "live_class_id" not in STATE:
            pytest.skip("no live class")
        r = requests.delete(f"{API}/teacher/live-classes/{STATE['live_class_id']}",
                            headers=_h(STATE["teacher_token"]))
        assert r.status_code == 200


# ----------------- ANNOUNCEMENTS -----------------
class TestAnnouncements:
    def test_teacher_creates_announcement(self):
        r = requests.post(
            f"{API}/announcements/",
            json={
                "title": "TEST Announcement",
                "message": "Test message content",
                "assigned_batches": ["JEEM2027"],
                "is_pinned": True,
            },
            headers=_h(STATE["teacher_token"]),
        )
        assert r.status_code == 200, r.text
        d = r.json()["announcement"]
        STATE["ann_id"] = d["announcement_id"]
        assert d["is_pinned"] is True

    def test_jeem_student_sees_announcement(self):
        r = requests.get(f"{API}/announcements/", headers=_h(STATE["student_token"]))
        assert r.status_code == 200
        ids = [a["announcement_id"] for a in r.json()["announcements"]]
        assert STATE["ann_id"] in ids

    def test_nex_student_does_not_see(self):
        if "nex_student_token" not in STATE:
            pytest.skip("no nex student")
        r = requests.get(f"{API}/announcements/", headers=_h(STATE["nex_student_token"]))
        assert r.status_code == 200
        ids = [a["announcement_id"] for a in r.json()["announcements"]]
        assert STATE["ann_id"] not in ids

    def test_delete_announcement(self):
        r = requests.delete(f"{API}/announcements/{STATE['ann_id']}",
                            headers=_h(STATE["teacher_token"]))
        assert r.status_code == 200


# ----------------- NOTIFICATIONS -----------------
class TestNotifications:
    def test_student_has_notifications(self):
        r = requests.get(f"{API}/notifications/", headers=_h(STATE["student_token"]))
        assert r.status_code == 200
        d = r.json()
        # After class + test + announcement, expect >=1 unread
        assert d["unread_count"] >= 1, f"expected unread>0, got {d['unread_count']}"
        STATE["notif_ids"] = [n["notification_id"] for n in d["notifications"] if not n["is_read"]]

    def test_mark_single_read(self):
        if not STATE.get("notif_ids"):
            pytest.skip("no notifs")
        nid = STATE["notif_ids"][0]
        r = requests.post(f"{API}/notifications/{nid}/read", headers=_h(STATE["student_token"]))
        assert r.status_code == 200

    def test_mark_all_read(self):
        r = requests.post(f"{API}/notifications/mark-all-read", headers=_h(STATE["student_token"]))
        assert r.status_code == 200
        r2 = requests.get(f"{API}/notifications/", headers=_h(STATE["student_token"]))
        assert r2.json()["unread_count"] == 0


# ----------------- QUESTIONS (Part 6 option-images) -----------------
class TestQuestions:
    def test_create_question_with_option_image(self):
        payload = {
            "subject": "Physics",
            "chapter": "Kinematics",
            "question_text": "Which diagram represents projectile?",
            "options": {
                "A": {"text": "Text only option"},
                "B": {"text": "With image", "imageUrl": "https://example.com/img.png"},
                "C": {"text": "Third"},
                "D": {"text": "Fourth"},
            },
            "correct_answers": ["B"],
            "is_sample": True,
        }
        r = requests.post(f"{API}/questions/single", json=payload,
                          headers=_h(STATE["admin_token"]))
        assert r.status_code == 200, r.text
        q = r.json()["question"]
        # Options should be jsonb with imageUrl preserved
        opts = q["options"] if isinstance(q["options"], dict) else __import__("json").loads(q["options"])
        assert opts["B"].get("imageUrl") == "https://example.com/img.png"
        assert opts["A"].get("text") == "Text only option"
        STATE["question_id"] = q["question_id"]

    def test_samples_lists_it(self):
        r = requests.get(f"{API}/questions/samples")
        assert r.status_code == 200
        ids = [q["question_id"] for q in r.json()["questions"]]
        assert STATE.get("question_id") in ids

    def test_zzz_cleanup_question(self):
        if "question_id" in STATE:
            r = requests.delete(f"{API}/questions/{STATE['question_id']}",
                                headers=_h(STATE["admin_token"]))
            assert r.status_code == 200


# ----------------- UPLOAD -----------------
class TestUpload:
    def test_upload_image_returns_public_url(self):
        # Minimal 1x1 PNG
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08"
            b"\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00"
            b"\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        files = {"file": ("test.png", io.BytesIO(png_bytes), "image/png")}
        r = requests.post(f"{API}/upload/image", files=files,
                          headers=_h(STATE["teacher_token"]), timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["url"].startswith("http")
        assert "question-images" in d["url"]
