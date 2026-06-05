"""
Pytest configuration and fixtures for FastAPI app tests.
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app
import copy


# Sample activities data for testing
SAMPLE_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": []
    }
}


@pytest.fixture
def client():
    """
    Provide a TestClient for the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def fresh_activities(monkeypatch):
    """
    Reset app activities to sample data before each test.
    This ensures test isolation - each test gets a clean state.
    """
    from src import app as app_module
    
    # Create a deep copy of sample data to avoid mutations
    sample_copy = copy.deepcopy(SAMPLE_ACTIVITIES)
    
    # Replace the app's activities dict with our fresh copy
    monkeypatch.setattr(app_module, "activities", sample_copy)
    
    return sample_copy
