"""Iter 21 backend tests:
- 3 seed logins
- student@test.com moved to NEX2027
- preseed-status + claim-preseed flow
- simple-submit admission + create-order + duplicate rejection
- /auth/me after preseed claim -> live_batch tier
"""
import os
import time
import uuid
import requests
import pytest

def _load_env():
    p = "/app/frontend/.env"
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)
_load_env()
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

SEED = [
    ("admin@nexuacademy.com", "nexuacademy123", "admin"),
    ("teacher@test.com", "password123", "teacher"),
    ("student@test.com", "password123", "student"),
]


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    return r


@pytest.mark.parametrize("email,password,role", SEED)
def test_seed_login(email, password, role):
    r = _login(email, password)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    user = data.get("user") or {}
    assert user.get("role") == role
    if email == "student@test.com":
        assert user.get("batch_id") == "NEX2027", f"student batch={user.get('batch_id')}"


def test_preseed_status_true_arjun():
    r = requests.get(f"{API}/auth/preseed-status", params={"first_name": "Arjun", "batch_id": "NEX2027"}, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j.get("is_preseed") is True


def test_preseed_status_true_shefali():
    r = requests.get(f"{API}/auth/preseed-status", params={"first_name": "Shefali", "batch_id": "NEX2027"}, timeout=30)
    assert r.status_code == 200
    assert r.json().get("is_preseed") is True


def test_preseed_status_true_shantanu():
    r = requests.get(f"{API}/auth/preseed-status", params={"first_name": "Shantanu", "batch_id": "NEX2028"}, timeout=30)
    assert r.status_code == 200
    assert r.json().get("is_preseed") is True


def test_preseed_status_false_unknown():
    r = requests.get(f"{API}/auth/preseed-status", params={"first_name": "Zzznotreal", "batch_id": "NEX2027"}, timeout=30)
    assert r.status_code == 200
    assert r.json().get("is_preseed") is False


# Use fresh preseed names – iterations may have consumed some
CLAIM_CANDIDATES = ["Garvit", "Khushi", "Kartavya", "Kovid", "Krisha", "Naavya", "Pragya",
                    "Abhinav", "Vivaan", "Urveesh", "Yashasvi", "Madhav", "Aniket",
                    "Rittam", "Eeshaan", "Ayush"]


@pytest.fixture(scope="module")
def claimed_user():
    """Claim the first candidate that still shows unclaimed."""
    for name in CLAIM_CANDIDATES:
        st = requests.get(f"{API}/auth/preseed-status",
                          params={"first_name": name, "batch_id": "NEX2027"}, timeout=30).json()
        if st.get("is_preseed") and not st.get("claimed"):
            uniq = uuid.uuid4().hex[:8]
            email = f"test_{name.lower()}_{uniq}@example.com"
            r = requests.post(f"{API}/auth/claim-preseed", json={
                "first_name": name, "email": email, "batch_id": "NEX2027"
            }, timeout=30)
            if r.status_code == 200:
                return {"name": name, "email": email, "resp": r.json()}
    pytest.skip("No unclaimed preseed candidates available")


def test_claim_preseed_success(claimed_user):
    data = claimed_user["resp"]
    name_lower = claimed_user["name"].lower()
    assert data.get("default_password") == f"{name_lower}2027"
    assert "access_token" in data
    user = data.get("user") or {}
    assert user.get("access_tier") == "live_batch"
    assert user.get("batch_id") == "NEX2027"


def test_claim_preseed_reclaim_400(claimed_user):
    r = requests.post(f"{API}/auth/claim-preseed", json={
        "first_name": claimed_user["name"],
        "email": f"other_{uuid.uuid4().hex[:6]}@example.com",
        "batch_id": "NEX2027"
    }, timeout=30)
    assert r.status_code == 400, r.text


def test_claim_preseed_unknown_404():
    r = requests.post(f"{API}/auth/claim-preseed", json={
        "first_name": "Zzznotreal",
        "email": f"nn_{uuid.uuid4().hex[:6]}@example.com",
        "batch_id": "NEX2027"
    }, timeout=30)
    assert r.status_code == 404, r.text


def test_auth_me_after_claim(claimed_user):
    tok = claimed_user["resp"]["access_token"]
    r = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    if "user" in j and isinstance(j["user"], dict):
        j = j["user"]
    assert j.get("access_tier") == "live_batch"
    assert j.get("is_existing_student") is True


# ---------- simple-submit + create-order ----------

@pytest.fixture(scope="module")
def simple_submitted():
    uniq = uuid.uuid4().hex[:10]
    payload = {
        "full_name": f"TEST Iter21 {uniq}",
        "email": f"test_iter21_{uniq}@example.com",
        "whatsapp_number": "+919999900000",
    }
    r = requests.post(f"{API}/admissions/simple-submit", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    return {"payload": payload, "resp": data}


def test_simple_submit_ok(simple_submitted):
    d = simple_submitted["resp"]
    assert "application_id" in d
    assert d.get("generated_password")
    assert d.get("access_token")
    assert d.get("user")


def test_simple_submit_duplicate_400(simple_submitted):
    r = requests.post(f"{API}/admissions/simple-submit",
                      json=simple_submitted["payload"], timeout=30)
    assert r.status_code == 400, r.text


def test_create_order_after_simple_submit(simple_submitted):
    tok = simple_submitted["resp"]["access_token"]
    r = requests.post(f"{API}/payments/create-order",
                      json={"payment_type": "admission_fee"},
                      headers={"Authorization": f"Bearer {tok}"}, timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("order_id")
    assert d.get("amount") == 3000000
    assert d.get("key_id")
