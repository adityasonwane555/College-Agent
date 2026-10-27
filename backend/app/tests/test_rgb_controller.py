import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.hardware.rgb_controller import RGBController, VALID_STATES

client = TestClient(app)


def test_state_normalization():
    controller = RGBController(enabled=False)

    for state in ["BOOTING", "IDLE", "LISTENING", "THINKING", "SPEAKING", "ERROR"]:
        assert controller.normalize_state(state.lower()) == state
        assert controller.normalize_state(f"  {state}  ") == state

    # Synonyms and transitions that map to IDLE
    assert controller.normalize_state("COMPLETED_SPEECH") == "IDLE"
    assert controller.normalize_state("COMPLETED") == "IDLE"
    assert controller.normalize_state("done") == "IDLE"

    # Invalid states
    with pytest.raises(ValueError):
        controller.normalize_state("INVALID_STATE_XYZ")


def test_nonblocking_set_state():
    # Controller with a dummy non-reachable IP
    controller = RGBController(base_url="http://192.0.2.1:80", enabled=True, timeout=0.1)

    # Calling set_state must return immediately without throwing an exception
    success = controller.set_state("SPEAKING", amplitude=0.75)
    assert success is True
    assert controller.current_state == "SPEAKING"
    assert controller.current_amplitude == 0.75

    controller.set_state("THINKING")
    assert controller.current_state == "THINKING"

    status = controller.get_status()
    assert status["current_state"] == "THINKING"
    assert "configured_url" in status

    controller.close()


def test_offline_resilience():
    # Offline controller must never crash or block
    controller = RGBController(base_url="http://127.0.0.1:59999", enabled=True, timeout=0.05)
    res = controller.test_connection()
    assert res["ok"] is False
    assert "Cannot reach ESP32" in res["message"]
    controller.close()


def test_api_hardware_led_routes():
    # Test POST /api/hardware/led-state
    resp = client.post("/api/hardware/led-state", json={"state": "SPEAKING", "amplitude": 0.6})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert resp.json()["state"] == "SPEAKING"

    # Test GET /api/hardware/led-status
    resp_status = client.get("/api/hardware/led-status")
    assert resp_status.status_code == 200
    data = resp_status.json()
    assert "current_state" in data
    assert "configured_url" in data

    # Test POST /api/hardware/led-ping
    resp_ping = client.post("/api/hardware/led-ping")
    assert resp_ping.status_code == 200
    assert "ok" in resp_ping.json()
