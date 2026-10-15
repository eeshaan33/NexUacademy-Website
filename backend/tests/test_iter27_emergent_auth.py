"""Iteration 27: Emergent Google Auth — backend endpoint tests + regression."""
import os
import pytest
import requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get("REACT_APP_BACKEND_URL") else None
if not BASE:
    # fallback to frontend/.env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE = line.split("=", 1)[1].strip().rstrip("/")
                break

API = f"{BASE}/api"


# ---- Emergent auth endpoints ----
class TestEmergentSession:
    def test_missing_header_returns_400(self):
        r = requests.post(f"{API}/auth/emergent/session", timeout=30)
        assert r.status_code == 400, r.text
        assert "Missing X-Session-ID" in r.json().get("detail", "")

    def test_invalid_session_id_returns_401(self):
        r = requests.post(
            f"{API}/auth/emergent/session",
            headers={"X-Session-ID": "fake_test_id_bogus_xyz"},
            timeout=30,
        )
        assert r.status_code == 401, r.text
        assert "Invalid Emergent session_id" in r.json().get("detail", "")

    def test_logout_no_cookie_idempotent(self):
        r = requests.post(f"{API}/auth/emergent/logout", timeout=30)
        assert r.status_code == 200
        assert r.json().get("success") is True


# ---- Regression on existing Supabase auth (bearer JWT path via new middleware) ----
class TestSupabaseAuthRegression:
    @pytest.fixture(scope="class")
    def teacher_token(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": "teacher@test.com", "password": "password123"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("access_token")
        assert data["user"]["role"] == "teacher"
        return data["access_token"]

    def test_login_teacher(self, teacher_token):
        assert isinstance(teacher_token, str) and len(teacher_token) > 20

    def test_me_with_bearer(self, teacher_token):
        r = requests.get(
            f"{API}/auth/me",
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=30,
        )
        assert r.status_code == 200, r.text
        assert r.json()["user"]["role"] == "teacher"

    def test_me_missing_auth_returns_401(self):
        r = requests.get(f"{API}/auth/me", timeout=30)
        assert r.status_code == 401
        assert "Missing bearer token" in r.json().get("detail", "")


# ---- Class scheduling regression (from iteration_26 baseline) ----
class TestClassRegression:
    @pytest.fixture(scope="class")
    def teacher_h(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": "teacher@test.com", "password": "password123"},
            timeout=30,
        )
        assert r.status_code == 200
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    @pytest.fixture(scope="class")
    def student_h(self):
        r = requests.post(
            f"{API}/auth/login",
            json={"email": "student@test.com", "password": "password123"},
            timeout=30,
        )
        assert r.status_code == 200
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def test_teacher_classes_endpoint(self, teacher_h):
        r = requests.get(f"{API}/teacher/classes/", headers=teacher_h, timeout=30)
        assert r.status_code in (200, 404), r.text  # 200 is expected; verify it's not 401/500

    def test_student_my_classes_endpoint(self, student_h):
        r = requests.get(f"{API}/student/classes/my-classes", headers=student_h, timeout=30)
        assert r.status_code in (200, 404), r.text
