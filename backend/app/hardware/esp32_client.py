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
import threading
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
        self._streaming_lock = threading.Lock()
        self._active_stream_client: Optional[httpx.Client] = None

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

    def stream_wav_to_speaker(self, audio_bytes: bytes, sample_rate: int = 24000) -> bool:
        """
        Decodes any audio file (MP3, WAV, etc.) into 16-bit mono PCM and streams it
        directly to the ESP32 MAX98357A speaker over Wi-Fi.
        """
        try:
            raw_pcm = b""
            # Use PyAV for universal audio decoding (MP3 from edge-tts, WAV from Fish Audio, etc.)
            try:
                import av
                container = av.open(io.BytesIO(audio_bytes))
                resampler = av.AudioResampler(format='s16', layout='mono', rate=sample_rate)
                chunks = []
                for frame in container.decode(audio=0):
                    for rframe in resampler.resample(frame):
                        chunks.append(rframe.to_ndarray().tobytes())
                raw_pcm = b"".join(chunks)
            except Exception as av_err:
                # Fallback to standard library wave module for WAV
                with io.BytesIO(audio_bytes) as bio:
                    with wave.open(bio, "rb") as wf:
                        raw_pcm = wf.readframes(wf.getnframes())

            if not raw_pcm:
                logger.warning("Decoded PCM audio buffer is empty.")
                return False

            # Dynamic timeout calculated from audio duration (16-bit mono = 2 bytes per sample)
            # ESP32 drains PCM at sample_rate, so network stream duration equals audio duration.
            audio_duration_sec = len(raw_pcm) / float(sample_rate * 2)
            stream_timeout = max(audio_duration_sec * 2.5 + 30.0, 90.0)

            client = httpx.Client(timeout=httpx.Timeout(stream_timeout, connect=2.0))
            with self._streaming_lock:
                self._active_stream_client = client
            try:
                url = f"{self.base_url}/api/speak/raw"
                resp = client.post(
                    url,
                    content=raw_pcm,
                    headers={"Content-Type": "application/octet-stream"}
                )
                if resp.status_code == 404:
                    resp = client.post(
                        f"{self.base_url}/api/speak",
                        content=raw_pcm,
                        headers={"Content-Type": "application/octet-stream"}
                    )
                return resp.status_code == 200
            finally:
                with self._streaming_lock:
                    if self._active_stream_client is client:
                        self._active_stream_client = None
                try:
                    client.close()
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Failed to stream audio to ESP32 speaker: {e}")
            return False

    def stop_speaker(self, target_state: str = "IDLE", reset_display: bool = True) -> bool:
        """Immediately halts speech playback on ESP32 hardware and transitions display & LED."""
        with self._streaming_lock:
            if self._active_stream_client:
                try:
                    self._active_stream_client.close()
                except Exception:
                    pass
                self._active_stream_client = None

        try:
            state_val = target_state.upper() if target_state else ("IDLE" if reset_display else "IDLE")
            with httpx.Client(timeout=2.0) as client:
                resp = client.post(f"{self.base_url}/api/stop?state={state_val}&idle=1")
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to send stop signal to ESP32: {e}")
            return False

    def fetch_mic_recording(self, seconds: int = 3) -> Optional[bytes]:
        """
        Downloads a recorded WAV clip from the ESP32 INMP441 microphone.
        Supports both the dedicated /api/mic/record endpoint and chunked /api/mic fallback.
        """
        try:
            with httpx.Client(timeout=seconds + 8.0) as client:
                resp = client.get(f"{self.base_url}/api/mic/record?seconds={seconds}")
                if resp.status_code == 200 and len(resp.content) > 44:
                    return resp.content
                elif resp.status_code == 404:
                    # Fallback for firmware running without /api/mic/record
                    logger.info("ESP32 /api/mic/record not found, falling back to /api/mic sample capture...")
                    pcm_chunks = []
                    start_t = time.time()
                    while time.time() - start_t < min(seconds, 2.5):
                        try:
                            r = client.get(f"{self.base_url}/api/mic")
                            if r.status_code == 200 and len(r.content) > 0:
                                pcm_chunks.append(r.content)
                        except Exception:
                            break
                    if pcm_chunks:
                        raw_pcm = b"".join(pcm_chunks)
                        return self._create_wav(raw_pcm, sample_rate=16000, channels=1, bits_per_sample=16)
        except Exception as e:
            logger.warning(f"Failed to fetch mic audio from ESP32: {e}")
        return None

    @staticmethod
    def _create_wav(pcm_data: bytes, sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        import struct
        data_size = len(pcm_data)
        riff_size = 36 + data_size
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)
        header = struct.pack(
            '<4sI4s4sIHHIIHH4sI',
            b'RIFF', riff_size, b'WAVE',
            b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample,
            b'data', data_size
        )
        return header + pcm_data


esp32_client = ESP32Client()
