"""Iter22: Upgrade paywall packs on top of tier system."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://nexu-qbank.preview.emergentagent.com").rstrip("/")
STUDENT_EMAIL = "student@test.com"
STUDENT_PASSWORD = "password123"


@pytest.fixture(scope="module")
def student_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture
def auth_headers(student_token):
    return {"Authorization": f"Bearer {student_token}", "Content-Type": "application/json"}


# --- /auth/me tier fields ---
def test_auth_me_has_tier_fields(auth_headers):
    r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers, timeout=30)
    assert r.status_code == 200, r.text
    u = r.json()["user"]
    assert "access_tier" in u
    assert "is_existing_student" in u
    assert u["access_tier"] == "free", f"expected free, got {u['access_tier']}"


# --- create-order plans ---
def test_create_order_lectures_upgrade(auth_headers):
    r = requests.post(f"{BASE_URL}/api/payments/create-order",
                      headers=auth_headers, json={"plan": "lectures_upgrade"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["amount"] == 150000
    assert d["plan"] == "lectures_upgrade"
    assert d.get("order_id", "").startswith("order_")
    assert d.get("key_id")


def test_create_order_lectures_tests_upgrade(auth_headers):
    r = requests.post(f"{BASE_URL}/api/payments/create-order",
                      headers=auth_headers, json={"plan": "lectures_tests_upgrade"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["amount"] == 250000
    assert d["plan"] == "lectures_tests_upgrade"


def test_create_order_admission_backcompat(auth_headers):
    r = requests.post(f"{BASE_URL}/api/payments/create-order",
                      headers=auth_headers, json={"plan": "admission_fee"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["amount"] == 3000000
    assert d["plan"] == "admission_fee"


def test_create_order_unknown_plan(auth_headers):
    r = requests.post(f"{BASE_URL}/api/payments/create-order",
                      headers=auth_headers, json={"plan": "bogus"}, timeout=30)
    assert r.status_code == 400
    assert "Unknown plan" in r.json().get("detail", "")


def test_create_order_price_override_for_upgrade(auth_headers):
    """Client amount must be ignored for upgrade plans."""
    r = requests.post(f"{BASE_URL}/api/payments/create-order",
                      headers=auth_headers, json={"plan": "lectures_upgrade", "amount": 1}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["amount"] == 150000, f"server-side override failed, got {d['amount']}"
