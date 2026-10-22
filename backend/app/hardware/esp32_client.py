"""
BUDDY AI — ESP32-S3 Hardware Client (PC Side)
Provides complete integration between the PC AI Agent and the ESP32-S3:
- RGB LED animations & audio-reactive modulation
- ST7789 TFT display updates (robot expressions, status cards, answers)
- Streaming audio playback from PC to MAX98357A speaker
- Fetching audio captures from INMP441 microphone for Whisper transcription
"""

import io
import time
import httpx
import wave
import logging
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger("buddy.hardware.esp32")


class ESP32Client:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 5.0
    ):
        self.base_url = (base_url or settings.ESP32_LED_URL).rstrip("/")
        self.timeout = timeout
        self.is_connected = False
        self.last_contact = 0.0

    def check_health(self) -> Dict[str, Any]:
        """Pings the ESP32 /health endpoint."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/health")
                if resp.status_code == 200:
                    self.is_connected = True
                    self.last_contact = time.time()
                    return resp.json()
        except Exception as e:
            self.is_connected = False
            logger.warning(f"ESP32 health check failed: {e}")
        return {"status": "offline", "error": "Cannot reach ESP32"}

    def set_state(
        self,
        state: str,
        amplitude: float = 0.0,
        bass: Optional[float] = None,
        mid: Optional[float] = None,
        treble: Optional[float] = None
    ) -> bool:
        """Updates robot state (IDLE, LISTENING, THINKING, SPEAKING, ERROR)."""
        payload = {
            "state": state,
            "amplitude": round(amplitude, 3),
            "bass": round(bass or 0.0, 3),
            "mid": round(mid or 0.0, 3),
            "treble": round(treble or 0.0, 3)
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/state", json=payload)
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to set ESP32 state: {e}")
            return False

    def update_display(self, title: str, body: str) -> bool:
        """Sends a message or announcement to the ST7789 display."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/api/display",
                    data={"title": title, "body": body}
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to update ESP32 display: {e}")
            return False

    def trigger_chime(self) -> bool:
        """Triggers the ESP32 hardware chime tone test."""
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/chime")
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to trigger chime: {e}")
            return False

    def stream_wav_to_speaker(self, wav_bytes: bytes) -> bool:
        """
        Parses a WAV file and streams raw 16-bit PCM to the MAX98357A speaker.
        """
        try:
            with io.BytesIO(wav_bytes) as bio:
                with wave.open(bio, "rb") as wf:
                    raw_pcm = wf.readframes(wf.getnframes())

            with httpx.Client(timeout=15.0) as client:
                resp = client.post(
                    f"{self.base_url}/api/speak/raw",
                    content=raw_pcm,
                    headers={"Content-Type": "application/octet-stream"}
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to stream audio to ESP32 speaker: {e}")
            return False

    def fetch_mic_recording(self, seconds: int = 3) -> Optional[bytes]:
        """
        Downloads a recorded WAV clip from the ESP32 INMP441 microphone.
        """
        try:
            with httpx.Client(timeout=seconds + 8.0) as client:
                resp = client.get(f"{self.base_url}/api/mic/record?seconds={seconds}")
                if resp.status_code == 200:
                    return resp.content
        except Exception as e:
            logger.warning(f"Failed to fetch mic audio from ESP32: {e}")
        return None


esp32_client = ESP32Client()
