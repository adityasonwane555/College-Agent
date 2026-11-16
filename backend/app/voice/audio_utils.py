"""
BUDDY AI 2.0 — Audio Processing & Waveform Utilities

Architecture & Audio Pipeline:
  - Audio Staging Directory:
      - Initializes persistent temp storage (AUDIO_DIR at data/audio_temp) for recording uploads and synthesized TTS clips.
  - Synthetic Tone Generation:
      - Generates smooth, windowed sine wave PCM audio with sinusoidal attack/decay envelopes for auditory testing and hardware diagnostics.
  - Acoustic Energy & Metric Analysis:
      - Computes Root-Mean-Square (RMS) energy across 16-bit mono linear PCM streams for real-time speech activity detection
        and visual modulation of the ESP32-S3 RGB LED ring.
  - Header Inspection:
      - Reads RIFF header parameters to extract exact track durations in seconds without loading raw audio payloads into RAM.
"""

import os
import wave
import struct
import math
from pathlib import Path
from ..config import DATA_DIR

AUDIO_DIR = DATA_DIR / "audio_temp"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def create_beep_wav(filename: Path, duration_sec: float = 1.0, freq_hz: float = 440.0) -> Path:
    """
    Creates a standard 16-bit mono PCM WAV file with a soft sinusoidal envelope for auditory hardware testing.

    Args:
        filename: Destination path for the generated WAV file.
        duration_sec: Tone duration in seconds (default: 1.0s).
        freq_hz: Frequency of the sine tone in Hertz (default: 440.0Hz / A4).

    Returns:
        Path: Path to the generated WAV audio file.
    """
    sample_rate = 16000
    num_samples = int(duration_sec * sample_rate)

    with wave.open(str(filename), 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        for i in range(num_samples):
            # Soft sine wave with fade in/out
            envelope = math.sin(math.pi * i / num_samples)
            sample = int(16000 * envelope * math.sin(2.0 * math.pi * freq_hz * (i / sample_rate)))
            wav_file.writeframes(struct.pack('<h', sample))

    return filename


def calculate_pcm_rms(pcm_data: bytes) -> float:
    """
    Calculates normalized Root-Mean-Square (RMS) amplitude from 16-bit signed linear PCM bytes.

    Args:
        pcm_data: Raw signed 16-bit mono PCM byte sequence.

    Returns:
        float: Normalized RMS audio energy value between 0.0 and 1.0.
    """
    if not pcm_data or len(pcm_data) < 2:
        return 0.0

    count = len(pcm_data) // 2
    format_str = f"<{count}h"
    try:
        shorts = struct.unpack(format_str, pcm_data[: count * 2])
    except struct.error:
        return 0.0

    sum_squares = sum(s * s for s in shorts)
    mean_square = sum_squares / count
    rms = math.sqrt(mean_square)
    # 32768 is max amplitude for signed 16-bit integers
    normalized = min(1.0, rms / 32768.0)
    return round(normalized, 4)


def get_wav_duration(wav_path: Path) -> float:
    """
    Inspects RIFF headers to compute the exact duration of a WAV file in seconds.

    Args:
        wav_path: Path to the target WAV file on disk.

    Returns:
        float: Duration in seconds, or 0.0 if file is unreadable.
    """
    if not wav_path.exists():
        return 0.0
    try:
        with wave.open(str(wav_path), 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate <= 0:
                return 0.0
            return round(frames / float(rate), 3)
    except Exception:
        return 0.0
