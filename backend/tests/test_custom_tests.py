"""
Test Custom Test Builder APIs
- POST /api/custom-tests/generate - Generate custom test
- GET /api/custom-tests/{test_id}/questions - Get test questions  
- POST /api/custom-tests/{test_id}/submit - Submit test and get results
- GET /api/custom-tests/syllabus - Get syllabus structure
- GET /api/custom-tests/question-counts - Get question counts by topic
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

class TestCustomTestAPIs:
    """Custom Test Builder API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Login and get session cookie"""
        self.session = requests.Session()
        # Login to get auth cookie
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "student@test.com",
            "password": "password123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.cookies = self.session.cookies
        self.test_id = None
    
    def test_01_get_syllabus(self):
        """Test GET /api/custom-tests/syllabus returns syllabus structure"""
        response = self.session.get(f"{BASE_URL}/api/custom-tests/syllabus")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "Physics" in data
        assert "Chemistry" in data
        assert "Mathematics" in data
        
        # Verify each subject has Class11 and Class12
        for subject in ["Physics", "Chemistry", "Mathematics"]:
            assert "Class11" in data[subject]
            assert "Class12" in data[subject]
            # Should have chapters with topics
            chapters = data[subject]["Class11"] + data[subject]["Class12"]
            assert len(chapters) > 0, f"{subject} should have chapters"
            if chapters:
                assert "chapter" in chapters[0]
                assert "topics" in chapters[0]
                assert "questionCount" in chapters[0]
        
        print(f"Syllabus loaded with {len(data['Physics']['Class11'] + data['Physics']['Class12'])} Physics chapters")
    
    def test_02_get_question_counts(self):
        """Test GET /api/custom-tests/question-counts returns topic counts"""
        response = self.session.get(f"{BASE_URL}/api/custom-tests/question-counts")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a dict with topic counts
        assert isinstance(data, dict)
        assert len(data) > 0, "Should have question counts"
        
        # Counts should be positive integers
        for key, count in data.items():
            assert isinstance(count, int)
            assert count >= 0
        
        print(f"Question counts for {len(data)} topics")
    
    def test_03_get_question_counts_with_exam_type(self):
        """Test GET /api/custom-tests/question-counts with examType filter"""
        response = self.session.get(
            f"{BASE_URL}/api/custom-tests/question-counts",
            params={"examType": "JEE_Main"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        print(f"JEE Main question counts for {len(data)} topics")
    
    def test_04_generate_custom_test(self):
        """Test POST /api/custom-tests/generate creates a custom test"""
        payload = {
            "examType": "JEE_Main",
            "selectedTopics": [
                {
                    "subject": "Physics",
                    "chapter": "Units and Measurements",
                    "topic": "Units and Measurements",
                    "questionCount": 3,
                    "difficulty": "Mixed"
                },
                {
                    "subject": "Chemistry",
                    "chapter": "Chemical Bonding and Molecular Structure",
                    "topic": "Chemical Bonding and Molecular Structure",
                    "questionCount": 2,
                    "difficulty": "Mixed"
                }
            ],
            "yearRange": {"start": 2015, "end": 2025},
            "duration": 30,
            "totalQuestions": 5,
            "totalMarks": 20
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/custom-tests/generate",
            json=payload
        )
        
        assert response.status_code == 200, f"Generate test failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data["success"] == True
        assert "test_id" in data
        assert data["test_id"].startswith("test_")
        assert "total_questions" in data
        assert "total_marks" in data
        assert "duration" in data
        assert data["duration"] == 30
        assert "subject_breakdown" in data
        
        # Store test_id for later tests
        TestCustomTestAPIs.generated_test_id = data["test_id"]
        
        print(f"Generated test: {data['test_id']} with {data['total_questions']} questions")
    
    def test_05_get_test_details(self):
        """Test GET /api/custom-tests/{test_id} returns test details"""
        test_id = getattr(TestCustomTestAPIs, 'generated_test_id', None)
        if not test_id:
            pytest.skip("No test_id from previous test")
        
        response = self.session.get(f"{BASE_URL}/api/custom-tests/{test_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify test details
        assert data["test_id"] == test_id
        assert "test_name" in data
        assert "duration" in data
        assert "total_questions" in data
        assert "questions" in data
        assert len(data["questions"]) > 0
        
        # Correct answers should be removed for test-taking
        for q in data["questions"]:
            assert "correctAnswer" not in q, "correctAnswer should be removed for test-taking"
            assert "questionNumber" in q
            assert "questionText" in q
            assert "options" in q
            assert "subject" in q
        
        print(f"Test details loaded: {data['test_name']}")
    
    def test_06_get_test_questions(self):
        """Test GET /api/custom-tests/{test_id}/questions returns questions without answers"""
        test_id = getattr(TestCustomTestAPIs, 'generated_test_id', None)
        if not test_id:
            pytest.skip("No test_id from previous test")
        
        response = self.session.get(f"{BASE_URL}/api/custom-tests/{test_id}/questions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "questions" in data
        assert "duration" in data
        assert "total_questions" in data
        
        questions = data["questions"]
        assert len(questions) > 0
        
        # Verify question structure
        for q in questions:
            assert "questionNumber" in q
            assert "questionText" in q
            assert "correctAnswer" not in q, "correctAnswer should not be exposed"
        
        print(f"Got {len(questions)} questions for test")
    
    def test_07_submit_test(self):
        """Test POST /api/custom-tests/{test_id}/submit calculates results"""
        test_id = getattr(TestCustomTestAPIs, 'generated_test_id', None)
        if not test_id:
            pytest.skip("No test_id from previous test")
        
        # Submit with some answers (mix of correct/wrong)
        payload = {
            "answers": {
                "1": "A",
                "2": "B",
                "3": "C"
            },
            "timeSpent": 600  # 10 minutes
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/custom-tests/{test_id}/submit",
            json=payload
        )
        
        assert response.status_code == 200, f"Submit failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data["success"] == True
        assert "attempt_id" in data
        assert "results" in data
        
        results = data["results"]
        assert "correct" in results
        assert "incorrect" in results
        assert "unattempted" in results
        assert "totalMarks" in results
        assert "maxMarks" in results
        assert "percentage" in results
        assert "accuracy" in results
        assert "timeSpent" in results
        
        # Verify questionResults
        assert "questionResults" in data
        for qr in data["questionResults"]:
            assert "questionNumber" in qr
            assert "userAnswer" in qr
            assert "correctAnswer" in qr
            assert "marks" in qr
            assert "status" in qr
            assert qr["status"] in ["correct", "incorrect", "unattempted"]
        
        print(f"Test submitted: {results['correct']} correct, {results['incorrect']} incorrect, Score: {results['percentage']}%")
    
    def test_08_get_test_not_found(self):
        """Test GET /api/custom-tests/{test_id} returns 404 for invalid ID"""
        response = self.session.get(f"{BASE_URL}/api/custom-tests/invalid_test_id_123")
        assert response.status_code == 404
    
    def test_09_generate_test_no_questions_error(self):
        """Test POST /api/custom-tests/generate returns error if no questions found"""
        payload = {
            "examType": "JEE_Main",
            "selectedTopics": [
                {
                    "subject": "Physics",
                    "chapter": "NonExistentChapter12345",
                    "topic": "NonExistentTopic",
                    "questionCount": 5,
                    "difficulty": "Mixed"
                }
            ],
            "yearRange": {"start": 2020, "end": 2025},
            "duration": 30,
            "totalQuestions": 5,
            "totalMarks": 20
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/custom-tests/generate",
            json=payload
        )
        
        # Should return 400 with error message
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        print(f"Correct error: {data['detail']}")
    
    def test_10_generate_test_authentication_required(self):
        """Test POST /api/custom-tests/generate requires authentication"""
        # Create new session without auth
        session = requests.Session()
        
        payload = {
            "examType": "JEE_Main",
            "selectedTopics": [],
            "yearRange": {"start": 2020, "end": 2025},
            "duration": 30,
            "totalQuestions": 0,
            "totalMarks": 0
        }
        
        response = session.post(f"{BASE_URL}/api/custom-tests/generate", json=payload)
        assert response.status_code == 401


class TestTestTemplateAPIs:
    """Test Template CRUD API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Login and get session cookie"""
        self.session = requests.Session()
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "student@test.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
    
    def test_01_get_templates_empty_or_list(self):
        """Test GET /api/test-templates returns list"""
        response = self.session.get(f"{BASE_URL}/api/test-templates")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} templates")
    
    def test_02_create_template(self):
        """Test POST /api/test-templates creates a template"""
        payload = {
            "templateName": "TEST_My Physics Template",
            "examType": "JEE_Main",
            "selectedTopics": [
                {
                    "subject": "Physics",
                    "chapter": "Mechanics",
                    "topic": "Kinematics",
                    "questionCount": 10,
                    "difficulty": "Medium"
                }
            ],
            "yearRange": {"start": 2018, "end": 2024},
            "duration": 60,
            "totalQuestions": 10,
            "totalMarks": 40,
            "subjectBreakdown": {"Physics": {"questions": 10, "marks": 40}}
        }
        
        response = self.session.post(f"{BASE_URL}/api/test-templates", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "template" in data
        assert data["template"]["template_name"] == "TEST_My Physics Template"
        assert "template_id" in data["template"]
        
        TestTestTemplateAPIs.created_template_id = data["template"]["template_id"]
        print(f"Created template: {data['template']['template_id']}")
    
    def test_03_update_template(self):
        """Test PUT /api/test-templates/{template_id} updates template"""
        template_id = getattr(TestTestTemplateAPIs, 'created_template_id', None)
        if not template_id:
            pytest.skip("No template_id from previous test")
        
        response = self.session.put(
            f"{BASE_URL}/api/test-templates/{template_id}",
            json={"templateName": "TEST_Updated Physics Template", "isFavorite": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("Template updated successfully")
    
    def test_04_mark_template_used(self):
        """Test POST /api/test-templates/{template_id}/use increments usage"""
        template_id = getattr(TestTestTemplateAPIs, 'created_template_id', None)
        if not template_id:
            pytest.skip("No template_id from previous test")
        
        response = self.session.post(f"{BASE_URL}/api/test-templates/{template_id}/use")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("Template marked as used")
    
    def test_05_delete_template(self):
        """Test DELETE /api/test-templates/{template_id} removes template"""
        template_id = getattr(TestTestTemplateAPIs, 'created_template_id', None)
        if not template_id:
            pytest.skip("No template_id from previous test")
        
        response = self.session.delete(f"{BASE_URL}/api/test-templates/{template_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        print("Template deleted successfully")
    
    def test_06_delete_template_not_found(self):
        """Test DELETE /api/test-templates/{template_id} returns 404 for invalid ID"""
        response = self.session.delete(f"{BASE_URL}/api/test-templates/invalid_template_123")
        assert response.status_code == 404
    
    def test_07_create_template_auth_required(self):
        """Test POST /api/test-templates requires authentication"""
        session = requests.Session()  # No auth
        
        payload = {
            "templateName": "Test",
            "examType": "JEE_Main",
            "selectedTopics": [],
            "yearRange": {"start": 2020, "end": 2025},
            "duration": 30,
            "totalQuestions": 0,
            "totalMarks": 0
        }
        
        response = session.post(f"{BASE_URL}/api/test-templates", json=payload)
        assert response.status_code == 401
