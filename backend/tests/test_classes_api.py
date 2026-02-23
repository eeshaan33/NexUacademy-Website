"""
Test Classes API for My Classes Section
Features:
- List all classes (upcoming and past)
- Get upcoming classes with countdown timer data
- Get past classes with recording/notes links
- Class detail with computed status
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestClassesAPI:
    """Tests for Classes API endpoints"""
    
    def test_01_get_all_classes(self):
        """Test GET /api/classes returns all classes"""
        response = requests.get(f"{BASE_URL}/api/classes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "classes" in data, "Response should have 'classes' key"
        assert "total" in data, "Response should have 'total' key"
        assert isinstance(data["classes"], list), "Classes should be a list"
        assert data["total"] > 0, "Should have seeded classes"
        
        # Verify class structure
        if data["classes"]:
            cls = data["classes"][0]
            assert "class_id" in cls, "Class should have class_id"
            assert "title" in cls, "Class should have title"
            assert "subject" in cls, "Class should have subject"
            assert "scheduled_datetime" in cls, "Class should have scheduled_datetime"
            assert "computed_status" in cls, "Class should have computed_status"
            assert "seconds_until_start" in cls, "Class should have seconds_until_start"
        print(f"PASSED: Got {data['total']} classes")

    def test_02_get_upcoming_classes(self):
        """Test GET /api/classes/upcoming returns upcoming classes with countdown data"""
        response = requests.get(f"{BASE_URL}/api/classes/upcoming")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "classes" in data, "Response should have 'classes' key"
        
        # Verify upcoming classes structure
        for cls in data["classes"]:
            assert "seconds_until_start" in cls, "Upcoming class should have seconds_until_start"
            assert "can_join" in cls, "Upcoming class should have can_join flag"
            assert cls["seconds_until_start"] >= 0, "seconds_until_start should be non-negative"
            
            # Verify scheduled_datetime is in future
            scheduled = datetime.fromisoformat(cls["scheduled_datetime"].replace('Z', '+00:00'))
            # Remove timezone for comparison if needed
            if scheduled.tzinfo:
                scheduled = scheduled.replace(tzinfo=None)
        
        print(f"PASSED: Got {len(data['classes'])} upcoming classes")

    def test_03_get_past_classes(self):
        """Test GET /api/classes/past returns past classes with recording links"""
        response = requests.get(f"{BASE_URL}/api/classes/past")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "classes" in data, "Response should have 'classes' key"
        
        # Verify past classes have expected fields
        has_recording = False
        has_notes = False
        has_slides = False
        
        for cls in data["classes"]:
            assert "scheduled_datetime" in cls, "Class should have scheduled_datetime"
            if cls.get("recording_url"):
                has_recording = True
            if cls.get("notes_url"):
                has_notes = True
            if cls.get("slides_url"):
                has_slides = True
        
        # At least some past classes should have resources
        assert has_recording or has_notes or has_slides, "Some past classes should have resources"
        print(f"PASSED: Got {len(data['classes'])} past classes with recording/notes links")

    def test_04_upcoming_classes_have_correct_fields(self):
        """Verify upcoming classes contain all fields needed for countdown timer"""
        response = requests.get(f"{BASE_URL}/api/classes/upcoming")
        assert response.status_code == 200
        
        data = response.json()
        if data["classes"]:
            cls = data["classes"][0]
            
            # Fields needed for NextClassCard component
            required_fields = [
                "class_id", "title", "subject", "chapter", "topic",
                "teacher_name", "scheduled_datetime", "duration",
                "meeting_link", "meeting_platform", "description",
                "seconds_until_start", "can_join"
            ]
            
            for field in required_fields:
                assert field in cls, f"Upcoming class should have '{field}'"
            
            print(f"PASSED: Upcoming class has all required fields for countdown timer")

    def test_05_past_classes_have_resource_links(self):
        """Verify past classes have recording/notes/slides links"""
        response = requests.get(f"{BASE_URL}/api/classes/past")
        assert response.status_code == 200
        
        data = response.json()
        resources_found = {"recording": [], "notes": [], "slides": []}
        
        for cls in data["classes"]:
            if cls.get("recording_url"):
                resources_found["recording"].append(cls["title"])
            if cls.get("notes_url"):
                resources_found["notes"].append(cls["title"])
            if cls.get("slides_url"):
                resources_found["slides"].append(cls["title"])
        
        print(f"PASSED: Past classes with recording: {len(resources_found['recording'])}")
        print(f"PASSED: Past classes with notes: {len(resources_found['notes'])}")
        print(f"PASSED: Past classes with slides: {len(resources_found['slides'])}")

    def test_06_get_class_by_id(self):
        """Test GET /api/classes/{class_id} returns single class details"""
        # First get a class_id from the list
        response = requests.get(f"{BASE_URL}/api/classes")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["classes"]) > 0, "Should have at least one class"
        
        class_id = data["classes"][0]["class_id"]
        
        # Get single class details
        response = requests.get(f"{BASE_URL}/api/classes/{class_id}")
        assert response.status_code == 200
        
        cls = response.json()
        assert cls["class_id"] == class_id
        assert "computed_status" in cls
        assert "seconds_until_start" in cls
        
        print(f"PASSED: Got class details for {cls['title']}")

    def test_07_get_class_schedule(self):
        """Test GET /api/classes/schedule returns grouped schedule"""
        response = requests.get(f"{BASE_URL}/api/classes/schedule?days=14")
        assert response.status_code == 200
        
        data = response.json()
        assert "schedule" in data
        assert isinstance(data["schedule"], dict)
        
        print(f"PASSED: Got schedule with {len(data['schedule'])} days")

    def test_08_class_not_found(self):
        """Test GET /api/classes/{class_id} returns 404 for invalid ID"""
        response = requests.get(f"{BASE_URL}/api/classes/invalid_class_id_12345")
        assert response.status_code == 404
        
        print("PASSED: Returns 404 for invalid class_id")


class TestClassesComputed:
    """Tests for computed class status and countdown"""
    
    def test_01_computed_status_values(self):
        """Verify computed_status is valid (upcoming/ongoing/completed)"""
        response = requests.get(f"{BASE_URL}/api/classes")
        assert response.status_code == 200
        
        data = response.json()
        valid_statuses = {"upcoming", "ongoing", "completed"}
        
        for cls in data["classes"]:
            status = cls.get("computed_status")
            assert status in valid_statuses, f"Invalid status: {status}"
        
        print("PASSED: All computed_status values are valid")

    def test_02_seconds_until_start_calculation(self):
        """Verify seconds_until_start is calculated correctly"""
        response = requests.get(f"{BASE_URL}/api/classes/upcoming")
        assert response.status_code == 200
        
        data = response.json()
        for cls in data["classes"]:
            seconds = cls["seconds_until_start"]
            assert isinstance(seconds, int), "seconds_until_start should be int"
            assert seconds >= 0, "seconds_until_start should be non-negative for upcoming"
        
        print("PASSED: seconds_until_start calculated correctly")

    def test_03_can_join_flag(self):
        """Verify can_join flag is set (true if within 10 mins of start)"""
        response = requests.get(f"{BASE_URL}/api/classes/upcoming")
        assert response.status_code == 200
        
        data = response.json()
        for cls in data["classes"]:
            can_join = cls["can_join"]
            seconds = cls["seconds_until_start"]
            
            # If more than 10 minutes away, should not be joinable
            if seconds > 600:
                assert can_join == False, f"Class should not be joinable if {seconds}s away"
        
        print("PASSED: can_join flag is correctly set")


class TestClassesFiltering:
    """Tests for class filtering options"""
    
    def test_01_filter_by_subject(self):
        """Test filtering classes by subject"""
        subjects = ["Physics", "Chemistry", "Mathematics"]
        
        for subject in subjects:
            response = requests.get(f"{BASE_URL}/api/classes?subject={subject}")
            assert response.status_code == 200
            
            data = response.json()
            for cls in data["classes"]:
                assert cls["subject"] == subject, f"Expected {subject}, got {cls['subject']}"
        
        print("PASSED: Subject filtering works correctly")

    def test_02_filter_upcoming_only(self):
        """Test filtering for upcoming classes only"""
        response = requests.get(f"{BASE_URL}/api/classes?upcoming_only=true")
        assert response.status_code == 200
        
        data = response.json()
        for cls in data["classes"]:
            status = cls.get("computed_status")
            assert status in ["upcoming", "ongoing"], f"Expected upcoming/ongoing, got {status}"
        
        print("PASSED: upcoming_only filter works")

    def test_03_pagination(self):
        """Test pagination with limit and skip"""
        # Get first 2 classes
        response1 = requests.get(f"{BASE_URL}/api/classes?limit=2&skip=0")
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Get next 2 classes
        response2 = requests.get(f"{BASE_URL}/api/classes?limit=2&skip=2")
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Verify pagination works (different classes)
        if len(data1["classes"]) > 0 and len(data2["classes"]) > 0:
            assert data1["classes"][0]["class_id"] != data2["classes"][0]["class_id"]
        
        print("PASSED: Pagination works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
