"""
Integration tests for FastAPI endpoints.

Tests cover all endpoints with both happy paths and error cases:
- GET / (redirect)
- GET /activities
- POST /activities/{activity_name}/signup
- POST /activities/{activity_name}/unregister
"""
import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, fresh_activities):
        """Test that get activities returns all activities with correct structure"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
    def test_get_activities_includes_all_fields(self, client, fresh_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)
        
    def test_get_activities_returns_participant_list(self, client, fresh_activities):
        """Test that participants are returned correctly"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club has 2 participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        
        # Gym Class has 0 participants
        assert len(data["Gym Class"]["participants"]) == 0


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client, fresh_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Gym%20Class/signup?email=john@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "john@mergington.edu" in data["message"]
        assert "Gym Class" in data["message"]
        
    def test_signup_adds_participant_to_activity(self, client, fresh_activities):
        """Test that signup actually adds participant to the activity"""
        client.post("/activities/Gym%20Class/signup?email=alice@mergington.edu")
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert "alice@mergington.edu" in data["Gym Class"]["participants"]
        
    def test_signup_duplicate_email_returns_400(self, client, fresh_activities):
        """Test that signing up with duplicate email returns error"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
        
    def test_signup_nonexistent_activity_returns_404(self, client, fresh_activities):
        """Test that signing up for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_signup_multiple_different_emails(self, client, fresh_activities):
        """Test that multiple different emails can sign up"""
        client.post("/activities/Gym%20Class/signup?email=student1@mergington.edu")
        client.post("/activities/Gym%20Class/signup?email=student2@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        participants = data["Gym Class"]["participants"]
        
        assert len(participants) == 2
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants
        
    def test_signup_to_different_activities(self, client, fresh_activities):
        """Test that same email can sign up for multiple activities"""
        email = "student@mergington.edu"
        
        client.post(f"/activities/Gym%20Class/signup?email={email}")
        client.post(f"/activities/Programming%20Class/signup?email={email}")
        
        response = client.get("/activities")
        data = response.json()
        
        assert email in data["Gym Class"]["participants"]
        assert email in data["Programming Class"]["participants"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client, fresh_activities):
        """Test successful unregister from an activity"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
        
    def test_unregister_removes_participant(self, client, fresh_activities):
        """Test that unregister actually removes participant"""
        client.post("/activities/Chess%20Club/unregister?email=michael@mergington.edu")
        
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]
        
    def test_unregister_nonexistent_participant_returns_404(self, client, fresh_activities):
        """Test that unregistering nonexistent participant returns 404"""
        response = client.post(
            "/activities/Gym%20Class/unregister?email=nobody@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Participant not found" in data["detail"]
        
    def test_unregister_nonexistent_activity_returns_404(self, client, fresh_activities):
        """Test that unregistering from nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
        
    def test_unregister_then_signup_again(self, client, fresh_activities):
        """Test that participant can be unregistered and then re-registered"""
        email = "michael@mergington.edu"
        activity = "Chess%20Club"
        
        # Unregister
        client.post(f"/activities/{activity}/unregister?email={email}")
        
        # Verify they're gone
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        
        # Sign up again
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify they're back
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
    def test_unregister_only_removes_specified_participant(self, client, fresh_activities):
        """Test that unregister only removes the specified participant"""
        activity = "Chess%20Club"
        
        # Unregister only michael
        client.post(f"/activities/{activity}/unregister?email=michael@mergington.edu")
        
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        
        # daniel should still be there
        assert "daniel@mergington.edu" in participants
        assert "michael@mergington.edu" not in participants


class TestEdgeCases:
    """Tests for edge cases and integration scenarios"""
    
    def test_url_encoded_activity_names(self, client, fresh_activities):
        """Test that URL-encoded activity names work correctly"""
        # "Programming Class" contains a space, must be URL encoded
        response = client.get("/activities")
        data = response.json()
        
        # Verify the activity exists (non-encoded key in dict)
        assert "Programming Class" in data
        
    def test_email_case_sensitivity(self, client, fresh_activities):
        """Test that email matching is case-sensitive"""
        email1 = "test@mergington.edu"
        email2 = "TEST@mergington.edu"
        
        client.post("/activities/Gym%20Class/signup?email=" + email1)
        client.post("/activities/Gym%20Class/signup?email=" + email2)
        
        response = client.get("/activities")
        participants = response.json()["Gym Class"]["participants"]
        
        # Both emails should be present (case-sensitive)
        assert email1 in participants
        assert email2 in participants
        assert len(participants) == 2
        
    def test_participant_count_updates_after_signup(self, client, fresh_activities):
        """Test that participant count is accurate after signup"""
        response = client.get("/activities")
        initial_count = len(response.json()["Gym Class"]["participants"])
        
        client.post("/activities/Gym%20Class/signup?email=new@mergington.edu")
        
        response = client.get("/activities")
        updated_count = len(response.json()["Gym Class"]["participants"])
        
        assert updated_count == initial_count + 1
        
    def test_max_participants_field_preserved(self, client, fresh_activities):
        """Test that max_participants field is not modified by signup"""
        response = client.get("/activities")
        initial_max = response.json()["Gym Class"]["max_participants"]
        
        client.post("/activities/Gym%20Class/signup?email=new@mergington.edu")
        
        response = client.get("/activities")
        updated_max = response.json()["Gym Class"]["max_participants"]
        
        assert updated_max == initial_max
