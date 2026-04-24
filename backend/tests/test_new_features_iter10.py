"""
Iteration 10 — tests for new features:
  - Student Analytics (overview/heatmap/activity/leaderboard)
  - Teacher detailed test results + CSV export
  - Batch CRUD (custom batches; predefined protection)
  - Reminder scheduler sanity
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

STUDENT = {"email": "student@test.com", "password": "password123"}
TEACHER = {"email": "teacher@test.com", "password": "password123"}
KNOWN_TEST_ID = "ttest_55c6448044bf"  # JEE Main test owned by teacher@test.com


def _login(creds):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"Login failed for {creds['email']}: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def student_session():
    return _login(STUDENT)


@pytest.fixture(scope="module")
def teacher_session():
    return _login(TEACHER)


# ---------- Student analytics ----------
class TestStudentAnalytics:
    def test_overview(self, student_session):
        r = student_session.get(f"{API}/student/analytics/overview", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("total_tests", "avg_accuracy", "batch_rank", "best_test", "worst_test"):
            assert k in data, f"missing key {k} in {data}"
        # best_test/worst_test may be null if no attempts – but for seeded student there IS data
        if data["best_test"]:
            assert "test_name" in data["best_test"]
        if data["worst_test"]:
            assert "test_name" in data["worst_test"]

    def test_heatmap(self, student_session):
        r = student_session.get(f"{API}/student/analytics/heatmap", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # expect list of cells with subject/chapter/accuracy
        assert isinstance(data, (list, dict))
        cells = data if isinstance(data, list) else data.get("cells", [])
        if cells:
            c = cells[0]
            assert "subject" in c and "chapter" in c and "accuracy" in c

    def test_activity_30_buckets(self, student_session):
        r = student_session.get(f"{API}/student/analytics/activity", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        buckets = data if isinstance(data, list) else data.get("buckets") or data.get("activity") or []
        assert len(buckets) == 30, f"expected 30 buckets, got {len(buckets)}: sample={buckets[:2]}"

    def test_leaderboard(self, student_session):
        r = student_session.get(f"{API}/student/analytics/leaderboard", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        rows = data if isinstance(data, list) else data.get("leaderboard") or data.get("rows") or []
        # Student has batch JEE Mains 2027 — should include self
        if rows:
            has_me = any(bool(r_.get("is_me")) for r_ in rows)
            assert has_me, "logged-in student should have is_me=true in leaderboard"


# ---------- Teacher detailed test results + CSV ----------
class TestTeacherTestResults:
    def test_results_enriched(self, teacher_session):
        r = teacher_session.get(f"{API}/teacher/tests/{KNOWN_TEST_ID}/results", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        # expect stats, question_stats, attempts with rank
        assert "stats" in data, f"missing stats: {list(data.keys())}"
        for k in ("avg_score", "avg_accuracy", "highest", "lowest"):
            assert k in data["stats"], f"stats missing {k}"
        assert "question_stats" in data
        assert isinstance(data["question_stats"], list)
        attempts = data.get("attempts") or data.get("results") or []
        if attempts:
            assert "rank" in attempts[0], f"attempts missing rank: {attempts[0].keys()}"

    def test_results_csv(self, teacher_session):
        r = teacher_session.get(f"{API}/teacher/tests/{KNOWN_TEST_ID}/results.csv", timeout=30)
        assert r.status_code == 200, r.text
        ct = r.headers.get("content-type", "")
        assert "text/csv" in ct, f"unexpected content-type: {ct}"
        cd = r.headers.get("content-disposition", "")
        assert "attachment" in cd.lower(), f"missing attachment header: {cd}"
        body = r.text
        header = body.splitlines()[0].lower() if body else ""
        for col in ("rank", "student", "email", "batch", "score", "accuracy"):
            assert col in header, f"missing column '{col}' in CSV header: {header}"

    def test_csv_forbidden_for_student(self, student_session):
        r = student_session.get(f"{API}/teacher/tests/{KNOWN_TEST_ID}/results.csv", timeout=30)
        assert r.status_code in (401, 403), r.status_code


# ---------- Batch CRUD ----------
class TestBatchCRUD:
    created_id = None

    def test_list_merges_predefined(self, teacher_session):
        r = teacher_session.get(f"{API}/batches/", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        batches = data if isinstance(data, list) else data.get("batches") or []
        names = [b.get("name") for b in batches]
        # expect at least one predefined like JEE Mains 2027
        assert any("JEE" in (n or "") for n in names), f"predefined not present: {names}"

    def test_create_custom_batch(self, teacher_session):
        payload = {"name": "TEST_QA Batch 2027", "year": 2027}
        r = teacher_session.post(f"{API}/batches/", json=payload, timeout=30)
        assert r.status_code in (200, 201), r.text
        data = r.json()
        batch = data.get("batch") or data
        assert batch.get("name") == payload["name"]
        assert "id" in batch or "_id" in batch or "batch_id" in batch
        TestBatchCRUD.created_id = batch.get("id") or batch.get("batch_id") or batch.get("_id")

        # verify GET lists it
        r2 = teacher_session.get(f"{API}/batches/", timeout=30)
        names = [b.get("name") for b in (r2.json() if isinstance(r2.json(), list) else r2.json().get("batches", []))]
        assert payload["name"] in names

    def test_delete_predefined_blocked(self, teacher_session):
        # attempt to delete a predefined batch id — use a clearly-predefined name/id
        r = teacher_session.get(f"{API}/batches/", timeout=30)
        batches = r.json() if isinstance(r.json(), list) else r.json().get("batches", [])
        predefined = next((b for b in batches if not b.get("is_custom", False) and b.get("id")), None)
        if not predefined:
            pytest.skip("no predefined batch with id available")
        pid = predefined["id"]
        rd = teacher_session.delete(f"{API}/batches/{pid}", timeout=30)
        assert rd.status_code in (400, 403), f"predefined delete should be blocked: {rd.status_code} {rd.text}"

    def test_delete_custom_batch(self, teacher_session):
        if not TestBatchCRUD.created_id:
            pytest.skip("no custom batch created")
        rd = teacher_session.delete(f"{API}/batches/{TestBatchCRUD.created_id}", timeout=30)
        assert rd.status_code in (200, 204), rd.text


# ---------- Scheduler sanity ----------
class TestSchedulerSanity:
    def test_scheduler_log_present(self):
        import subprocess
        out = subprocess.run(
            ["grep", "-c", "Unified reminder scheduler started",
             "/var/log/supervisor/backend.err.log"],
            capture_output=True, text=True
        )
        assert int(out.stdout.strip() or 0) >= 1


# ---------- Regression: auth still works ----------
class TestAuthRegression:
    def test_student_me(self, student_session):
        r = student_session.get(f"{API}/auth/me", timeout=30)
        assert r.status_code == 200
        assert r.json().get("email") == STUDENT["email"]

    def test_teacher_me(self, teacher_session):
        r = teacher_session.get(f"{API}/auth/me", timeout=30)
        assert r.status_code == 200
        assert r.json().get("email") == TEACHER["email"]
