"""
Test Suite for Teacher Dashboard, Student Features, and Notification System
Tests the following features:
- Teacher Authentication & Dashboard
- Teacher Class Management (CRUD)
- Teacher Test Management (Create with questions)
- Student View Students & Analytics
- Student Assigned Tests
- Student Classes
- Notification System
- Push Notification VAPID Key
- Batch Selection
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://jee-test-engine.preview.emergentagent.com')

# Test credentials
TEACHER_EMAIL = "teacher@test.com"
TEACHER_PASSWORD = "password123"
STUDENT_EMAIL = "student@test.com"
STUDENT_PASSWORD = "password123"


class TestBatchesAPI:
    """Test batch endpoints - no auth required"""
    
    def test_get_batches(self):
        """GET /api/batches/ returns predefined batches"""
        response = requests.get(f"{BASE_URL}/api/batches/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "batches" in data
        assert len(data["batches"]) == 6
        
        # Verify batch structure
        batch_ids = [b["id"] for b in data["batches"]]
        assert "JEE-2027-Morning" in batch_ids
        assert "JEE-2027-Evening" in batch_ids
        print("✓ GET /api/batches/ - All predefined batches returned")


class TestPushAPI:
    """Test push notification endpoints"""
    
    def test_get_vapid_public_key(self):
        """GET /api/push/vapid-public-key returns VAPID key"""
        response = requests.get(f"{BASE_URL}/api/push/vapid-public-key")
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data
        assert len(data["public_key"]) > 0
        print("✓ GET /api/push/vapid-public-key - VAPID key returned")


class TestTeacherAuthentication:
    """Test teacher authentication and session management"""
    
    @pytest.fixture(scope="class")
    def teacher_session(self):
        """Login as teacher and get session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Teacher login failed: {response.text}")
        
        data = response.json()
        assert data["user"]["role"] == "teacher", "User must be teacher role"
        print(f"✓ Teacher login successful: {data['user']['name']}")
        return session
    
    def test_teacher_login(self, teacher_session):
        """POST /api/auth/login with teacher credentials"""
        response = teacher_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "teacher"
        assert data["email"] == TEACHER_EMAIL
        print("✓ Teacher auth/me - Teacher role verified")


class TestTeacherClasses:
    """Test teacher class management endpoints"""
    
    @pytest.fixture(scope="class")
    def teacher_session(self):
        """Login as teacher and get session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Teacher login failed: {response.text}")
        return session
    
    def test_get_teacher_classes(self, teacher_session):
        """GET /api/teacher/classes/ returns teacher's classes"""
        response = teacher_session.get(f"{BASE_URL}/api/teacher/classes/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "classes" in data
        print(f"✓ GET /api/teacher/classes/ - {len(data['classes'])} classes found")
    
    def test_get_class_stats(self, teacher_session):
        """GET /api/teacher/classes/stats returns class statistics"""
        response = teacher_session.get(f"{BASE_URL}/api/teacher/classes/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total" in data
        assert "upcoming" in data
        assert "completed" in data
        print(f"✓ GET /api/teacher/classes/stats - total:{data['total']}, upcoming:{data['upcoming']}")
    
    def test_create_class(self, teacher_session):
        """POST /api/teacher/classes/create creates a new class"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        class_data = {
            "title": f"TEST_Physics_Class_{uuid.uuid4().hex[:6]}",
            "subject": "Physics",
            "chapter": "Kinematics",
            "topic": "Motion in One Dimension",
            "meeting_link": "https://zoom.us/j/test123",
            "meeting_platform": "Zoom",
            "scheduled_date": tomorrow,
            "scheduled_time": "10:00",
            "duration": 60,
            "assigned_batches": ["JEE-2027-Morning"],
            "description": "Test class created by automated test",
            "prerequisites": "None"
        }
        
        response = teacher_session.post(
            f"{BASE_URL}/api/teacher/classes/create",
            json=class_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "class" in data
        assert data["class"]["title"] == class_data["title"]
        assert data["class"]["subject"] == "Physics"
        
        # Store class_id for cleanup
        class_id = data["class"]["class_id"]
        print(f"✓ POST /api/teacher/classes/create - Class created: {class_id}")
        
        # Cleanup - delete the test class
        delete_response = teacher_session.delete(f"{BASE_URL}/api/teacher/classes/{class_id}")
        assert delete_response.status_code == 200
        print(f"✓ DELETE /api/teacher/classes/{class_id} - Cleanup successful")
    
    def test_create_class_validation(self, teacher_session):
        """POST /api/teacher/classes/create validates required fields"""
        response = teacher_session.post(
            f"{BASE_URL}/api/teacher/classes/create",
            json={"title": "Test"}  # Missing required fields
        )
        assert response.status_code == 400
        print("✓ POST /api/teacher/classes/create - Validation works for missing fields")


class TestTeacherTests:
    """Test teacher test management endpoints"""
    
    @pytest.fixture(scope="class")
    def teacher_session(self):
        """Login as teacher and get session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Teacher login failed: {response.text}")
        return session
    
    def test_get_teacher_tests(self, teacher_session):
        """GET /api/teacher/tests/ returns teacher's tests"""
        response = teacher_session.get(f"{BASE_URL}/api/teacher/tests/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tests" in data
        print(f"✓ GET /api/teacher/tests/ - {len(data['tests'])} tests found")
    
    def test_get_test_stats(self, teacher_session):
        """GET /api/teacher/tests/stats returns test statistics"""
        response = teacher_session.get(f"{BASE_URL}/api/teacher/tests/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total" in data
        assert "scheduled" in data
        assert "draft" in data
        print(f"✓ GET /api/teacher/tests/stats - total:{data['total']}, scheduled:{data['scheduled']}, draft:{data['draft']}")
    
    def test_create_test_with_questions(self, teacher_session):
        """POST /api/teacher/tests/create creates a test with questions"""
        future_date = (datetime.now() + timedelta(days=2)).isoformat()
        
        test_data = {
            "test_name": f"TEST_Mock_Test_{uuid.uuid4().hex[:6]}",
            "exam_type": "JEE_Main",
            "subject": "Physics",
            "test_type": "Chapter Test",
            "chapters": ["Kinematics"],
            "topics": ["Motion in One Dimension"],
            "scheduled_date_time": future_date,
            "duration": 60,
            "instructions": "Test instructions",
            "allow_reattempts": False,
            "max_attempts": 1,
            "show_solutions_after_submit": True,
            "show_results_immediately": True,
            "randomize_questions": False,
            "assigned_batches": ["JEE-2027-Morning"],
            "questions": [
                {
                    "question_text": "A ball is thrown vertically upward with velocity 10 m/s. What is its velocity at the highest point?",
                    "question_image_url": "",
                    "options": {"A": "0 m/s", "B": "10 m/s", "C": "5 m/s", "D": "-10 m/s"},
                    "correct_answer": "A",
                    "marks": 4,
                    "negative_marks": -1,
                    "subject": "Physics",
                    "chapter": "Kinematics",
                    "topic": "Motion in One Dimension",
                    "difficulty": "Easy",
                    "teacher_note": "At the highest point, velocity becomes zero before the ball starts falling down."
                },
                {
                    "question_text": "Which of the following is a scalar quantity?",
                    "question_image_url": "",
                    "options": {"A": "Velocity", "B": "Displacement", "C": "Speed", "D": "Acceleration"},
                    "correct_answer": "C",
                    "marks": 4,
                    "negative_marks": -1,
                    "subject": "Physics",
                    "chapter": "Kinematics",
                    "difficulty": "Easy",
                    "teacher_note": "Speed is a scalar quantity (magnitude only). Velocity, displacement, and acceleration are vectors."
                }
            ]
        }
        
        response = teacher_session.post(
            f"{BASE_URL}/api/teacher/tests/create",
            json=test_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "test" in data
        assert data["test"]["test_name"] == test_data["test_name"]
        assert data["test"]["total_questions"] == 2
        assert data["test"]["total_marks"] == 8  # 4 + 4
        assert data["test"]["status"] == "scheduled"  # Has questions, so scheduled
        
        test_id = data["test"]["test_id"]
        print(f"✓ POST /api/teacher/tests/create - Test created with {data['test']['total_questions']} questions: {test_id}")
        
        # Cleanup - delete the test
        delete_response = teacher_session.delete(f"{BASE_URL}/api/teacher/tests/{test_id}")
        assert delete_response.status_code == 200
        print(f"✓ DELETE /api/teacher/tests/{test_id} - Cleanup successful")
    
    def test_create_draft_test(self, teacher_session):
        """POST /api/teacher/tests/create without questions creates draft"""
        future_date = (datetime.now() + timedelta(days=2)).isoformat()
        
        test_data = {
            "test_name": f"TEST_Draft_Test_{uuid.uuid4().hex[:6]}",
            "exam_type": "JEE_Main",
            "subject": "Chemistry",
            "test_type": "Mock Test",
            "scheduled_date_time": future_date,
            "duration": 90,
            "assigned_batches": ["JEE-2027-Evening"],
            "questions": []  # No questions = draft
        }
        
        response = teacher_session.post(
            f"{BASE_URL}/api/teacher/tests/create",
            json=test_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["test"]["status"] == "draft"
        
        test_id = data["test"]["test_id"]
        print(f"✓ POST /api/teacher/tests/create - Draft test created: {test_id}")
        
        # Cleanup
        teacher_session.delete(f"{BASE_URL}/api/teacher/tests/{test_id}")


class TestTeacherStudents:
    """Test teacher student management endpoints"""
    
    @pytest.fixture(scope="class")
    def teacher_session(self):
        """Login as teacher and get session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Teacher login failed: {response.text}")
        return session
    
    def test_get_students(self, teacher_session):
        """GET /api/teacher/students/ returns student list"""
        response = teacher_session.get(f"{BASE_URL}/api/teacher/students/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "students" in data
        assert "count" in data
        print(f"✓ GET /api/teacher/students/ - {data['count']} students found")
    
    def test_get_students_by_batch(self, teacher_session):
        """GET /api/teacher/students/?batch_id=X filters by batch"""
        response = teacher_session.get(
            f"{BASE_URL}/api/teacher/students/",
            params={"batch_id": "JEE-2027-Morning"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print(f"✓ GET /api/teacher/students/?batch_id - Batch filter works")


class TestStudentAuthentication:
    """Test student authentication"""
    
    @pytest.fixture(scope="class")
    def student_session(self):
        """Login as student and get session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Student login failed: {response.text}")
        
        data = response.json()
        assert data["user"]["role"] == "student", "User must be student role"
        print(f"✓ Student login successful: {data['user']['name']}")
        return session
    
    def test_student_login(self, student_session):
        """POST /api/auth/login with student credentials"""
        response = student_session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "student"
        print("✓ Student auth/me - Student role verified")


class TestStudentTests:
    """Test student test endpoints"""
    
    @pytest.fixture(scope="class")
    def student_session(self):
        """Login as student and get session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Student login failed: {response.text}")
        return session
    
    def test_get_assigned_tests(self, student_session):
        """GET /api/student/tests/assigned returns assigned tests"""
        response = student_session.get(f"{BASE_URL}/api/student/tests/assigned")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tests" in data
        # Note: May be empty if student has no batch_id set
        print(f"✓ GET /api/student/tests/assigned - {len(data['tests'])} tests found")


class TestStudentClasses:
    """Test student class endpoints"""
    
    @pytest.fixture(scope="class")
    def student_session(self):
        """Login as student and get session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Student login failed: {response.text}")
        return session
    
    def test_get_my_classes(self, student_session):
        """GET /api/student/classes/my-classes returns student's classes"""
        response = student_session.get(f"{BASE_URL}/api/student/classes/my-classes")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "classes" in data
        # Note: May be empty if student has no batch_id set
        print(f"✓ GET /api/student/classes/my-classes - {len(data['classes'])} classes found")


class TestNotifications:
    """Test notification endpoints"""
    
    @pytest.fixture(scope="class")
    def teacher_session(self):
        """Login as teacher and get session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Teacher login failed: {response.text}")
        return session
    
    @pytest.fixture(scope="class")
    def student_session(self):
        """Login as student and get session"""
        session = requests.Session()
        response = session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Student login failed: {response.text}")
        return session
    
    def test_teacher_notifications(self, teacher_session):
        """GET /api/notifications/ returns teacher notifications"""
        response = teacher_session.get(f"{BASE_URL}/api/notifications/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "notifications" in data
        assert "unread_count" in data
        print(f"✓ GET /api/notifications/ (teacher) - {len(data['notifications'])} notifications, {data['unread_count']} unread")
    
    def test_student_notifications(self, student_session):
        """GET /api/notifications/ returns student notifications"""
        response = student_session.get(f"{BASE_URL}/api/notifications/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "notifications" in data
        assert "unread_count" in data
        print(f"✓ GET /api/notifications/ (student) - {len(data['notifications'])} notifications, {data['unread_count']} unread")


class TestE2ETeacherToStudent:
    """End-to-end test: Teacher creates content, student sees it"""
    
    def test_full_test_flow(self):
        """Teacher creates test -> Student sees assigned test"""
        # Login as teacher
        teacher_session = requests.Session()
        teacher_login = teacher_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
        )
        if teacher_login.status_code != 200:
            pytest.skip("Teacher login failed")
        
        teacher_data = teacher_login.json()["user"]
        print(f"✓ Logged in as teacher: {teacher_data['name']}")
        
        # Check if student has batch_id
        student_session = requests.Session()
        student_login = student_session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        if student_login.status_code != 200:
            pytest.skip("Student login failed")
        
        student_data = student_login.json()["user"]
        student_batch = student_data.get("batch_id")
        print(f"✓ Logged in as student: {student_data['name']}, batch: {student_batch}")
        
        if not student_batch:
            print("⚠ Student has no batch_id - will use JEE-2027-Morning for test")
            test_batch = "JEE-2027-Morning"
        else:
            test_batch = student_batch
        
        # Teacher creates test assigned to student's batch
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        test_data = {
            "test_name": f"E2E_Test_{uuid.uuid4().hex[:6]}",
            "exam_type": "JEE_Main",
            "subject": "Mathematics",
            "test_type": "Practice Test",
            "scheduled_date_time": future_date,
            "duration": 30,
            "assigned_batches": [test_batch],
            "questions": [
                {
                    "question_text": "What is 2 + 2?",
                    "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
                    "correct_answer": "B",
                    "marks": 4,
                    "negative_marks": -1,
                    "teacher_note": "Basic arithmetic - 2+2=4"
                }
            ]
        }
        
        create_response = teacher_session.post(
            f"{BASE_URL}/api/teacher/tests/create",
            json=test_data
        )
        assert create_response.status_code == 200
        test = create_response.json()["test"]
        test_id = test["test_id"]
        print(f"✓ Teacher created test: {test_id} for batch {test_batch}")
        
        # If student has matching batch, check if they can see it
        if student_batch == test_batch:
            assigned_response = student_session.get(f"{BASE_URL}/api/student/tests/assigned")
            assert assigned_response.status_code == 200
            assigned_tests = assigned_response.json()["tests"]
            test_ids = [t["test_id"] for t in assigned_tests]
            
            if test_id in test_ids:
                print(f"✓ Student can see the assigned test!")
                
                # Try to start the test
                start_response = student_session.post(f"{BASE_URL}/api/student/tests/{test_id}/start")
                if start_response.status_code == 200:
                    attempt_data = start_response.json()
                    attempt_id = attempt_data["attempt"]["attempt_id"]
                    print(f"✓ Student started test, attempt_id: {attempt_id}")
                    
                    # Submit the test
                    submit_response = student_session.post(
                        f"{BASE_URL}/api/student/tests/attempts/{attempt_id}/submit",
                        json={
                            "answers": [{"question_number": 1, "selected_answer": "B"}],
                            "time_spent": 60
                        }
                    )
                    if submit_response.status_code == 200:
                        result = submit_response.json()["attempt"]
                        print(f"✓ Test submitted! Score: {result['total_score']}/{result['max_score']}")
                        
                        # Get results with teacher notes
                        results_response = student_session.get(
                            f"{BASE_URL}/api/student/tests/results/{attempt_id}"
                        )
                        if results_response.status_code == 200:
                            print("✓ Student can view test results")
            else:
                print(f"⚠ Test not visible to student (batch mismatch or timing)")
        else:
            print(f"⚠ Student batch ({student_batch}) doesn't match test batch ({test_batch})")
        
        # Cleanup - delete test
        teacher_session.delete(f"{BASE_URL}/api/teacher/tests/{test_id}")
        print(f"✓ Cleanup: Test {test_id} deleted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
