"""Iteration 16 tests — Razorpay payments + Analytics dashboards."""
import hmac
import hashlib
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://tier-learn-app.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

RAZORPAY_KEY_SECRET = "MPm0hqGI2U4iIVf6Yh2EDGMU"

ADMIN = {"email": "admin@nexuacademy.com", "password": "nexuacademy123"}
TEACHER = {"email": "teacher@test.com", "password": "password123"}
STUDENT = {"email": "student@test.com", "password": "password123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT)


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


@pytest.fixture(scope="module")
def teacher_token():
    return _login(TEACHER)


def h(token):
    return {"Authorization": f"Bearer {token}"}


# ------------------------- Auth sanity -------------------------
class TestAuthSeed:
    def test_admin_login(self):
        assert _login(ADMIN)

    def test_teacher_login(self):
        assert _login(TEACHER)

    def test_student_login(self):
        assert _login(STUDENT)


# ------------------------- Batches --------------------------------
class TestBatchesByCode:
    @pytest.mark.parametrize("code", ["JEEM2027", "NEX2027", "NEX2028"])
    def test_by_code(self, code):
        r = requests.get(f"{API}/batches/by-code/{code}", timeout=15)
        assert r.status_code == 200, f"{code} -> {r.status_code} {r.text}"
        data = r.json()
        # Response may be batch object directly or wrapped
        assert code in str(data)


# ------------------------- Analytics -----------------------------
class TestAnalytics:
    def test_student_dashboard(self, student_token):
        r = requests.get(f"{API}/analytics/dashboard", headers=h(student_token), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        s = data["stats"]
        for k in ["tests_taken", "tests_in_progress", "average_accuracy",
                  "total_classes", "upcoming_classes", "unread_notifications"]:
            assert k in s, f"missing key {k}"

    def test_student_subject_wise(self, student_token):
        r = requests.get(f"{API}/analytics/subject-wise", headers=h(student_token), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        assert isinstance(data.get("subjects"), list)

    def test_admin_overview(self, admin_token):
        r = requests.get(f"{API}/analytics/admin/overview", headers=h(admin_token), timeout=20)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        s = data["stats"]
        for k in ["total_students", "total_teachers", "total_classes",
                  "total_tests", "total_announcements", "revenue_inr"]:
            assert k in s
        assert isinstance(data["batches"], list)
        assert isinstance(data["recent_signups"], list)
        assert isinstance(data["recent_payments"], list)

    def test_admin_overview_forbidden_for_student(self, student_token):
        r = requests.get(f"{API}/analytics/admin/overview", headers=h(student_token), timeout=20)
        assert r.status_code == 403, r.text

    def test_admin_overview_forbidden_for_teacher(self, teacher_token):
        r = requests.get(f"{API}/analytics/admin/overview", headers=h(teacher_token), timeout=20)
        assert r.status_code == 403, r.text


# ------------------------- Payments ------------------------------
class TestPayments:
    @pytest.fixture(scope="class")
    def order(self, student_token):
        r = requests.post(f"{API}/payments/create-order",
                          headers=h(student_token),
                          json={"plan": "admission_fee"}, timeout=30)
        assert r.status_code == 200, f"create-order failed: {r.status_code} {r.text}"
        data = r.json()
        assert data["amount"] == 3000000
        assert data["currency"] == "INR"
        assert data["order_id"].startswith("order_")
        assert data["key_id"].startswith("rzp_test_")
        assert "prefill" in data
        assert data["prefill"]["email"] == STUDENT["email"]
        assert "receipt" in data
        return data

    def test_create_order(self, order):
        assert order["order_id"]

    def test_verify_bad_signature(self, student_token, order):
        payload = {
            "razorpay_order_id": order["order_id"],
            "razorpay_payment_id": f"pay_test_{uuid.uuid4().hex[:12]}",
            "razorpay_signature": "deadbeef" * 8,
        }
        r = requests.post(f"{API}/payments/verify", headers=h(student_token),
                          json=payload, timeout=20)
        assert r.status_code == 400, r.text

    def test_my_payments_shows_failed(self, student_token, order):
        r = requests.get(f"{API}/payments/my", headers=h(student_token), timeout=20)
        assert r.status_code == 200
        payments = r.json()["payments"]
        match = [p for p in payments if p.get("razorpay_order_id") == order["order_id"]]
        assert match, "our order not in /payments/my"
        assert match[0]["status"] == "failed"

    def test_verify_good_signature(self, student_token):
        # Create a fresh order (previous one was marked failed)
        r = requests.post(f"{API}/payments/create-order",
                          headers=h(student_token),
                          json={"plan": "admission_fee"}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        order_id = d["order_id"]
        payment_id_rp = f"pay_test_{uuid.uuid4().hex[:12]}"
        body = f"{order_id}|{payment_id_rp}".encode()
        sig = hmac.new(RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256).hexdigest()
        vr = requests.post(f"{API}/payments/verify", headers=h(student_token), json={
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id_rp,
            "razorpay_signature": sig,
        }, timeout=20)
        assert vr.status_code == 200, vr.text
        assert vr.json()["status"] == "paid"
        # Verify persistence via /payments/my
        my = requests.get(f"{API}/payments/my", headers=h(student_token), timeout=20).json()
        row = next((p for p in my["payments"] if p["razorpay_order_id"] == order_id), None)
        assert row and row["status"] == "paid"


# ------------------------- Webhook -------------------------------
class TestWebhook:
    def test_webhook_unknown_order(self):
        payload = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {
                "id": "pay_fake123", "order_id": "order_unknown_xyz"
            }}},
        }
        r = requests.post(f"{API}/payments/webhook", json=payload, timeout=20)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["received"] is True
        assert j["matched"] is False

    def test_webhook_matched_order(self, student_token):
        # Create an order, then send webhook payment.captured for it
        r = requests.post(f"{API}/payments/create-order",
                          headers=h(student_token),
                          json={"plan": "admission_fee"}, timeout=30)
        assert r.status_code == 200
        order_id = r.json()["order_id"]

        wh = {
            "event": "payment.captured",
            "payload": {"payment": {"entity": {
                "id": f"pay_wh_{uuid.uuid4().hex[:10]}",
                "order_id": order_id,
            }}},
        }
        wr = requests.post(f"{API}/payments/webhook", json=wh, timeout=20)
        assert wr.status_code == 200, wr.text
        j = wr.json()
        assert j["received"] is True
        assert j["matched"] is True
        assert j["event"] == "payment.captured"

        # Confirm payment status flipped to 'paid'
        my = requests.get(f"{API}/payments/my", headers=h(student_token), timeout=20).json()
        row = next((p for p in my["payments"] if p["razorpay_order_id"] == order_id), None)
        assert row and row["status"] == "paid"


# ------------------------- Full admission → order flow -----------
class TestAdmissionToPayment:
    def test_full_flow(self):
        email = f"TEST_{uuid.uuid4().hex[:10]}@nexutest.dev"
        password = "Password123!"
        admission = {
            "email": email,
            "password": password,
            "student_name": "Test Admission Flow",
            "father_name": "Father Test",
            "mother_name": "Mother Test",
            "contact_number": "9876543210",
            "date_of_birth": "2008-06-15",
            "gender": "male",
            "address": "1 Test Lane",
            "city": "Delhi",
            "state": "Delhi",
            "pincode": "110001",
            "class_level": "12",
            "school_name": "Delhi Public School",
            "course_applying": "JEE Mains",
            "batch_code": "JEEM2027",
        }
        r = requests.post(f"{API}/admissions/submit", json=admission, timeout=30)
        assert r.status_code in (200, 201), f"admission failed: {r.status_code} {r.text}"
        body = r.json()
        assert body.get("success") is True or body.get("student_id") or body.get("roll_number")
        # roll_number should exist somewhere in response
        assert "roll_number" in str(body).lower() or body.get("roll_number")

        # Login as new student
        token = _login({"email": email, "password": password})
        # Create order
        cr = requests.post(f"{API}/payments/create-order", headers=h(token),
                           json={"plan": "admission_fee"}, timeout=30)
        assert cr.status_code == 200, cr.text
        data = cr.json()
        assert data["amount"] == 3000000
        assert data["order_id"].startswith("order_")
