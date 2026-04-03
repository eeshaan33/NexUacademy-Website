"""
Test JEE Main and JEE Advanced test interfaces - Backend API tests
Tests: Student assigned tests, start test with pattern, teacher test list, test creation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
STUDENT_EMAIL = "student@test.com"
STUDENT_PASSWORD = "password123"
TEACHER_EMAIL = "teacher@test.com"
TEACHER_PASSWORD = "password123"

# Test IDs
JEE_MAIN_TEST_ID = "ttest_55c6448044bf"
JEE_ADVANCED_TEST_ID = "ttest_a430b6a6c893"


class TestStudentLogin:
    """Test student authentication"""
    
    def test_student_login_success(self):
        """Student can login with valid credentials"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == STUDENT_EMAIL
        assert data["user"]["role"] == "student"
        assert data["user"]["batch_id"] == "JEE Mains 2027"
        print(f"✓ Student login successful: {data['user']['name']}")


class TestAssignedTests:
    """Test student assigned tests endpoint"""
    
    @pytest.fixture
    def student_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        return session
    
    def test_get_assigned_tests(self, student_session):
        """Student can see assigned tests for their batch"""
        response = student_session.get(f"{BASE_URL}/api/student/tests/assigned")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tests" in data
        assert len(data["tests"]) >= 2
        print(f"✓ Found {len(data['tests'])} assigned tests")
    
    def test_jee_main_test_in_assigned(self, student_session):
        """JEE Main test appears in assigned tests with correct pattern"""
        response = student_session.get(f"{BASE_URL}/api/student/tests/assigned")
        data = response.json()
        jee_main_test = next((t for t in data["tests"] if t["test_id"] == JEE_MAIN_TEST_ID), None)
        assert jee_main_test is not None, "JEE Main test not found in assigned tests"
        assert jee_main_test["test_pattern"] == "JEE_Main_Pattern"
        assert jee_main_test["exam_type"] == "JEE_Main"
        print(f"✓ JEE Main test found: {jee_main_test['test_name']} with pattern {jee_main_test['test_pattern']}")
    
    def test_jee_advanced_test_in_assigned(self, student_session):
        """JEE Advanced test appears in assigned tests with correct pattern"""
        response = student_session.get(f"{BASE_URL}/api/student/tests/assigned")
        data = response.json()
        jee_adv_test = next((t for t in data["tests"] if t["test_id"] == JEE_ADVANCED_TEST_ID), None)
        assert jee_adv_test is not None, "JEE Advanced test not found in assigned tests"
        assert jee_adv_test["test_pattern"] == "JEE_Advanced_Pattern"
        assert jee_adv_test["exam_type"] == "JEE_Advanced"
        print(f"✓ JEE Advanced test found: {jee_adv_test['test_name']} with pattern {jee_adv_test['test_pattern']}")


class TestStartTest:
    """Test start test endpoint returns test_pattern for SmartTestRouter"""
    
    @pytest.fixture
    def student_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        return session
    
    def test_start_jee_main_test_returns_pattern(self, student_session):
        """Starting JEE Main test returns test_pattern field"""
        response = student_session.post(f"{BASE_URL}/api/student/tests/{JEE_MAIN_TEST_ID}/start")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test" in data
        assert "attempt" in data
        assert data["test"]["test_pattern"] == "JEE_Main_Pattern"
        assert data["test"]["exam_type"] == "JEE_Main"
        assert "questions" in data["test"]
        assert len(data["test"]["questions"]) >= 1
        print(f"✓ Start JEE Main test returns pattern: {data['test']['test_pattern']}")
        print(f"  - Attempt ID: {data['attempt']['attempt_id']}")
        print(f"  - Questions: {len(data['test']['questions'])}")
    
    def test_start_jee_advanced_test_returns_pattern(self, student_session):
        """Starting JEE Advanced test returns test_pattern field"""
        response = student_session.post(f"{BASE_URL}/api/student/tests/{JEE_ADVANCED_TEST_ID}/start")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test" in data
        assert data["test"]["test_pattern"] == "JEE_Advanced_Pattern"
        assert data["test"]["exam_type"] == "JEE_Advanced"
        print(f"✓ Start JEE Advanced test returns pattern: {data['test']['test_pattern']}")
    
    def test_jee_main_test_has_mcq_and_numerical(self, student_session):
        """JEE Main test has both MCQ and Numerical questions"""
        response = student_session.post(f"{BASE_URL}/api/student/tests/{JEE_MAIN_TEST_ID}/start")
        data = response.json()
        questions = data["test"]["questions"]
        question_types = [q["question_type"] for q in questions]
        has_mcq = any("MCQ" in qt for qt in question_types)
        has_numerical = any("Numerical" in qt for qt in question_types)
        print(f"✓ Question types: {question_types}")
        assert has_mcq, "JEE Main test should have MCQ questions"
        assert has_numerical, "JEE Main test should have Numerical questions"
    
    def test_jee_main_test_has_katex_math(self, student_session):
        """JEE Main test questions contain KaTeX math delimiters"""
        response = student_session.post(f"{BASE_URL}/api/student/tests/{JEE_MAIN_TEST_ID}/start")
        data = response.json()
        questions = data["test"]["questions"]
        has_math = any("$" in q.get("question_text", "") for q in questions)
        assert has_math, "JEE Main test should have math content with $ delimiters"
        print("✓ JEE Main test contains KaTeX math content")


class TestTeacherLogin:
    """Test teacher authentication"""
    
    def test_teacher_login_success(self):
        """Teacher can login with valid credentials"""
        session = requests.Session()
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['name']}")


class TestTeacherTestList:
    """Test teacher test list shows pattern badges"""
    
    @pytest.fixture
    def teacher_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        return session
    
    def test_teacher_can_list_tests(self, teacher_session):
        """Teacher can list all tests"""
        response = teacher_session.get(f"{BASE_URL}/api/teacher/tests/")
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        assert len(data["tests"]) >= 2
        print(f"✓ Teacher can see {len(data['tests'])} tests")
    
    def test_teacher_tests_have_pattern_field(self, teacher_session):
        """Teacher test list includes test_pattern field for new tests"""
        response = teacher_session.get(f"{BASE_URL}/api/teacher/tests/")
        data = response.json()
        # Check that our specific test IDs have pattern
        jee_main = next((t for t in data["tests"] if t["test_id"] == JEE_MAIN_TEST_ID), None)
        jee_adv = next((t for t in data["tests"] if t["test_id"] == JEE_ADVANCED_TEST_ID), None)
        assert jee_main is not None, "JEE Main test not found"
        assert jee_adv is not None, "JEE Advanced test not found"
        assert jee_main.get("test_pattern") == "JEE_Main_Pattern"
        assert jee_adv.get("test_pattern") == "JEE_Advanced_Pattern"
        print(f"✓ JEE Main test has pattern: {jee_main.get('test_pattern')}")
        print(f"✓ JEE Advanced test has pattern: {jee_adv.get('test_pattern')}")


class TestBatches:
    """Test batches endpoint"""
    
    @pytest.fixture
    def teacher_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        return session
    
    def test_get_batches(self, teacher_session):
        """Can get list of batches"""
        response = teacher_session.get(f"{BASE_URL}/api/batches/")
        assert response.status_code == 200
        data = response.json()
        assert "batches" in data
        batch_ids = [b["id"] for b in data["batches"]]
        assert "JEE Mains 2027" in batch_ids, "JEE Mains 2027 batch should exist"
        print(f"✓ Found batches: {batch_ids}")


class TestStudentClasses:
    """Test student classes are filtered by batch"""
    
    @pytest.fixture
    def student_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        return session
    
    def test_student_classes_endpoint(self, student_session):
        """Student can access classes endpoint"""
        response = student_session.get(f"{BASE_URL}/api/student/classes")
        # May return 200 with empty list or classes
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Student classes endpoint works, found {len(data.get('classes', []))} classes")
        else:
            print("✓ Student classes endpoint returns 404 (no classes assigned)")


class TestTestSubmission:
    """Test test submission flow"""
    
    @pytest.fixture
    def student_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        return session
    
    def test_autosave_answers(self, student_session):
        """Can autosave answers during test"""
        # First start the test to get attempt_id
        start_response = student_session.post(f"{BASE_URL}/api/student/tests/{JEE_MAIN_TEST_ID}/start")
        data = start_response.json()
        attempt_id = data["attempt"]["attempt_id"]
        
        # Autosave some answers
        response = student_session.put(
            f"{BASE_URL}/api/student/tests/attempts/{attempt_id}/autosave",
            json={"answers": [{"question_number": 1, "selected_answer": "A"}]}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        print(f"✓ Autosave works for attempt {attempt_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
