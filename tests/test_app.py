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
