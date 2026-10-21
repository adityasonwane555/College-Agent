import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["database"] == "connected"
    assert "whisper" in data
    assert "ollama" in data


def test_config_endpoint():
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "stt_model" in data
    assert "tts_enabled" in data


def test_chat_endpoint_valid_and_invalid_input():
    # Valid input
    response = client.post("/api/chat", json={
        "message": "What is the fee for B.Tech?"
    })
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    assert isinstance(data["citations"], list)

    # Invalid empty message
    bad_resp = client.post("/api/chat", json={"message": "   "})
    assert bad_resp.status_code == 400


def test_college_info_endpoints():
    dept_resp = client.get("/api/college/departments")
    assert dept_resp.status_code == 200
    assert len(dept_resp.json()) > 0

    events_resp = client.get("/api/college/events")
    assert events_resp.status_code == 200
    assert len(events_resp.json()) > 0

    hours_resp = client.get("/api/college/hours")
    assert hours_resp.status_code == 200
    assert len(hours_resp.json()) > 0


def test_admin_endpoint_protection():
    # Attempting to post FAQ without authorization header
    unauth_resp = client.post("/api/admin/faq", json={
        "question": "Can unauthorized users post?",
        "answer": "No",
        "category": "Security"
    })
    assert unauth_resp.status_code == 401

    # Login to get token
    login_resp = client.post("/api/admin/login", json={
        "username": settings.ADMIN_USERNAME,
        "password": settings.ADMIN_PASSWORD
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["token"]

    # Authorized post
    auth_resp = client.post(
        "/api/admin/faq",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "question": "Can authenticated admins post?",
            "answer": "Yes they can.",
            "category": "Admin"
        }
    )
    assert auth_resp.status_code == 200
    assert auth_resp.json()["status"] == "created"
