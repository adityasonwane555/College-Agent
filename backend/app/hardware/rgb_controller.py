"""
BUDDY AI - Hardware RGB LED Controller Client
Communicates with the ESP32-S3 over local Wi-Fi to synchronize the onboard WS2812 RGB LED
with the real-time AI speech, thought, and listening states.
"""

import sys
import time
import httpx
import logging
import asyncio
import threading
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger("buddy.hardware.led")

VALID_STATES = {
    "BOOTING",
    "IDLE",
    "LISTENING",
    "THINKING",
    "SPEAKING",
    "INTERRUPTED",
    "ERROR",
    "COMPLETED"
}


class RGBController:
    """
    Non-blocking PC client that dispatches state updates to the ESP32-S3 over Wi-Fi.
    All network transmissions occur asynchronously in a background thread/task to
    guarantee zero latency impact on audible speech playback or AI processing.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout: Optional[float] = None,
        token: Optional[str] = None
    ):
        self.base_url = (base_url or settings.ESP32_LED_URL).rstrip("/")
        self.enabled = settings.ESP32_LED_ENABLED if enabled is None else enabled
        self.timeout = settings.ESP32_LED_TIMEOUT_SECONDS if timeout is None else timeout
        self.token = settings.ESP32_LED_TOKEN if token is None else token

        self.current_state: str = "BOOTING"
        self.current_amplitude: float = 0.0
        self.last_sent_state: Optional[str] = None
        self.last_sent_amplitude: float = 0.0
        self.is_connected: bool = False
        self.last_error: Optional[str] = None
        self.last_contact_time: float = 0.0

        # Background transmission queue and worker
        self._lock = threading.Lock()
        self._pending_update: Optional[Dict[str, Any]] = None
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._has_work = threading.Event()

        if self.enabled:
            self._start_worker()

    def _start_worker(self):
        """Starts background worker thread for non-blocking HTTP dispatch."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                name="BuddyLedWorker",
                daemon=True
            )
            self._worker_thread.start()

    def _worker_loop(self):
        """Dedicated background thread that dispatches queued state changes."""
        while not self._stop_event.is_set():
            # Wait until new state update is queued
            self._has_work.wait(timeout=0.5)
            if self._stop_event.is_set():
                break

            payload = None
            with self._lock:
                if self._pending_update:
                    payload = self._pending_update
                    self._pending_update = None
                self._has_work.clear()

            if payload:
                self._dispatch_sync(
                    payload["state"],
                    payload.get("amplitude", 0.0),
                    payload.get("bass"),
                    payload.get("mid"),
                    payload.get("treble")
                )

    def _dispatch_sync(
        self,
        state: str,
        amplitude: float = 0.0,
        bass: Optional[float] = None,
        mid: Optional[float] = None,
        treble: Optional[float] = None
    ) -> bool:
        """Performs synchronous HTTP POST to ESP32 /api/state."""
        if not self.enabled:
            return False

        url = f"{self.base_url}/api/state"
        body: Dict[str, Any] = {"state": state, "amplitude": round(amplitude, 2)}
        if bass is not None:
            body["bass"] = round(bass, 2)
        if mid is not None:
            body["mid"] = round(mid, 2)
        if treble is not None:
            body["treble"] = round(treble, 2)

        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=body, headers=headers)
                if resp.status_code == 200:
                    self.is_connected = True
                    self.last_sent_state = state
                    self.last_sent_amplitude = amplitude
                    self.last_contact_time = time.time()
                    self.last_error = None
                    return True
                else:
                    self.last_error = f"HTTP {resp.status_code}: {resp.text[:100]}"
                    logger.warning("[RGBController] ESP32 error: %s", self.last_error)
                    return False
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            logger.debug("[RGBController] Could not reach ESP32 at %s: %s", url, e)
            return False

    def normalize_state(self, state: str) -> str:
        """Normalizes and validates incoming state string."""
        s = state.strip().upper()
        if s in ("COMPLETED_SPEECH", "FINISHED", "DONE"):
            return "COMPLETED"
        if s not in VALID_STATES:
            raise ValueError(f"Invalid state '{state}'. Valid states: {sorted(list(VALID_STATES))}")
        return s

    def set_state(
        self,
        state: str,
        amplitude: float = 0.0,
        bass: Optional[float] = None,
        mid: Optional[float] = None,
        treble: Optional[float] = None
    ) -> bool:
        """
        Non-blocking API: Enqueues a state update and returns immediately (<0.1ms).
        Ensures the AI voice playback and reasoning pipelines are never stalled.
        """
        try:
            norm_state = self.normalize_state(state)
        except ValueError as ve:
            logger.error("[RGBController] %s", ve)
            return False

        self.current_state = norm_state
        self.current_amplitude = amplitude

        # Suppress identical duplicates (unless frequency or amplitude changed during SPEAKING)
        if (
            norm_state == self.last_sent_state
            and abs(amplitude - self.last_sent_amplitude) < 0.15
            and norm_state != "SPEAKING"
        ):
            return True

        if not self.enabled:
            return True

        with self._lock:
            self._pending_update = {
                "state": norm_state,
                "amplitude": amplitude,
                "bass": bass,
                "mid": mid,
                "treble": treble
            }
            self._has_work.set()

        return True

    async def set_state_async(self, state: str, amplitude: float = 0.0) -> bool:
        """Asynchronous coroutine wrapper for non-blocking state updates."""
        return self.set_state(state, amplitude)

    def get_status(self) -> Dict[str, Any]:
        """Returns local controller status and connectivity to the ESP32."""
        return {
            "enabled": self.enabled,
            "configured_url": self.base_url,
            "current_state": self.current_state,
            "last_sent_state": self.last_sent_state,
            "is_connected": self.is_connected,
            "last_error": self.last_error,
            "last_contact_ago_sec": round(time.time() - self.last_contact_time, 1) if self.last_contact_time else None
        }

    def test_connection(self) -> Dict[str, Any]:
        """Actively pings ESP32-S3 /health and /api/status endpoints to verify hardware."""
        if not self.enabled:
            return {"ok": False, "message": "ESP32 LED Controller is disabled in configuration."}

        url = f"{self.base_url}/api/status"
        try:
            with httpx.Client(timeout=1.5) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    self.is_connected = True
                    self.last_contact_time = time.time()
                    return {"ok": True, "device_data": data, "message": f"Successfully connected to ESP32 at {self.base_url}"}
                else:
                    return {"ok": False, "message": f"ESP32 returned status {resp.status_code}"}
        except Exception as e:
            self.is_connected = False
            return {"ok": False, "message": f"Cannot reach ESP32 at {self.base_url}: {e}"}

    def close(self):
        """Shuts down background worker thread."""
        self._stop_event.set()
        self._has_work.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)


# Global singleton instance for application-wide use
rgb_controller = RGBController()


# Convenience module-level functions
def set_led_state(state: str, amplitude: float = 0.0) -> bool:
    return rgb_controller.set_state(state, amplitude)


async def set_led_state_async(state: str, amplitude: float = 0.0) -> bool:
    return await rgb_controller.set_state_async(state, amplitude)


def get_led_status() -> Dict[str, Any]:
    return rgb_controller.get_status()
