"""Iteration 18 tests — server-authoritative scoring, autosave, PDF/Resend receipt,
LiveNowBanner backend feed, dynamic batches regression."""
import hashlib
import hmac
import os
import sys
import uuid

import pytest
import requests

# Ensure /app/backend is on sys.path so we can import services.* for the
# receipt-builder standalone assertion.
BACKEND_DIR = "/app/backend"
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://neet-jee-prep-55.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

RAZORPAY_KEY_SECRET = "MPm0hqGI2U4iIVf6Yh2EDGMU"

ADMIN = {"email": "admin@nexuacademy.com", "password": "nexuacademy123"}
TEACHER = {"email": "teacher@test.com", "password": "password123"}
STUDENT = {"email": "student@test.com", "password": "password123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login {creds['email']} failed: {r.status_code} {r.text}"
    return r.json()["access_token"]


def h(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT)


@pytest.fixture(scope="module")
def teacher_token():
    return _login(TEACHER)


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN)


# --------------- Helper: create a 4-question test assigned to JEEM2027 ---------------
def _make_test(teacher_token, name_suffix=""):
    """Create test with:
      Q1 MCQ_Single correct=A (marks 4/-1)
      Q2 MCQ_Multiple correct=[B,C] (marks 4/-1)
      Q3 Numerical correct=42 range 41.9..42.1 (marks 4/0)
      Q4 MCQ_Single correct=D (marks 4/-1)
    """
    questions = [
        {"question_number": 1, "question_type": "MCQ_Single", "question_text": "1+1?",
         "options": ["A) 2", "B) 3", "C) 4", "D) 5"], "correct_answers": ["A"],
         "marks": 4, "negative_marks": -1},
        {"question_number": 2, "question_type": "MCQ_Multiple", "question_text": "Primes?",
         "options": ["A) 4", "B) 5", "C) 7", "D) 9"], "correct_answers": ["B", "C"],
         "marks": 4, "negative_marks": -1},
        {"question_number": 3, "question_type": "Numerical", "question_text": "Answer to life?",
         "numerical_answer": 42, "answer_range": {"min": 41.9, "max": 42.1},
         "marks": 4, "negative_marks": 0},
        {"question_number": 4, "question_type": "MCQ_Single", "question_text": "Capital of India?",
         "options": ["A) Mumbai", "B) Chennai", "C) Kolkata", "D) Delhi"],
         "correct_answers": ["D"], "marks": 4, "negative_marks": -1},
    ]
    payload = {
        "test_name": f"TEST_scoring_{uuid.uuid4().hex[:6]}{name_suffix}",
        "subject": "Physics",
        "test_type": "chapter",
        "exam_type": "JEE Main",
        "duration": 60,
        "total_questions": 4,
        "total_marks": 16,
        "assigned_batches": ["JEEM2027"],
        "questions": questions,
        "status": "scheduled",
    }
    r = requests.post(f"{API}/teacher/tests/create", headers=h(teacher_token),
                      json=payload, timeout=30)
    assert r.status_code == 200, f"create test failed: {r.status_code} {r.text}"
    return r.json()["test"]


def _start_attempt(student_token, test_id):
    r = requests.post(f"{API}/student/tests/{test_id}/start",
                      headers=h(student_token), json={}, timeout=20)
    assert r.status_code == 200, f"start failed: {r.status_code} {r.text}"
    return r.json()["attempt"]["attempt_id"]


# --------------- Scoring: client lies about is_correct ---------------
class TestServerScoring:
    @pytest.fixture(scope="class")
    def test_row(self, teacher_token):
        return _make_test(teacher_token)

    @pytest.fixture(scope="class")
    def cleanup(self, teacher_token, test_row):
        yield
        try:
            requests.delete(f"{API}/teacher/tests/{test_row['test_id']}",
                            headers=h(teacher_token), timeout=15)
        except Exception:
            pass

    def test_client_lies_are_ignored(self, student_token, teacher_token, test_row, cleanup):
        test_id = test_row["test_id"]
        attempt_id = _start_attempt(student_token, test_id)

        # Client submits: Q1=A (correct), Q2=[A,B] (wrong), Q3=100 (wrong), Q4=D (correct)
        # But CLIENT LIES: is_correct=True for all of them.
        answers = [
            {"question_number": 1, "selected_answer": "A", "is_correct": True, "time_taken": 5},
            {"question_number": 2, "selected_answer": ["A", "B"], "is_correct": True, "time_taken": 5},
            {"question_number": 3, "selected_answer": "100", "is_correct": True, "time_taken": 5},
            {"question_number": 4, "selected_answer": "D", "is_correct": True, "time_taken": 5},
        ]
        r = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                          headers=h(student_token),
                          json={"answers": answers, "time_spent": 100}, timeout=30)
        assert r.status_code == 200, r.text
        att = r.json()["attempt"]
        # Server-computed: Q1 correct (+4), Q2 wrong (-1), Q3 wrong (0), Q4 correct (+4) = 7
        assert att["total_score"] == 7, f"expected 7 got {att['total_score']}"
        assert att["correct_answers"] == 2
        assert att["incorrect_answers"] == 2
        assert att["unattempted"] == 0
        assert att["max_score"] == 16
        # 2 correct out of 4 attempted => 50% accuracy
        assert abs(float(att["accuracy"]) - 50.0) < 0.01
        # Verify authoritative_answers overrode is_correct
        import json as _json
        answers_out = att["answers"]
        if isinstance(answers_out, str):
            answers_out = _json.loads(answers_out)
        by_q = {a["question_number"]: a for a in answers_out}
        assert by_q[1]["is_correct"] is True
        assert by_q[2]["is_correct"] is False   # client said True — server overrode
        assert by_q[3]["is_correct"] is False   # client said True — server overrode
        assert by_q[4]["is_correct"] is True

    def test_unattempted_submit_scores_zero(self, student_token, teacher_token, cleanup):
        test_row = _make_test(teacher_token, name_suffix="_unattempted")
        try:
            attempt_id = _start_attempt(student_token, test_row["test_id"])
            answers = [
                {"question_number": 1, "selected_answer": ""},
                {"question_number": 2, "selected_answer": []},
                {"question_number": 3, "selected_answer": None},
                {"question_number": 4, "selected_answer": ""},
            ]
            r = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                              headers=h(student_token),
                              json={"answers": answers, "time_spent": 10}, timeout=30)
            assert r.status_code == 200, r.text
            att = r.json()["attempt"]
            assert att["total_score"] == 0
            assert att["correct_answers"] == 0
            assert att["incorrect_answers"] == 0
            assert att["unattempted"] == 4
            assert att["accuracy"] in (0, 0.0)
        finally:
            requests.delete(f"{API}/teacher/tests/{test_row['test_id']}",
                            headers=h(teacher_token), timeout=15)

    def test_resubmit_is_idempotent(self, student_token, teacher_token, cleanup):
        test_row = _make_test(teacher_token, name_suffix="_idempo")
        try:
            attempt_id = _start_attempt(student_token, test_row["test_id"])
            answers = [
                {"question_number": 1, "selected_answer": "A"},
                {"question_number": 2, "selected_answer": ["B", "C"]},
                {"question_number": 3, "selected_answer": "42"},
                {"question_number": 4, "selected_answer": "D"},
            ]
            r1 = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                               headers=h(student_token),
                               json={"answers": answers, "time_spent": 60}, timeout=30)
            assert r1.status_code == 200
            att1 = r1.json()["attempt"]
            assert att1["total_score"] == 16
            assert att1["correct_answers"] == 4

            # Resubmit with different (wrong) answers — must return same score
            wrong = [{"question_number": i, "selected_answer": "X"} for i in range(1, 5)]
            r2 = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                               headers=h(student_token),
                               json={"answers": wrong, "time_spent": 999}, timeout=30)
            assert r2.status_code == 200
            att2 = r2.json()["attempt"]
            assert att2["total_score"] == att1["total_score"] == 16
            assert att2["correct_answers"] == 4
            assert att2["status"] == "submitted"
        finally:
            requests.delete(f"{API}/teacher/tests/{test_row['test_id']}",
                            headers=h(teacher_token), timeout=15)


# --------------- Autosave endpoint ---------------
class TestAutosave:
    def test_autosave_ok_and_skipped_after_submit(self, student_token, teacher_token):
        test_row = _make_test(teacher_token, name_suffix="_autosave")
        try:
            attempt_id = _start_attempt(student_token, test_row["test_id"])
            saved = [{"question_number": 1, "selected_answer": "A"}]
            r = requests.put(f"{API}/student/tests/attempts/{attempt_id}/autosave",
                             headers=h(student_token),
                             json={"answers": saved}, timeout=20)
            assert r.status_code == 200, r.text
            body = r.json()
            assert body.get("success") is True
            assert not body.get("skipped")

            # Now submit
            r_sub = requests.post(f"{API}/student/tests/attempts/{attempt_id}/submit",
                                  headers=h(student_token),
                                  json={"answers": saved, "time_spent": 5}, timeout=30)
            assert r_sub.status_code == 200

            # Autosaving a submitted attempt should return skipped:true
            r2 = requests.put(f"{API}/student/tests/attempts/{attempt_id}/autosave",
                              headers=h(student_token),
                              json={"answers": saved}, timeout=20)
            assert r2.status_code == 200, r2.text
            b2 = r2.json()
            assert b2.get("success") is True
            assert b2.get("skipped") is True
        finally:
            requests.delete(f"{API}/teacher/tests/{test_row['test_id']}",
                            headers=h(teacher_token), timeout=15)


# --------------- Dynamic batches regression ---------------
class TestDynamicBatches:
    def test_create_alphanumeric_batch_ok(self, admin_token):
        code = f"TEST{uuid.uuid4().hex[:6].upper()}"
        name = f"TEST Batch {code}"
        r = requests.post(f"{API}/batches/", headers=h(admin_token),
                          json={"name": name, "year": 2027, "code": code}, timeout=15)
        assert r.status_code == 200, r.text
        b = r.json()["batch"]
        assert b["code"] == code
        assert b["is_custom"] is True

        # duplicate should 400
        r2 = requests.post(f"{API}/batches/", headers=h(admin_token),
                           json={"name": name + " x", "year": 2027, "code": code}, timeout=15)
        assert r2.status_code == 400

        # cleanup: delete custom batch (should 200)
        rd = requests.delete(f"{API}/batches/{code}", headers=h(admin_token), timeout=15)
        assert rd.status_code == 200, rd.text

    def test_non_alphanumeric_code_rejected(self, admin_token):
        code = "BAD-CODE!"
        r = requests.post(f"{API}/batches/", headers=h(admin_token),
                          json={"name": "TEST bad code", "year": 2027, "code": code}, timeout=15)
        # 400 either from pydantic length (BAD-CODE! is 9 alnum-ish w/ special chars length 9 -> passes pydantic min 4 max 16 so falls to alnum check)
        assert r.status_code in (400, 422), r.text

    def test_predefined_cannot_be_deleted(self, admin_token):
        r = requests.delete(f"{API}/batches/JEEM2027", headers=h(admin_token), timeout=15)
        assert r.status_code == 400, r.text


# --------------- Live Now banner backend feed ---------------
class TestLiveClassesFeedForBanner:
    def test_student_live_classes_returns_is_live_flag(self, student_token, teacher_token):
        """LiveNowBanner uses GET /api/student/live-classes/ and filters is_live=true.
        We just verify the endpoint returns the shape banner expects."""
        r = requests.get(f"{API}/student/live-classes/",
                         headers=h(student_token), timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "classes" in data
        # Each class must expose is_live (bool) and class_id / title
        for c in data["classes"]:
            assert "is_live" in c
            assert "class_id" in c
            assert "title" in c


# --------------- Receipt PDF builder (standalone) ---------------
class TestReceiptPdf:
    def test_build_receipt_pdf_returns_bytes(self):
        from services.receipt_service import build_receipt_pdf, pretty_paid_at
        data = {
            "receipt_no": "NEXU-TEST01",
            "payment_id": "pay_TEST_pdf",
            "order_id": "order_TEST_pdf",
            "paid_at_pretty": pretty_paid_at("2026-01-15T10:30:00Z"),
            "amount_paise": 3000000,
            "plan": "admission_fee",
            "student_name": "Test Student",
            "student_email": "student@test.com",
            "student_phone": "9999999999",
            "batch_code": "JEEM2027",
        }
        pdf = build_receipt_pdf(data)
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 1024, f"pdf only {len(pdf)} bytes"
        # PDF file magic
        assert pdf[:4] == b"%PDF"

    def test_pretty_paid_at_handles_none_and_iso(self):
        from services.receipt_service import pretty_paid_at
        s1 = pretty_paid_at(None)
        s2 = pretty_paid_at("2026-01-15T10:30:00Z")
        assert isinstance(s1, str) and len(s1) > 5
        assert "2026" in s2


# --------------- Verify → receipt email attempted (best-effort) ---------------
class TestVerifyEmailReceipt:
    def test_verify_good_sig_returns_paid_and_attempts_email(self, student_token):
        r = requests.post(f"{API}/payments/create-order",
                          headers=h(student_token),
                          json={"plan": "admission_fee"}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        order_id = d["order_id"]
        pay_id = f"pay_test_{uuid.uuid4().hex[:12]}"
        body = f"{order_id}|{pay_id}".encode()
        sig = hmac.new(RAZORPAY_KEY_SECRET.encode(), body, hashlib.sha256).hexdigest()

        vr = requests.post(f"{API}/payments/verify", headers=h(student_token),
                           json={
                               "razorpay_order_id": order_id,
                               "razorpay_payment_id": pay_id,
                               "razorpay_signature": sig,
                           }, timeout=30)
        # Endpoint must still return 200 even if Resend fails (best-effort).
        assert vr.status_code == 200, vr.text
        assert vr.json()["status"] == "paid"

    def test_webhook_captured_still_flips_paid(self, student_token):
        # regression for iter16
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
        wr = requests.post(f"{API}/payments/webhook", json=wh, timeout=30)
        assert wr.status_code == 200
        assert wr.json()["matched"] is True
        my = requests.get(f"{API}/payments/my", headers=h(student_token), timeout=20).json()
        row = next((p for p in my["payments"] if p["razorpay_order_id"] == order_id), None)
        assert row and row["status"] == "paid"
