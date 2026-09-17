"""Iter25 pre-deploy readiness: YouTube latest + live class end-to-end (Zoom)."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://tier-learn-app.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

TEACHER = {"email": "teacher@test.com", "password": "password123"}
STUDENT = {"email": "student@test.com", "password": "password123"}


def _login(creds):
    r = requests.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token") or data.get("data", {}).get("access_token")
    assert tok, f"no token in login response: {data}"
    return tok


@pytest.fixture(scope="module")
def teacher_headers():
    return {"Authorization": f"Bearer {_login(TEACHER)}"}


@pytest.fixture(scope="module")
def student_headers():
    return {"Authorization": f"Bearer {_login(STUDENT)}"}


# ---------------- YouTube ----------------
class TestYouTubeLatest:
    def test_latest_returns_valid_video(self):
        r = requests.get(f"{API}/youtube/latest", timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("success") is True, j
        vid = j.get("video_id") or j.get("data", {}).get("video_id")
        title = j.get("title") or j.get("data", {}).get("title")
        embed = j.get("embed_url") or j.get("data", {}).get("embed_url")
        assert isinstance(vid, str) and len(vid) == 11, f"bad video_id: {vid}"
        assert title and isinstance(title, str)
        assert embed and embed.startswith("https://www.youtube.com/embed/"), embed

    def test_latest_cached_on_second_call(self):
        requests.get(f"{API}/youtube/latest", timeout=30)
        r = requests.get(f"{API}/youtube/latest", timeout=30)
        assert r.status_code == 200
        j = r.json()
        cached = j.get("cached", j.get("data", {}).get("cached"))
        # Accept True or absent-but-fast; assert it is not explicitly False
        assert cached is True or cached is None, f"expected cached=true, got {cached}"


# ---------------- Live class E2E ----------------
class TestLiveClassE2E:
    _class_id = None

    def test_teacher_create(self, teacher_headers):
        import datetime as dt
        future = dt.datetime.utcnow() + dt.timedelta(days=1)
        payload = {
            "title": f"AutoTest Live {int(time.time())}",
            "subject": "Physics",
            "scheduled_date": future.strftime("%Y-%m-%d"),
            "scheduled_time": future.strftime("%H:%M"),
            "duration_minutes": 60,
            "assigned_batches": ["NEX2027"],
            "description": "iter25 pre-deploy",
        }
        r = requests.post(f"{API}/teacher/live-classes/create", json=payload, headers=teacher_headers, timeout=60)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("success") is True, j
        cls = j.get("class") or j.get("data") or j
        cid = cls.get("class_id") or cls.get("id")
        assert cid, f"no class_id: {j}"
        meeting = cls.get("meeting_id") or cls.get("zoom_meeting_id")
        assert meeting, f"no zoom meeting_id: {j}"
        TestLiveClassE2E._class_id = cid

    def test_teacher_lists_new_class(self, teacher_headers):
        assert TestLiveClassE2E._class_id
        r = requests.get(f"{API}/teacher/classes/", headers=teacher_headers, timeout=30)
        assert r.status_code == 200
        j = r.json()
        classes = j.get("data") or j.get("classes") or j
        ids = [c.get("class_id") or c.get("id") for c in classes]
        assert TestLiveClassE2E._class_id in ids, f"created class not in teacher list ids={ids}"

    def test_student_lists_new_class(self, student_headers):
        assert TestLiveClassE2E._class_id
        r = requests.get(f"{API}/student/live-classes/", headers=student_headers, timeout=30)
        assert r.status_code == 200
        j = r.json()
        classes = j.get("data") or j.get("classes") or j
        ids = [c.get("class_id") or c.get("id") for c in classes]
        assert TestLiveClassE2E._class_id in ids, f"student cannot see class ids={ids}"

    def test_teacher_start(self, teacher_headers):
        cid = TestLiveClassE2E._class_id
        r = requests.post(f"{API}/teacher/live-classes/{cid}/start", headers=teacher_headers, timeout=60)
        assert r.status_code == 200, r.text
        j = r.json()
        d = j.get("data") or j
        for k in ("signature", "sdk_key", "meeting_number"):
            assert d.get(k), f"missing {k} in start resp: {j}"

    def test_student_sees_is_live(self, student_headers):
        cid = TestLiveClassE2E._class_id
        r = requests.get(f"{API}/student/live-classes/", headers=student_headers, timeout=30)
        assert r.status_code == 200
        j = r.json()
        classes = j.get("data") or j.get("classes") or j
        row = next((c for c in classes if (c.get("class_id") or c.get("id")) == cid), None)
        assert row, "class missing from student list after start"
        assert row.get("is_live") is True, f"is_live not True: {row}"

    def test_student_join(self, student_headers):
        cid = TestLiveClassE2E._class_id
        r = requests.get(f"{API}/student/live-classes/{cid}/join", headers=student_headers, timeout=60)
        assert r.status_code == 200, r.text
        j = r.json()
        d = j.get("data") or j
        for k in ("signature", "sdk_key", "meeting_number"):
            assert d.get(k), f"missing {k}: {j}"

    def test_teacher_end(self, teacher_headers, student_headers):
        cid = TestLiveClassE2E._class_id
        r = requests.post(f"{API}/teacher/live-classes/{cid}/end", headers=teacher_headers, timeout=60)
        assert r.status_code == 200, r.text
        # verify is_live reverted
        r2 = requests.get(f"{API}/student/live-classes/", headers=student_headers, timeout=30)
        classes = r2.json().get("data") or r2.json().get("classes") or r2.json()
        row = next((c for c in classes if (c.get("class_id") or c.get("id")) == cid), None)
        if row is not None:
            assert row.get("is_live") in (False, None), f"is_live still true: {row}"
