import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    app_module = importlib.import_module("src.app")
    original_activities = app_module.activities.copy()
    app_module.activities = {
        name: {
            **details,
            "participants": list(details.get("participants", [])),
        }
        for name, details in original_activities.items()
    }

    with TestClient(app_module.app) as test_client:
        yield test_client

    app_module.activities = original_activities


def test_duplicate_signup_is_rejected_without_adding_participant(client):
    signup_url = "/activities/Chess Club/signup?email=student@example.com"

    first_response = client.post(signup_url)
    duplicate_response = client.post(signup_url)

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student already signed up for this activity"

    participants = client.get("/activities").json()["Chess Club"]["participants"]
    assert participants.count("student@example.com") == 1


def test_student_can_sign_up_for_different_activities(client):
    email = "student@example.com"

    chess_response = client.post(f"/activities/Chess Club/signup?email={email}")
    drama_response = client.post(f"/activities/Drama Club/signup?email={email}")

    assert chess_response.status_code == 200
    assert drama_response.status_code == 200


def test_unregister_participant_removes_their_signup(client):
    response = client.post("/activities/Chess Club/signup?email=student@example.com")
    assert response.status_code == 200

    response = client.delete("/activities/Chess Club/signup?email=student@example.com")
    assert response.status_code == 200

    activities = client.get("/activities").json()
    assert "student@example.com" not in activities["Chess Club"]["participants"]


def test_activities_endpoint_disables_caching(client):
    response = client.get("/activities")
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
