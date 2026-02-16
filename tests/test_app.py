"""
Tests for the High School Activities Management System API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Test the GET /activities endpoint"""

    def test_get_activities_success(self):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        
        # Verify it's a dictionary
        assert isinstance(activities, dict)
        # Verify there are activities
        assert len(activities) > 0
        # Verify structure of an activity
        assert "Basketball" in activities or "Chess Club" in activities
        first_activity = list(activities.values())[0]
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity


class TestSignupEndpoint:
    """Test the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=student@example.com"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "student@example.com" in data["message"]
        assert "Basketball" in data["message"]

    def test_signup_duplicate(self):
        """Test that duplicate signups are prevented"""
        email = "duplicate@example.com"
        # First signup should succeed
        response1 = client.post(f"/activities/Art Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(f"/activities/Art Club/signup?email={email}")
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"].lower()

    def test_signup_nonexistent_activity(self):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent/signup?email=student@example.com"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestUnregisterEndpoint:
    """Test the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregistration from an activity"""
        email = "unregister@example.com"
        # First signup
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Drama Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]

    def test_unregister_not_signed_up(self):
        """Test unregistering when not signed up"""
        response = client.delete(
            "/activities/Debate Team/unregister?email=notregistered@example.com"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"].lower()

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent/unregister?email=student@example.com"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestRootEndpoint:
    """Test the GET / endpoint"""

    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "static/index.html" in response.headers["location"]


class TestIntegration:
    """Integration tests for signup/unregister flow"""

    def test_signup_updates_participants_list(self):
        """Test that signup correctly updates the participants list"""
        email = "integration@example.com"
        activity = "Volleyball"
        
        # Get initial activity state
        response1 = client.get("/activities")
        initial_participants = response1.json()[activity]["participants"].copy()
        
        # Signup
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Check updated activity state
        response2 = client.get("/activities")
        updated_participants = response2.json()[activity]["participants"]
        
        assert email in updated_participants
        assert len(updated_participants) == len(initial_participants) + 1

    def test_unregister_updates_participants_list(self):
        """Test that unregister correctly updates the participants list"""
        email = "integration2@example.com"
        activity = "Science Club"
        
        # Signup first
        client.post(f"/activities/{activity}/signup?email={email}")
        
        # Get participants list after signup
        response1 = client.get("/activities")
        participants_after_signup = response1.json()[activity]["participants"].copy()
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        
        # Check participants list after unregister
        response2 = client.get("/activities")
        participants_after_unregister = response2.json()[activity]["participants"]
        
        assert email not in participants_after_unregister
        assert len(participants_after_unregister) == len(participants_after_signup) - 1
