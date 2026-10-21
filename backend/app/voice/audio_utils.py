import os
import wave
import struct
import math
from pathlib import Path
from ..config import DATA_DIR

AUDIO_DIR = DATA_DIR / "audio_temp"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def create_beep_wav(filename: Path, duration_sec: float = 1.0, freq_hz: float = 440.0) -> Path:
    """Creates a basic standard PCM WAV file for fallback audio testing."""
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
