"""Iter23 backend tests — teacher/student class root alias, google oauth redirect_to,
batch cleanup migration, preseed roster."""
import os
import time
import uuid
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def teacher_token():
    return _login("teacher@test.com", "password123")


@pytest.fixture(scope="module")
def student_token():
    return _login("student@test.com", "password123")


@pytest.fixture(scope="module")
def admin_token():
    return _login("admin@nexuacademy.com", "nexuacademy123")


# ---------------- Teacher classes root alias + stats ----------------

def test_teacher_classes_root_alias(teacher_token):
    h = {"Authorization": f"Bearer {teacher_token}"}
    r = requests.get(f"{API}/teacher/classes/", headers=h, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("success") is True
    assert isinstance(data.get("classes"), list)


def test_teacher_classes_stats(teacher_token):
    h = {"Authorization": f"Bearer {teacher_token}"}
    r = requests.get(f"{API}/teacher/classes/stats", headers=h, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("total", "upcoming", "completed"):
        assert k in d


def test_teacher_classes_stats_summary(teacher_token):
    h = {"Authorization": f"Bearer {teacher_token}"}
    r = requests.get(f"{API}/teacher/classes/stats/summary", headers=h, timeout=30)
    assert r.status_code == 200


# ---------------- E2E: create class → visible in teacher & student list ----------------

def test_create_class_e2e_visible_to_teacher_and_student(teacher_token, student_token):
    h = {"Authorization": f"Bearer {teacher_token}"}
    title = f"TEST_iter23_{uuid.uuid4().hex[:8]}"
    payload = {
        "title": title,
        "subject": "Physics",
        "chapter": "Rotation",
        "topic": "Torque",
        "description": "iter23 e2e",
        "prerequisites": "",
        "scheduled_date": "2027-06-01",
        "scheduled_time": "10:00",
        "duration": 60,
        "meeting_link": "https://zoom.us/j/1234567890",
        "meeting_platform": "Zoom",
        "assigned_batches": ["NEX2027"],
    }
    r = requests.post(f"{API}/teacher/classes/create", json=payload, headers=h, timeout=30)
    assert r.status_code == 200, r.text
    created = r.json()
    assert created.get("success") is True
    class_id = created["class"]["class_id"]

    # Teacher sees it
    r2 = requests.get(f"{API}/teacher/classes/", headers=h, timeout=30)
    assert r2.status_code == 200
    titles = [c.get("title") for c in r2.json()["classes"]]
    assert title in titles, f"Teacher does not see new class. titles={titles}"

    # Student in NEX2027 sees it via root alias
    sh = {"Authorization": f"Bearer {student_token}"}
    r3 = requests.get(f"{API}/student/classes/", headers=sh, timeout=30)
    assert r3.status_code == 200, r3.text
    stitles = [c.get("title") for c in r3.json()["classes"]]
    assert title in stitles, f"Student does not see class. titles={stitles}"

    # Also via /my-classes for parity
    r4 = requests.get(f"{API}/student/classes/my-classes", headers=sh, timeout=30)
    assert r4.status_code == 200
    my_titles = [c.get("title") for c in r4.json()["classes"]]
    assert title in my_titles

    # Cleanup
    requests.delete(f"{API}/teacher/classes/{class_id}", headers=h, timeout=30)


# ---------------- Google OAuth URL ----------------

def test_google_oauth_url_with_redirect_to():
    redir = "https://nexuacademy.com/auth/callback"
    r = requests.get(f"{API}/auth/google/url", params={"redirect_to": redir}, timeout=30)
    assert r.status_code == 200, r.text
    url = r.json().get("url", "")
    assert "/auth/v1/authorize" in url and "provider=google" in url
    assert "redirect_to=https%3A%2F%2Fnexuacademy.com%2Fauth%2Fcallback" in url


def test_google_oauth_url_without_redirect_to():
    r = requests.get(f"{API}/auth/google/url", timeout=30)
    assert r.status_code == 200
    url = r.json().get("url", "")
    assert "/auth/v1/authorize" in url and "provider=google" in url


# ---------------- Migration verifications (admin queries) ----------------

def test_no_students_in_jeem2027(admin_token):
    """Uses admin students-list endpoint if available; otherwise skip."""
    h = {"Authorization": f"Bearer {admin_token}"}
    # Try common admin endpoints
    for path in ("/admin/students", "/admin/users", "/admin/profiles"):
        r = requests.get(f"{API}{path}", headers=h, timeout=30)
        if r.status_code == 200:
            body = r.json()
            items = body.get("students") or body.get("users") or body.get("profiles") or body if isinstance(body, list) else []
            if isinstance(body, dict):
                for k in ("students", "users", "profiles", "data", "items"):
                    if isinstance(body.get(k), list):
                        items = body[k]
                        break
            jeem = [u for u in items if (u.get("batch_id") == "JEEM2027" and (u.get("role") == "student"))]
            assert len(jeem) == 0, f"Found {len(jeem)} students still in JEEM2027"
            return
    pytest.skip("No admin students endpoint available to verify")


def test_preseed_shefali_present(admin_token):
    """Shefali should be a preseed with default_password shefali2027."""
    r = requests.get(f"{API}/auth/preseed-status", params={
        "first_name": "Shefali", "batch_id": "NEX2027"
    }, timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("is_preseed") is True
    assert d.get("batch_id") == "NEX2027"
    assert d.get("first_name", "").lower() == "shefali"


# ---------------- /auth/me tier field ----------------

def test_auth_me_has_access_tier(student_token):
    h = {"Authorization": f"Bearer {student_token}"}
    r = requests.get(f"{API}/auth/me", headers=h, timeout=30)
    assert r.status_code == 200
    u = r.json()["user"]
    assert "access_tier" in u
    assert u.get("batch_id") == "NEX2027"
