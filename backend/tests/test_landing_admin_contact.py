"""
Test suite for Landing Page, Admin Login from Main Page, and Contact Form features
Tests:
- Contact form submission (POST /api/admin/contact) - public endpoint
- Admin login from main login page (POST /api/auth/login with admin@nexuacademy.com)
- Admin can view contacts (GET /api/admin/contacts)
- Admin can mark inquiry as responded (PUT /api/admin/contacts/{id}/status)
- Teacher login redirects to /teacher
- Student login redirects to /dashboard
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@nexuacademy.com"
ADMIN_PASSWORD = "nexuacademy123"
TEACHER_EMAIL = "teacher@test.com"
TEACHER_PASSWORD = "password123"
STUDENT_EMAIL = "student@test.com"
STUDENT_PASSWORD = "password123"


class TestContactFormAPI:
    """Test contact form submission - public endpoint, no auth needed"""
    
    def test_contact_form_submission_success(self):
        """Test successful contact form submission"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "name": f"TEST_Contact_{unique_id}",
            "email": f"test_{unique_id}@example.com",
            "phone": "+91 9876543210",
            "course": "JEE Mains",
            "message": "I want to know more about the courses"
        }
        response = requests.post(f"{BASE_URL}/api/admin/contact", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert "inquiry" in data
        assert data["inquiry"]["name"] == payload["name"]
        assert data["inquiry"]["email"] == payload["email"]
        assert data["inquiry"]["phone"] == payload["phone"]
        assert data["inquiry"]["course"] == payload["course"]
        assert data["inquiry"]["status"] == "new"
        assert "contact_id" in data["inquiry"]
        print(f"✓ Contact form submitted successfully: {data['inquiry']['contact_id']}")
        return data["inquiry"]["contact_id"]
    
    def test_contact_form_without_message(self):
        """Test contact form submission without optional message"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "name": f"TEST_NoMsg_{unique_id}",
            "email": f"nomsg_{unique_id}@example.com",
            "phone": "+91 1234567890",
            "course": "NEET"
        }
        response = requests.post(f"{BASE_URL}/api/admin/contact", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["inquiry"]["message"] == "" or data["inquiry"]["message"] is None
        print("✓ Contact form without message submitted successfully")
    
    def test_contact_form_missing_required_fields(self):
        """Test contact form with missing required fields"""
        payload = {
            "name": "Test User"
            # Missing email, phone, course
        }
        response = requests.post(f"{BASE_URL}/api/admin/contact", json=payload)
        
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"
        print("✓ Contact form correctly rejects missing required fields")


class TestAdminLoginFromMainPage:
    """Test admin login from the main /login page (POST /api/auth/login)"""
    
    def test_admin_login_success(self):
        """Test admin can login from main login page"""
        payload = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "user" in data
        assert data["user"]["role"] == "admin"
        assert data["user"]["email"] == ADMIN_EMAIL
        print(f"✓ Admin login successful, role: {data['user']['role']}")
        return response.cookies.get("session_token")
    
    def test_admin_login_invalid_password(self):
        """Test admin login with wrong password"""
        payload = {
            "email": ADMIN_EMAIL,
            "password": "wrongpassword"
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Admin login correctly rejects invalid password")
    
    def test_admin_login_invalid_email(self):
        """Test login with non-existent admin email"""
        payload = {
            "email": "notadmin@nexuacademy.com",
            "password": ADMIN_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Login correctly rejects non-existent email")


class TestAdminContactManagement:
    """Test admin can view and manage contact inquiries"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin before each test"""
        self.session = requests.Session()
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Admin login failed: {login_response.text}"
        self.admin_user = login_response.json().get("user")
    
    def test_admin_can_view_contacts(self):
        """Test admin can view all contact inquiries"""
        response = self.session.get(f"{BASE_URL}/api/admin/contacts")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "contacts" in data
        assert "stats" in data
        assert "total" in data["stats"]
        assert "new" in data["stats"]
        assert "responded" in data["stats"]
        print(f"✓ Admin can view contacts. Stats: total={data['stats']['total']}, new={data['stats']['new']}, responded={data['stats']['responded']}")
    
    def test_admin_can_mark_contact_responded(self):
        """Test admin can mark a contact inquiry as responded"""
        # First create a contact
        unique_id = uuid.uuid4().hex[:8]
        contact_payload = {
            "name": f"TEST_Respond_{unique_id}",
            "email": f"respond_{unique_id}@example.com",
            "phone": "+91 5555555555",
            "course": "JEE Advanced",
            "message": "Test message for respond test"
        }
        create_response = requests.post(f"{BASE_URL}/api/admin/contact", json=contact_payload)
        assert create_response.status_code == 200
        contact_id = create_response.json()["inquiry"]["contact_id"]
        
        # Mark as responded
        response = self.session.put(f"{BASE_URL}/api/admin/contacts/{contact_id}/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["message"] == "Status updated"
        print(f"✓ Admin marked contact {contact_id} as responded")
        
        # Verify status changed
        contacts_response = self.session.get(f"{BASE_URL}/api/admin/contacts")
        contacts = contacts_response.json()["contacts"]
        updated_contact = next((c for c in contacts if c["contact_id"] == contact_id), None)
        assert updated_contact is not None
        assert updated_contact["status"] == "responded"
        print("✓ Contact status verified as 'responded'")
    
    def test_mark_nonexistent_contact_returns_404(self):
        """Test marking non-existent contact returns 404"""
        response = self.session.put(f"{BASE_URL}/api/admin/contacts/nonexistent_id/status")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Correctly returns 404 for non-existent contact")


class TestAdminContactsRequiresAuth:
    """Test that contact management endpoints require admin auth"""
    
    def test_view_contacts_requires_auth(self):
        """Test GET /api/admin/contacts requires authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/contacts")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ View contacts correctly requires authentication")
    
    def test_mark_responded_requires_auth(self):
        """Test PUT /api/admin/contacts/{id}/status requires authentication"""
        response = requests.put(f"{BASE_URL}/api/admin/contacts/some_id/status")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Mark responded correctly requires authentication")


class TestTeacherLogin:
    """Test teacher login from main login page"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure test teacher exists"""
        # Login as admin to create teacher if needed
        admin_session = requests.Session()
        admin_session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        # Try to create test teacher (may already exist)
        admin_session.post(f"{BASE_URL}/api/admin/create-teacher", json={
            "name": "Test Teacher",
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
    
    def test_teacher_login_success(self):
        """Test teacher can login from main login page"""
        payload = {
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "user" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful, role: {data['user']['role']}")


class TestStudentLogin:
    """Test student login from main login page"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure test student exists"""
        # Try to register student (may already exist)
        requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Student",
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD,
            "batch_id": "batch_default"
        })
    
    def test_student_login_success(self):
        """Test student can login from main login page"""
        payload = {
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "user" in data
        assert data["user"]["role"] == "student"
        print(f"✓ Student login successful, role: {data['user']['role']}")


class TestAdminCreateTeacher:
    """Test admin can create teacher accounts"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        self.session = requests.Session()
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
    
    def test_admin_create_teacher_success(self):
        """Test admin can create a new teacher"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "name": f"TEST_Teacher_{unique_id}",
            "email": f"teacher_{unique_id}@nexuacademy.com",
            "password": "testpass123"
        }
        response = self.session.post(f"{BASE_URL}/api/admin/create-teacher", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "teacher" in data
        assert data["teacher"]["email"] == payload["email"]
        assert data["teacher"]["role"] == "teacher"
        print(f"✓ Teacher created: {payload['email']}")
    
    def test_admin_create_teacher_duplicate_email(self):
        """Test creating teacher with existing email fails"""
        unique_id = uuid.uuid4().hex[:8]
        payload = {
            "name": f"TEST_Dup_{unique_id}",
            "email": f"dup_{unique_id}@nexuacademy.com",
            "password": "testpass123"
        }
        # Create first time
        self.session.post(f"{BASE_URL}/api/admin/create-teacher", json=payload)
        
        # Try to create again with same email
        response = self.session.post(f"{BASE_URL}/api/admin/create-teacher", json=payload)
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Correctly rejects duplicate email")


class TestAdminListTeachers:
    """Test admin can list teachers"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin"""
        self.session = requests.Session()
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
    
    def test_admin_list_teachers(self):
        """Test admin can list all teachers"""
        response = self.session.get(f"{BASE_URL}/api/admin/teachers")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "teachers" in data
        assert isinstance(data["teachers"], list)
        print(f"✓ Admin can list teachers. Count: {len(data['teachers'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
