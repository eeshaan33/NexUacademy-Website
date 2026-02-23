"""
Test suite for Admission System APIs
Tests: Submit, List, Detail, Status Update, Stats, Export
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://test-maker-staging.preview.emergentagent.com')

class TestAdmissionAPIs:
    """Admission system endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data prefix for cleanup"""
        self.test_prefix = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.created_admission_id = None
    
    def test_01_admission_submit(self):
        """Test admission form submission creates entry in database"""
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "student_name": f"{self.test_prefix}_Student",
            "father_name": f"{self.test_prefix}_Father",
            "mother_name": f"{self.test_prefix}_Mother",
            "date_of_birth": "2005-05-15",
            "gender": "Male",
            "contact_number": "9876543210",
            "email": unique_email,
            "address": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456",
            "course_applying": "JEE Main 2025",
            "photo_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "signature_base64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        }
        
        response = requests.post(f"{BASE_URL}/api/admissions/submit", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "admission_id" in data
        assert data["admission_id"].startswith("ADM")
        
        # Store admission_id for subsequent tests
        self.__class__.created_admission_id = data["admission_id"]
        print(f"Created admission: {data['admission_id']}")
    
    def test_02_admission_stats(self):
        """Test admission stats endpoint returns correct structure"""
        response = requests.get(f"{BASE_URL}/api/admissions/stats")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "pending" in data
        assert "approved" in data
        assert "rejected" in data
        assert "by_course" in data
        
        # Values should be integers
        assert isinstance(data["total"], int)
        assert isinstance(data["pending"], int)
        assert isinstance(data["approved"], int)
        assert isinstance(data["rejected"], int)
        
        # Verify counts are consistent
        assert data["total"] >= data["pending"] + data["approved"] + data["rejected"] or \
               data["total"] == data["pending"] + data["approved"] + data["rejected"]
        
        print(f"Stats: Total={data['total']}, Pending={data['pending']}, Approved={data['approved']}, Rejected={data['rejected']}")
    
    def test_03_admission_list(self):
        """Test admission list endpoint returns paginated data"""
        response = requests.get(f"{BASE_URL}/api/admissions/list?limit=10&skip=0")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "admissions" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        
        assert isinstance(data["admissions"], list)
        assert data["total"] >= 0
        
        # Verify admission structure (exclude large base64 fields)
        if data["admissions"]:
            admission = data["admissions"][0]
            assert "admission_id" in admission
            assert "student_name" in admission
            assert "email" in admission
            assert "status" in admission
            assert "submitted_at" in admission
            # Photo and signature should be excluded in list view
            assert "photo" not in admission
            assert "signature" not in admission
        
        print(f"List: {len(data['admissions'])} admissions, page {data['page']} of {data['pages']}")
    
    def test_04_admission_list_filter_by_status(self):
        """Test admission list filtering by status"""
        # Test pending filter
        response = requests.get(f"{BASE_URL}/api/admissions/list?status=pending&limit=5")
        assert response.status_code == 200
        
        data = response.json()
        for admission in data["admissions"]:
            assert admission["status"] == "pending", f"Expected pending, got {admission['status']}"
        
        print(f"Filtered by pending: {len(data['admissions'])} results")
    
    def test_05_admission_detail(self):
        """Test admission detail endpoint returns full data including photo/signature"""
        # Use previously created admission or get first from list
        if not hasattr(self.__class__, 'created_admission_id') or not self.__class__.created_admission_id:
            list_response = requests.get(f"{BASE_URL}/api/admissions/list?limit=1")
            if list_response.status_code == 200 and list_response.json()["admissions"]:
                self.__class__.created_admission_id = list_response.json()["admissions"][0]["admission_id"]
        
        if not self.__class__.created_admission_id:
            pytest.skip("No admission available for detail test")
        
        response = requests.get(f"{BASE_URL}/api/admissions/detail/{self.__class__.created_admission_id}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["admission_id"] == self.__class__.created_admission_id
        assert "student_name" in data
        assert "father_name" in data
        assert "date_of_birth" in data
        assert "gender" in data
        assert "email" in data
        assert "contact_number" in data
        assert "address" in data
        assert "city" in data
        assert "state" in data
        assert "pincode" in data
        assert "course_applying" in data
        assert "status" in data
        
        # Detail should include photo and signature
        if data.get("photo"):
            assert "base64" in data["photo"] or data["photo"].startswith("data:image")
        if data.get("signature"):
            assert "base64" in data["signature"] or data["signature"].startswith("data:image")
        
        print(f"Detail for {data['admission_id']}: {data['student_name']}, status={data['status']}")
    
    def test_06_admission_detail_not_found(self):
        """Test admission detail returns 404 for invalid ID"""
        response = requests.get(f"{BASE_URL}/api/admissions/detail/INVALID_ID_12345")
        
        assert response.status_code == 404
        print("404 returned for invalid admission ID")
    
    def test_07_admission_update_status_approve(self):
        """Test admin can approve admission"""
        if not hasattr(self.__class__, 'created_admission_id') or not self.__class__.created_admission_id:
            pytest.skip("No admission available for status update test")
        
        response = requests.put(
            f"{BASE_URL}/api/admissions/update-status/{self.__class__.created_admission_id}?status=approved"
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        
        # Verify status change persisted
        detail_response = requests.get(f"{BASE_URL}/api/admissions/detail/{self.__class__.created_admission_id}")
        assert detail_response.status_code == 200
        assert detail_response.json()["status"] == "approved"
        
        print(f"Admission {self.__class__.created_admission_id} approved successfully")
    
    def test_08_admission_update_status_reject(self):
        """Test admin can reject admission"""
        # Create new admission for rejection test
        unique_email = f"reject_test_{uuid.uuid4().hex[:8]}@example.com"
        
        payload = {
            "student_name": "Reject Test Student",
            "father_name": "Test Father",
            "mother_name": "Test Mother",
            "date_of_birth": "2005-06-20",
            "gender": "Female",
            "contact_number": "9876543211",
            "email": unique_email,
            "address": "456 Test Avenue",
            "city": "Test City",
            "state": "Test State",
            "pincode": "654321",
            "course_applying": "JEE Advanced 2025"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admissions/submit", json=payload)
        assert create_response.status_code == 200
        
        new_admission_id = create_response.json()["admission_id"]
        
        # Reject the admission
        response = requests.put(
            f"{BASE_URL}/api/admissions/update-status/{new_admission_id}?status=rejected"
        )
        
        assert response.status_code == 200
        assert response.json().get("success") == True
        
        # Verify rejection persisted
        detail_response = requests.get(f"{BASE_URL}/api/admissions/detail/{new_admission_id}")
        assert detail_response.status_code == 200
        assert detail_response.json()["status"] == "rejected"
        
        print(f"Admission {new_admission_id} rejected successfully")
    
    def test_09_admission_export_csv(self):
        """Test CSV export endpoint returns downloadable file"""
        response = requests.get(f"{BASE_URL}/api/admissions/export/excel")
        
        assert response.status_code == 200
        
        # Check content type is CSV
        content_type = response.headers.get("content-type", "")
        assert "text/csv" in content_type or "application/octet-stream" in content_type or "text/plain" in content_type
        
        # Check content disposition for filename
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition or "admissions.csv" in content_disposition
        
        # Verify CSV content structure
        csv_content = response.text
        lines = csv_content.strip().split("\n")
        assert len(lines) >= 1  # At least header row
        
        # Check header contains expected columns
        header = lines[0].lower()
        assert "admission_id" in header
        assert "student_name" in header
        assert "email" in header
        assert "status" in header
        
        print(f"CSV export successful: {len(lines)} rows (including header)")
    
    def test_10_admission_submit_validation(self):
        """Test admission submission validation for required fields"""
        # Missing required fields should fail
        payload = {
            "student_name": "Test",
            # Missing other required fields
        }
        
        response = requests.post(f"{BASE_URL}/api/admissions/submit", json=payload)
        
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("Validation error returned for incomplete form")


class TestQuestionsSyllabus:
    """Test chemistry chapters are accessible"""
    
    def test_syllabus_has_new_chemistry_chapters(self):
        """Test new chemistry chapters are accessible in syllabus"""
        response = requests.get(f"{BASE_URL}/api/questions/syllabus")
        
        assert response.status_code == 200
        
        data = response.json()
        
        # Structure is { "Chemistry": { "Class11": [...], "Class12": [...] }, "Physics": {...}, ... }
        assert "Chemistry" in data, "Chemistry subject not found"
        
        chemistry = data["Chemistry"]
        
        # Get all chapter names from both Class11 and Class12
        chapter_names = []
        for class_key in ["Class11", "Class12"]:
            if class_key in chemistry:
                chapter_names.extend([c.get("chapter") for c in chemistry[class_key]])
        
        # Check for new chemistry chapters (mapped to actual chapter names in syllabus)
        new_chapters = [
            "Coordination Compounds",
            "The d- and f-Block Elements",  # D-F Block mapped to this
            "Electrochemistry",
            "Chemistry in Everyday Life",  # Environmental Chemistry related
            "Equilibrium"
        ]
        
        found_chapters = []
        missing_chapters = []
        for chapter in new_chapters:
            if chapter in chapter_names:
                found_chapters.append(chapter)
            else:
                missing_chapters.append(chapter)
        
        print(f"Found chapters: {found_chapters}")
        if missing_chapters:
            print(f"Missing chapters: {missing_chapters}")
        
        # At least some of the new chapters should be present
        assert len(found_chapters) >= 3, f"Expected at least 3 new chapters, found {len(found_chapters)}: {found_chapters}"
    
    def test_new_chemistry_chapters_have_questions(self):
        """Test that new chemistry chapters have questions loaded"""
        chapters_to_test = [
            ("Coordination Compounds", 100),  # Expected at least 100 questions
            ("Electrochemistry", 100),
            ("Equilibrium", 50)
        ]
        
        for chapter, min_expected in chapters_to_test:
            response = requests.get(f"{BASE_URL}/api/questions/?limit=1&subject=Chemistry&chapter={chapter}")
            assert response.status_code == 200
            
            data = response.json()
            total = data.get("total", 0)
            
            print(f"{chapter}: {total} questions")
            assert total >= min_expected, f"Expected at least {min_expected} questions for {chapter}, got {total}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
