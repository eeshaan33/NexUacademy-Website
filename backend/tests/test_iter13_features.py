"""Iteration 13 backend tests:
- Enhanced CSV bulk import: duplicate detection (in-batch + vs DB), malformed rows, image_url normalization
- Admin list endpoint /api/questions/admin/list with filters + q search, non-admin 403
- Admin delete /api/questions/admin/{qid}; student GET reflects live sync
- Regression: auth, suggestions, custom-tests minimal, stats
"""
import os
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_CREDS = {"email": "admin@nexuacademy.com", "password": "nexuacademy123"}
STUDENT_CREDS = {"email": "student@test.com", "password": "password123"}
TEACHER_CREDS = {"email": "teacher@test.com", "password": "password123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed {r.status_code} {r.text}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN_CREDS)


@pytest.fixture(scope="module")
def student_token():
    return _login(STUDENT_CREDS)


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def student_headers(student_token):
    return {"Authorization": f"Bearer {student_token}"}


# ---------- Auth regression ----------
def test_login_admin():
    assert _login(ADMIN_CREDS)


def test_login_teacher():
    assert _login(TEACHER_CREDS)


def test_login_student():
    assert _login(STUDENT_CREDS)


# ---------- CSV bulk-import: duplicates within batch + vs DB ----------
CSV_HEADER = ("exam_type,subject,chapter,topic,year,difficulty,question_text,"
              "question_image_url,option_a,option_b,option_c,option_d,correct_answer,"
              "marks,negative_marks,solution_youtube_url,solution_timestamp")


def _make_csv(unique_tag):
    # 2 duplicate rows within batch + 1 unique => inserted=2, duplicates=1
    q_unique = f"TEST_iter13 {unique_tag} Unique question?"
    q_dup = f"TEST_iter13 {unique_tag} Duplicate question?"
    row_u = f'JEE_Main,Physics,Kinematics,1D,2023,Easy,{q_unique},,A,B,C,D,A,4,-1,,0'
    row_d = f'JEE_Main,Physics,Kinematics,1D,2023,Easy,{q_dup},,A,B,C,D,B,4,-1,,0'
    csv_body = "\n".join([CSV_HEADER, row_u, row_d, row_d]) + "\n"
    return csv_body, q_unique, q_dup


@pytest.fixture(scope="module")
def csv_tag():
    return uuid.uuid4().hex[:8]


def test_csv_dup_within_batch_returns_inserted_2_dup_1(admin_headers, csv_tag):
    csv_body, q_u, q_d = _make_csv(csv_tag)
    r = requests.post(
        f"{API}/questions/bulk-import/csv",
        data=csv_body.encode("utf-8"),
        headers={**admin_headers, "Content-Type": "text/csv"},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["inserted"] == 2, f"expected inserted=2 got {j}"
    assert j["duplicates_skipped_count"] == 1, f"expected dup=1 got {j}"


def test_csv_resending_same_all_duplicates(admin_headers, csv_tag):
    csv_body, _, _ = _make_csv(csv_tag)
    r = requests.post(
        f"{API}/questions/bulk-import/csv",
        data=csv_body.encode("utf-8"),
        headers={**admin_headers, "Content-Type": "text/csv"},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["inserted"] == 0, f"expected inserted=0 got {j}"
    assert j["duplicates_skipped_count"] == 3, f"expected dup=3 got {j}"


def test_csv_malformed_rows_errors_and_valid_inserted(admin_headers):
    tag = uuid.uuid4().hex[:8]
    good = (f"JEE_Main,Chemistry,Atomic Structure,Bohr,2022,Easy,"
            f"TEST_iter13 {tag} ValidQ?,,A,B,C,D,A,4,-1,,0")
    # Malformed: missing fields (year invalid)
    bad_missing = "JEE_Main,Chemistry,Atomic Structure,Bohr"
    bad_year = (f"JEE_Main,Chemistry,Atomic Structure,Bohr,NOTYEAR,Easy,"
                f"TEST_iter13 {tag} BadYearQ?,,A,B,C,D,A,4,-1,,0")
    csv_body = "\n".join([CSV_HEADER, good, bad_missing, bad_year]) + "\n"
    r = requests.post(
        f"{API}/questions/bulk-import/csv",
        data=csv_body.encode("utf-8"),
        headers={**admin_headers, "Content-Type": "text/csv"},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["inserted"] >= 1, f"expected >=1 inserted, got {j}"
    assert j["errors_count"] >= 1, f"expected errors_count>=1, got {j}"


def test_csv_image_url_normalization(admin_headers):
    tag = uuid.uuid4().hex[:8]
    # absolute http stays; bare file becomes /uploads/; garbage becomes empty
    r1 = (f"JEE_Main,Physics,Optics,Lens,2022,Easy,"
          f"TEST_iter13 {tag} img1?,https://example.com/a.png,A,B,C,D,A,4,-1,,0")
    r2 = (f"JEE_Main,Physics,Optics,Lens,2022,Easy,"
          f"TEST_iter13 {tag} img2?,foo.png,A,B,C,D,A,4,-1,,0")
    r3 = (f"JEE_Main,Physics,Optics,Lens,2022,Easy,"
          f"TEST_iter13 {tag} img3?,abc,A,B,C,D,A,4,-1,,0")
    csv_body = "\n".join([CSV_HEADER, r1, r2, r3]) + "\n"
    r = requests.post(
        f"{API}/questions/bulk-import/csv",
        data=csv_body.encode("utf-8"),
        headers={**admin_headers, "Content-Type": "text/csv"},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    assert r.json()["inserted"] == 3

    # Fetch via admin list and verify normalization
    qr = requests.get(
        f"{API}/questions/admin/list",
        params={"q": f"TEST_iter13 {tag} img"},
        headers=admin_headers,
        timeout=30,
    )
    assert qr.status_code == 200, qr.text
    rows = qr.json()["questions"]
    by_text = {r["question_text"]: r.get("question_image_url", "") for r in rows}
    # Find matching entries
    img1 = next((v for k, v in by_text.items() if "img1" in k), None)
    img2 = next((v for k, v in by_text.items() if "img2" in k), None)
    img3 = next((v for k, v in by_text.items() if "img3" in k), None)
    assert img1 == "https://example.com/a.png", f"img1 bad: {img1}"
    assert img2 == "/uploads/foo.png", f"img2 bad: {img2}"
    assert img3 == "", f"img3 bad (garbage should be empty): {img3}"


# ---------- Admin list endpoint ----------
def test_admin_list_requires_admin(student_headers):
    r = requests.get(f"{API}/questions/admin/list", headers=student_headers, timeout=30)
    assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text}"


def test_admin_list_filters_and_search(admin_headers):
    r = requests.get(
        f"{API}/questions/admin/list",
        params={"exam_type": "JEE_Main", "subject": "Physics", "limit": 30, "page": 1},
        headers=admin_headers,
        timeout=30,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert "total" in j and "pages" in j and "questions" in j
    assert j["limit"] == 30
    # all returned rows should match filter
    for q in j["questions"]:
        assert q.get("exam_type") == "JEE_Main"
        assert q.get("subject") == "Physics"

    # q search
    r2 = requests.get(
        f"{API}/questions/admin/list",
        params={"q": "TEST_iter13"},
        headers=admin_headers,
        timeout=30,
    )
    assert r2.status_code == 200
    assert r2.json()["total"] >= 1


# ---------- Admin delete + live sync to student ----------
def test_admin_delete_and_live_sync(admin_headers, student_headers):
    tag = uuid.uuid4().hex[:8]
    q_text = f"TEST_iter13 {tag} DeleteMeQ?"
    row = (f"JEE_Main,Physics,Gravitation,Orbit,2022,Easy,"
           f"{q_text},,A,B,C,D,A,4,-1,,0")
    csv_body = "\n".join([CSV_HEADER, row]) + "\n"
    r = requests.post(
        f"{API}/questions/bulk-import/csv",
        data=csv_body.encode("utf-8"),
        headers={**admin_headers, "Content-Type": "text/csv"},
        timeout=60,
    )
    assert r.status_code == 200 and r.json()["inserted"] == 1

    # locate question_id
    lr = requests.get(f"{API}/questions/admin/list",
                      params={"q": q_text[:30]}, headers=admin_headers, timeout=30)
    assert lr.status_code == 200
    rows = lr.json()["questions"]
    target = next((q for q in rows if q["question_text"] == q_text), None)
    assert target, f"didn't find just-inserted question. rows={rows}"
    qid = target["question_id"]

    # student GET sees some physics total
    sg = requests.get(f"{API}/questions/", params={"subject": "Physics"},
                      headers=student_headers, timeout=30)
    assert sg.status_code == 200
    before_total = sg.json()["total"]

    # delete
    d = requests.delete(f"{API}/questions/admin/{qid}", headers=admin_headers, timeout=30)
    assert d.status_code == 200, d.text
    assert d.json()["success"] is True

    # student re-fetch: total should decrease by 1
    sg2 = requests.get(f"{API}/questions/", params={"subject": "Physics"},
                       headers=student_headers, timeout=30)
    assert sg2.status_code == 200
    after_total = sg2.json()["total"]
    assert after_total == before_total - 1, f"live sync failed before={before_total} after={after_total}"

    # admin delete of unknown -> 404
    d2 = requests.delete(f"{API}/questions/admin/q_does_not_exist_xyz",
                         headers=admin_headers, timeout=30)
    assert d2.status_code == 404


def test_admin_delete_non_admin_403(student_headers):
    r = requests.delete(f"{API}/questions/admin/q_any_id",
                        headers=student_headers, timeout=30)
    assert r.status_code == 403


# ---------- CSV non-admin 403 ----------
def test_bulk_import_csv_non_admin_403(student_headers):
    r = requests.post(
        f"{API}/questions/bulk-import/csv",
        data=CSV_HEADER.encode("utf-8"),
        headers={**student_headers, "Content-Type": "text/csv"},
        timeout=30,
    )
    assert r.status_code == 403


# ---------- Regression: stats + syllabus + student questions base ----------
def test_stats_public():
    r = requests.get(f"{API}/questions/stats", timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert "total" in j


def test_student_questions_default_listing(student_headers):
    r = requests.get(f"{API}/questions/", headers=student_headers, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert "total" in j and "questions" in j


# ---------- Cleanup fixture: delete TEST_iter13 rows at end ----------
@pytest.fixture(scope="module", autouse=True)
def _cleanup_after(admin_token):
    yield
    headers = {"Authorization": f"Bearer {admin_token}"}
    try:
        lr = requests.get(f"{API}/questions/admin/list",
                          params={"q": "TEST_iter13", "limit": 200},
                          headers=headers, timeout=30)
        if lr.status_code == 200:
            for q in lr.json().get("questions", []):
                requests.delete(f"{API}/questions/admin/{q['question_id']}",
                                headers=headers, timeout=15)
    except Exception:
        pass
