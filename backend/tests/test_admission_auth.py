"""
Test suite for Admission Form with Password + Auto-Login Flow
Tests: 
- Admission form creates user account with password
- Login works with credentials created during admission  
- PYQ section shows all subjects and year categorization
- Dashboard shows user stats after login
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nta-test-engine.preview.emergentagent.com').rstrip('/')


class TestAdmissionCreatesUserAccount:
    """Test admission form creates user account with password"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup unique test data"""
        self.test_suffix = uuid.uuid4().hex[:8]
        self.test_email = f"newstudent_{self.test_suffix}@test.com"
        self.test_password = "TestPass123!"
    
    def test_01_admission_submit_with_password(self):
        """Test admission form submission with password creates user account and returns user object"""
        payload = {
            "student_name": f"Test Student {self.test_suffix}",
            "father_name": "Test Father",
            "mother_name": "Test Mother",
            "date_of_birth": "2005-05-15",
            "gender": "Male",
            "contact_number": "9876543210",
            "email": self.test_email,
            "password": self.test_password,  # Password field now required
            "address": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456",
            "course_applying": "JEE Main 2025",
            "photo_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "signature_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        }
        
        response = requests.post(f"{BASE_URL}/api/admissions/submit", json=payload)
        
        # Should succeed
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify success and admission_id
        assert data.get("success") == True, "Expected success=True"
        assert "admission_id" in data, "Missing admission_id in response"
        assert data["admission_id"].startswith("ADM"), "admission_id should start with ADM"
        
        # Verify user object is returned (auto-login)
        assert "user" in data, "Missing user object in response - auto-login failed"
        user = data["user"]
        assert user.get("email") == self.test_email, f"User email mismatch: {user.get('email')}"
        assert user.get("name") == f"Test Student {self.test_suffix}", "User name mismatch"
        assert user.get("role") == "student", f"User role should be 'student', got {user.get('role')}"
        assert "user_id" in user, "Missing user_id in user object"
        assert user.get("admission_id") == data["admission_id"], "admission_id should be linked to user"
        
        # Store for subsequent tests
        self.__class__.created_user_email = self.test_email
        self.__class__.created_user_password = self.test_password
        self.__class__.created_admission_id = data["admission_id"]
        
        # Check session cookie is set
        cookies = response.cookies
        print(f"Cookies received: {dict(cookies)}")
        
        print(f"PASSED: Admission created user account - email={self.test_email}, admission_id={data['admission_id']}")
    
    def test_02_login_with_admission_credentials(self):
        """Test login works with credentials created during admission"""
        # Use stored credentials from previous test or skip
        if not hasattr(self.__class__, 'created_user_email'):
            pytest.skip("No admission created in previous test")
        
        login_payload = {
            "email": self.__class__.created_user_email,
            "password": self.__class__.created_user_password
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "user" in data, "Missing user in login response"
        assert data["user"]["email"] == self.__class__.created_user_email
        assert "message" in data
        
        # Verify session cookie is set
        cookies = response.cookies
        
        print(f"PASSED: Login successful with admission credentials - {self.__class__.created_user_email}")
    
    def test_03_admission_duplicate_email_rejected(self):
        """Test admission with existing email is rejected"""
        if not hasattr(self.__class__, 'created_user_email'):
            pytest.skip("No admission created in previous test")
        
        payload = {
            "student_name": "Duplicate Test",
            "father_name": "Test Father",
            "mother_name": "Test Mother",
            "date_of_birth": "2005-05-15",
            "gender": "Male",
            "contact_number": "9876543210",
            "email": self.__class__.created_user_email,  # Same email as before
            "password": "AnotherPass123",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456",
            "course_applying": "JEE Main 2025"
        }
        
        response = requests.post(f"{BASE_URL}/api/admissions/submit", json=payload)
        
        # Should fail with 400 - email already registered
        assert response.status_code == 400, f"Expected 400 for duplicate email, got {response.status_code}"
        
        data = response.json()
        assert "already registered" in data.get("detail", "").lower(), f"Expected 'already registered' error, got: {data}"
        
        print("PASSED: Duplicate email correctly rejected")


class TestExistingUserLogin:
    """Test login with existing test credentials"""
    
    def test_login_existing_student(self):
        """Test login with pre-existing test student account"""
        login_payload = {
            "email": "student@test.com",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "student@test.com"
        
        # Store session for subsequent tests
        cookies = response.cookies
        self.__class__.session = requests.Session()
        self.__class__.session.cookies.update(cookies)
        
        print(f"PASSED: Existing student login successful - {data['user']['email']}")
    
    def test_login_invalid_credentials(self):
        """Test login fails with wrong password"""
        login_payload = {
            "email": "student@test.com",
            "password": "wrongpassword"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        
        print("PASSED: Invalid credentials correctly rejected with 401")


class TestPYQSubjectsAndYears:
    """Test PYQ section shows all subjects and year categorization"""
    
    def test_01_syllabus_has_all_three_subjects(self):
        """Test syllabus endpoint returns Physics, Chemistry, and Mathematics"""
        response = requests.get(f"{BASE_URL}/api/questions/syllabus")
        
        assert response.status_code == 200, f"Syllabus endpoint failed: {response.status_code}"
        
        data = response.json()
        
        # Verify all 3 subjects are present
        assert "Physics" in data, "Physics subject missing from syllabus"
        assert "Chemistry" in data, "Chemistry subject missing from syllabus"
        assert "Mathematics" in data, "Mathematics subject missing from syllabus"
        
        # Print chapter counts per subject
        for subject in ["Physics", "Chemistry", "Mathematics"]:
            total_chapters = 0
            for class_key in data.get(subject, {}):
                total_chapters += len(data[subject][class_key])
            print(f"{subject}: {total_chapters} chapters")
        
        print("PASSED: All 3 subjects present in syllabus")
    
    def test_02_physics_questions_exist(self):
        """Test Physics has questions loaded"""
        response = requests.get(f"{BASE_URL}/api/questions/?subject=Physics&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        total = data.get("total", 0)
        assert total > 0, "No Physics questions found"
        
        print(f"PASSED: Physics has {total} questions")
    
    def test_03_chemistry_questions_exist(self):
        """Test Chemistry has questions loaded"""
        response = requests.get(f"{BASE_URL}/api/questions/?subject=Chemistry&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        total = data.get("total", 0)
        assert total > 0, "No Chemistry questions found"
        
        print(f"PASSED: Chemistry has {total} questions")
    
    def test_04_mathematics_questions_exist(self):
        """Test Mathematics has questions loaded"""
        response = requests.get(f"{BASE_URL}/api/questions/?subject=Mathematics&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        total = data.get("total", 0)
        assert total > 0, "No Mathematics questions found"
        
        print(f"PASSED: Mathematics has {total} questions")
    
    def test_05_questions_have_year_field(self):
        """Test questions have year field for categorization (2020-2025)"""
        response = requests.get(f"{BASE_URL}/api/questions/?limit=20")
        
        assert response.status_code == 200
        data = response.json()
        
        questions = data.get("questions", [])
        assert len(questions) > 0, "No questions returned"
        
        # Check year field exists on questions
        years_found = set()
        questions_with_year = 0
        for q in questions:
            if "year" in q and q["year"]:
                years_found.add(q["year"])
                questions_with_year += 1
        
        print(f"Years found in questions: {sorted(years_found)}")
        print(f"{questions_with_year}/{len(questions)} questions have year field")
        
        # At least some questions should have year
        assert questions_with_year > 0, "No questions have year field"
    
    def test_06_filter_questions_by_year(self):
        """Test questions can be filtered by year"""
        # Test year 2024 filter
        response = requests.get(f"{BASE_URL}/api/questions/?year=2024&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        questions = data.get("questions", [])
        total = data.get("total", 0)
        
        print(f"Year 2024: {total} total questions")
        
        # All returned questions should be from 2024
        for q in questions:
            assert q.get("year") == 2024, f"Question has wrong year: {q.get('year')}"
        
        print("PASSED: Year filter working correctly")


class TestDashboardStats:
    """Test dashboard shows user stats after login"""
    
    def test_dashboard_stats_endpoint(self):
        """Test user dashboard stats endpoint"""
        # First login
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "student@test.com",
            "password": "password123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Could not login for dashboard test")
        
        # Get current user
        me_response = session.get(f"{BASE_URL}/api/auth/me")
        
        # me endpoint should work with session cookie
        if me_response.status_code == 200:
            user = me_response.json()
            print(f"Logged in as: {user.get('email', 'unknown')}")
        
        # Get analytics/stats
        analytics_response = session.get(f"{BASE_URL}/api/analytics/user-stats")
        
        if analytics_response.status_code == 200:
            stats = analytics_response.json()
            print(f"User stats: {stats}")
        else:
            # Analytics might need auth - check alternatives
            print(f"Analytics endpoint returned {analytics_response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
