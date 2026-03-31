"""
Test Admin Panel Features for NexUacademy
- Admin login/logout
- Create teacher accounts
- List teachers
- Teacher/Student login with role-based redirect
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAdminLogin:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": "admin",
            "password": "nexuacademy123"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "message" in data, "Response should contain message"
        assert data["message"] == "Admin login successful"
        print(f"✓ Admin login successful, token: {data['token'][:20]}...")
    
    def test_admin_login_invalid_username(self):
        """Test admin login with wrong username"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": "wrongadmin",
            "password": "nexuacademy123"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        assert "Invalid admin credentials" in data["detail"]
        print("✓ Invalid username correctly rejected")
    
    def test_admin_login_invalid_password(self):
        """Test admin login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        assert "Invalid admin credentials" in data["detail"]
        print("✓ Invalid password correctly rejected")


class TestAdminTeacherManagement:
    """Admin teacher creation and listing tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": "admin",
            "password": "nexuacademy123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_create_teacher_success(self, admin_token):
        """Test creating a new teacher account"""
        unique_email = f"TEST_teacher_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(
            f"{BASE_URL}/api/admin/create-teacher",
            json={
                "name": "Test Teacher",
                "email": unique_email,
                "password": "teacher123"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert "Teacher account created successfully" in data["message"]
        assert "teacher" in data
        teacher = data["teacher"]
        assert teacher["email"] == unique_email
        assert teacher["name"] == "Test Teacher"
        assert teacher["role"] == "teacher"
        assert "password" not in teacher, "Password should not be returned"
        print(f"✓ Teacher created: {unique_email}")
    
    def test_create_teacher_duplicate_email(self, admin_token):
        """Test creating teacher with existing email fails"""
        # First create a teacher
        unique_email = f"TEST_dup_{uuid.uuid4().hex[:8]}@test.com"
        requests.post(
            f"{BASE_URL}/api/admin/create-teacher",
            json={"name": "First Teacher", "email": unique_email, "password": "pass123"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Try to create another with same email
        response = requests.post(
            f"{BASE_URL}/api/admin/create-teacher",
            json={"name": "Second Teacher", "email": unique_email, "password": "pass456"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "Email already registered" in data.get("detail", "")
        print("✓ Duplicate email correctly rejected")
    
    def test_create_teacher_without_auth(self):
        """Test creating teacher without admin auth fails"""
        response = requests.post(
            f"{BASE_URL}/api/admin/create-teacher",
            json={"name": "Unauth Teacher", "email": "unauth@test.com", "password": "pass123"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated request correctly rejected")
    
    def test_list_teachers(self, admin_token):
        """Test listing all teachers"""
        response = requests.get(
            f"{BASE_URL}/api/admin/teachers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "teachers" in data
        assert isinstance(data["teachers"], list)
        print(f"✓ Listed {len(data['teachers'])} teachers")
        
        # Verify teacher structure
        if len(data["teachers"]) > 0:
            teacher = data["teachers"][0]
            assert "email" in teacher
            assert "name" in teacher
            assert "role" in teacher
            assert teacher["role"] == "teacher"
            assert "password" not in teacher, "Password should not be returned"
    
    def test_list_teachers_without_auth(self):
        """Test listing teachers without admin auth fails"""
        response = requests.get(f"{BASE_URL}/api/admin/teachers")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Unauthenticated list request correctly rejected")


class TestAdminLogout:
    """Admin logout tests"""
    
    def test_admin_logout(self):
        """Test admin logout"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/admin/login", json={
            "username": "admin",
            "password": "nexuacademy123"
        })
        token = login_response.json().get("token")
        
        # Then logout
        response = requests.post(
            f"{BASE_URL}/api/admin/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "message" in data
        assert "logout" in data["message"].lower()
        print("✓ Admin logout successful")


class TestTeacherLogin:
    """Teacher login and role-based redirect tests"""
    
    def test_teacher_login_success(self):
        """Test teacher login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "teacher@test.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "user" in data
        user = data["user"]
        assert user["role"] == "teacher", f"Expected role 'teacher', got '{user['role']}'"
        assert user["email"] == "teacher@test.com"
        print(f"✓ Teacher login successful, role: {user['role']}")
    
    def test_teacher_login_invalid_password(self):
        """Test teacher login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "teacher@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid teacher password correctly rejected")


class TestStudentLogin:
    """Student login and role-based redirect tests"""
    
    def test_student_login_success(self):
        """Test student login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "student@test.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "user" in data
        user = data["user"]
        assert user["role"] == "student", f"Expected role 'student', got '{user['role']}'"
        assert user["email"] == "student@test.com"
        print(f"✓ Student login successful, role: {user['role']}")
    
    def test_student_login_invalid_password(self):
        """Test student login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "student@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid student password correctly rejected")


class TestStudentRegistration:
    """Student registration tests - signup should only allow students"""
    
    def test_student_registration_success(self):
        """Test student registration with batch selection"""
        unique_email = f"TEST_student_{uuid.uuid4().hex[:8]}@test.com"
        
        # First get available batches
        batches_response = requests.get(f"{BASE_URL}/api/batches/")
        batches = batches_response.json().get("batches", [])
        batch_id = batches[0]["id"] if batches else "JEE-2027-Morning"
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test Student",
            "email": unique_email,
            "password": "student123",
            "role": "student",
            "batch_id": batch_id
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "user" in data
        user = data["user"]
        # Registration should always create student role regardless of what's passed
        assert user["role"] == "student", f"Expected role 'student', got '{user['role']}'"
        assert user["email"] == unique_email
        print(f"✓ Student registration successful: {unique_email}")
    
    def test_registration_forces_student_role(self):
        """Test that registration always creates student role even if teacher is requested"""
        unique_email = f"TEST_forced_{uuid.uuid4().hex[:8]}@test.com"
        
        # Get a batch
        batches_response = requests.get(f"{BASE_URL}/api/batches/")
        batches = batches_response.json().get("batches", [])
        batch_id = batches[0]["id"] if batches else "JEE-2027-Morning"
        
        # Try to register as teacher (should be forced to student)
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Wannabe Teacher",
            "email": unique_email,
            "password": "teacher123",
            "role": "teacher",  # This should be ignored
            "batch_id": batch_id
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        user = data["user"]
        assert user["role"] == "student", f"Registration should force student role, got '{user['role']}'"
        print("✓ Registration correctly forces student role")


class TestBatchesAPI:
    """Batches API tests"""
    
    def test_get_batches(self):
        """Test getting list of batches"""
        response = requests.get(f"{BASE_URL}/api/batches/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "batches" in data
        assert isinstance(data["batches"], list)
        assert len(data["batches"]) > 0, "Should have at least one batch"
        
        # Verify batch structure
        batch = data["batches"][0]
        assert "id" in batch
        assert "name" in batch
        print(f"✓ Got {len(data['batches'])} batches")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
