"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestGetActivities:
    """Test the GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 status"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_activities(self):
        """Test that GET /activities contains expected activities"""
        response = client.get("/activities")
        activities = response.json()
        expected_activities = [
            "Basketball", "Soccer", "Art Club", "Drama Club", 
            "Debate Team", "Science Club", "Chess Club", 
            "Programming Class", "Gym Class"
        ]
        for activity in expected_activities:
            assert activity in activities

    def test_activity_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_with_valid_activity_and_email(self):
        """Test successful signup for a valid activity"""
        response = client.post(
            "/activities/Basketball/signup?email=newemail@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_with_nonexistent_activity(self):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonexistentActivity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student_returns_400(self):
        """Test that signing up twice returns 400"""
        email = "james@mergington.edu"  # Already in Basketball
        response = client.post(
            f"/activities/Basketball/signup?email={email}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_response_format(self):
        """Test that signup response has correct format"""
        response = client.post(
            "/activities/Soccer/signup?email=testuser@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestUnregisterParticipant:
    """Test the DELETE /activities/{activity_name}/participants endpoint"""

    def test_unregister_existing_participant(self):
        """Test successful unregistration of existing participant"""
        response = client.delete(
            "/activities/Basketball/participants?email=james@mergington.edu"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/NonexistentActivity/participants?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_nonexistent_participant(self):
        """Test unregistering non-existent participant returns 404"""
        response = client.delete(
            "/activities/Basketball/participants?email=nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_unregister_response_format(self):
        """Test that unregister response has correct format"""
        # First signup
        client.post(
            "/activities/Art%20Club/signup?email=tempuser@mergington.edu"
        )
        # Then unregister
        response = client.delete(
            "/activities/Art%20Club/participants?email=tempuser@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestRootEndpoint:
    """Test the GET / endpoint"""

    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests for signup and unregister flow"""

    def test_signup_and_unregister_flow(self):
        """Test complete signup and unregister flow"""
        activity = "Science%20Club"
        email = "integration@mergington.edu"
        
        # Get initial state
        response = client.get("/activities")
        initial_count = len(response.json()["Science Club"]["participants"])
        
        # Signup
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        updated_count = len(response.json()["Science Club"]["participants"])
        assert updated_count == initial_count + 1
        assert email in response.json()["Science Club"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/participants?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        final_count = len(response.json()["Science Club"]["participants"])
        assert final_count == initial_count
        assert email not in response.json()["Science Club"]["participants"]
