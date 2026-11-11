"""
BUDDY AI 2.0 — ESP32-S3 Hardware Client (PC Side)

Architecture & Hardware Peripheral Integration:
  - Microcontroller Transport & Network Protocol:
      - Communicates with the ESP32-S3 over local Wi-Fi via lightweight HTTP REST endpoints.
      - Enforces 'Connection: close' semantics to prevent single-threaded ESP32 WebServer socket exhaustion.
      - Implements dual-phase network auto-discovery combining mDNS (buddy.local) and local subnet ARP scanning.
  - Actuation & Audio Streaming Subsystems:
      - MAX98357A I2S Audio Amplifier: Streams 24kHz 16-bit mono signed PCM with dynamic timeout calculations
        proportional to playback duration and thread-safe streaming cancellation.
      - INMP441 I2S Microphone: On-demand 16kHz audio recording capture over Wi-Fi with automatic RIFF WAVE packaging.
      - ST7789 SPI TFT Display: Text, status cards, and facial expression updates rendered at 40MHz SPI.
      - WS2812 RGB LED Ring/Matrix: Synchronizes visual states and 3-band audio reactivity (bass, mid, treble).
      - Hardware Chime Generation: Auditory confirmation tones synthesized directly on the DAC.
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
    """
    PC-side hardware client for orchestrating the companion ESP32-S3 microcontroller.
    Provides audio streaming, microphone recording, display rendering, and automatic network discovery.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 5.0
    ):
        """
        Initializes the ESP32 hardware client.

        Args:
            base_url: Base HTTP URL of the ESP32-S3 (defaults to settings.ESP32_LED_URL).
            timeout: Default HTTP socket timeout in seconds.
        """
        self.base_url = (base_url or settings.ESP32_LED_URL).rstrip("/")
        self.timeout = timeout
        self.is_connected = False
        self.last_contact = 0.0
        self._last_speaker_fail = 0.0
        self._streaming_lock = threading.Lock()
        self._active_stream_client: Optional[httpx.Client] = None

    def check_health(self) -> Dict[str, Any]:
        """
        Polls the ESP32-S3 /health endpoint to verify network reachability,
        WiFi signal strength (RSSI), battery voltage, and free heap memory.
        Automatically triggers network auto-discovery if the configured IP is unreachable.

        Returns:
            Dict[str, Any]: Device telemetry dictionary or offline status report.
        """
        try:
            with httpx.Client(timeout=min(self.timeout, 2.5)) as client:
                resp = client.get(f"{self.base_url}/health")
                if resp.status_code == 200 and "buddy_esp32" in resp.text:
                    self.is_connected = True
                    self.last_contact = time.time()
                    return resp.json()
        except Exception:
            pass

        # Attempt auto-discovery across mDNS & local subnet ARP table
        discovered = self.discover_esp32()
        if discovered:
            return discovered

        self.is_connected = False
        return {"status": "offline", "error": f"Cannot reach ESP32 at {self.base_url}"}

    def discover_esp32(self) -> Optional[Dict[str, Any]]:
        """
        Locates the ESP32-S3 via mDNS (buddy.local) or local subnet ARP table candidates.
        Automatically updates base_url and synchronizes RGBController upon finding the board.

        Returns:
            Optional[Dict[str, Any]]: Telemetry payload from newly discovered device, or None if undiscovered.
        """
        candidates = ["http://buddy.local"]
        try:
            import subprocess
            out = subprocess.check_output("arp -a", shell=True, text=True, errors="replace")
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0].count(".") == 3:
                    ip = parts[0]
                    if not (ip.startswith("224.") or ip.endswith(".255") or ip.startswith("127.")):
                        candidates.append(f"http://{ip}")
        except Exception:
            pass

        seen = {self.base_url}
        for cand in candidates:
            if cand in seen:
                continue
            seen.add(cand)
            try:
                with httpx.Client(timeout=0.8) as client:
                    resp = client.get(f"{cand}/health")
                    if resp.status_code == 200 and "buddy_esp32" in resp.text:
                        logger.info(f"[ESP32 Discovery] Located ESP32 at {cand} (switched from {self.base_url})")
                        self.base_url = cand
                        self.is_connected = True
                        self.last_contact = time.time()
                        try:
                            from .rgb_controller import rgb_controller
                            rgb_controller.base_url = cand
                        except Exception:
                            pass
                        return resp.json()
            except Exception:
                continue
        return None

    def set_state(
        self,
        state: str,
        amplitude: float = 0.0,
        bass: Optional[float] = None,
        mid: Optional[float] = None,
        treble: Optional[float] = None
    ) -> bool:
        """
        Updates robot visual state (IDLE, LISTENING, THINKING, SPEAKING, ERROR) and audio reactivity bands.

        Args:
            state: Target operational state string.
            amplitude: Overall RMS audio amplitude (0.0 to 1.0).
            bass: Low-frequency energy level.
            mid: Mid-frequency energy level.
            treble: High-frequency energy level.

        Returns:
            bool: True if ESP32 acknowledged state transition with HTTP 200.
        """
        payload = {
            "state": state,
            "amplitude": round(amplitude, 3),
            "bass": round(bass or 0.0, 3),
            "mid": round(mid or 0.0, 3),
            "treble": round(treble or 0.0, 3)
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/api/state",
                    json=payload,
                    headers={"Connection": "close"}
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to set ESP32 state: {e}")
            return False

    def update_display(self, title: str, body: str) -> bool:
        """
        Sends an informational card or announcement to the ST7789 TFT display.

        Args:
            title: Header / title string to render.
            body: Body message or announcement text.

        Returns:
            bool: True if display successfully refreshed.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/api/display",
                    data={"title": title, "body": body},
                    headers={"Connection": "close"}
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to update ESP32 display: {e}")
            return False

    def trigger_chime(self) -> bool:
        """
        Triggers the ESP32 hardware chime tone test via MAX98357A I2S DAC.

        Returns:
            bool: True if chime test succeeded.
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    f"{self.base_url}/api/chime",
                    headers={"Connection": "close"}
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to trigger chime: {e}")
            return False

    def stream_wav_to_speaker(self, audio_bytes: bytes, sample_rate: int = 24000) -> bool:
        """
        Decodes any incoming audio file (MP3 from Edge-TTS, WAV from Fish Audio, etc.)
        into signed 16-bit mono PCM and streams it directly to the ESP32 MAX98357A I2S DAC.
        
        Network & Audio Handling:
          - Uses PyAV for fast hardware/software decoding and resamples to exactly 24 kHz mono.
          - Employs dynamic stream timeout based on audio duration (length / byte_rate).
          - Enforces 'Connection: close' to ensure single-threaded ESP32 WebServer releases socket.
          - Features a non-blocking circuit breaker with brief 2.0s cooldown on failure.

        Args:
            audio_bytes: Raw audio byte buffer (MP3 or WAV).
            sample_rate: Target PCM sample rate in Hz (default: 24000).

        Returns:
            bool: True if audio stream was completely delivered to the speaker.
        """
        if time.time() - self._last_speaker_fail < 2.0:
            return False
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
            except Exception:
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

            client = httpx.Client(timeout=httpx.Timeout(stream_timeout, connect=5.0))
            with self._streaming_lock:
                self._active_stream_client = client
            try:
                url = f"{self.base_url}/api/speak/raw"
                headers = {
                    "Content-Type": "application/octet-stream",
                    "Connection": "close"
                }
                resp = client.post(
                    url,
                    content=raw_pcm,
                    headers=headers
                )
                if resp.status_code == 404:
                    resp = client.post(
                        f"{self.base_url}/api/speak",
                        content=raw_pcm,
                        headers=headers
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
            self._last_speaker_fail = time.time()
            logger.warning(f"Failed to stream audio to ESP32 speaker: {e}")
            return False

    def stop_speaker(self, target_state: str = "IDLE", reset_display: bool = True) -> bool:
        """
        Immediately halts speech playback on ESP32 hardware and transitions display & LED.
        Aborts any active HTTP chunked upload stream from the PC side and flushes ESP32 I2S DMA buffers.

        Args:
            target_state: Visual state to set after halting (default: "IDLE").
            reset_display: Whether to return the ST7789 display to idle face mode.

        Returns:
            bool: True if stop signal was acknowledged.
        """
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
                resp = client.post(
                    f"{self.base_url}/api/stop?state={state_val}&idle=1",
                    headers={"Connection": "close"}
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Failed to send stop signal to ESP32: {e}")
            return False

    def fetch_mic_recording(self, seconds: int = 3) -> Optional[bytes]:
        """
        Downloads a recorded WAV clip from the ESP32 INMP441 microphone over Wi-Fi.
        Supports both the dedicated /api/mic/record endpoint and chunked /api/mic fallback.

        Args:
            seconds: Duration of audio capture in seconds (default: 3).

        Returns:
            Optional[bytes]: RIFF WAVE formatted 16kHz audio buffer, or None on failure.
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
        """
        Wraps raw linear PCM audio bytes in a standard 44-byte RIFF/WAVE container.

        Args:
            pcm_data: Raw signed 16-bit PCM bytes.
            sample_rate: Sampling frequency in Hz (default: 16000).
            channels: Channel count (1 for mono, 2 for stereo).
            bits_per_sample: Bit depth per sample (default: 16).

        Returns:
            bytes: Valid RIFF WAVE file binary.
        """
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
