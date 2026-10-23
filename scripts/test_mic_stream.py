#!/usr/bin/env python3
"""
BUDDY AI — Test Microphone Stream & PC Transcription (Test 8 Tool)

Verifies the complete hardware-to-AI voice pipeline:
1. Pings the ESP32-S3 HTTP REST server (/api/health) to confirm network connectivity and Wi-Fi RSSI.
2. Triggers an on-demand audio capture from the INMP441 I2S microphone (/api/record?seconds=N).
3. Receives standard 16 kHz 16-bit mono RIFF WAV audio over HTTP binary transport.
4. Persists the audio file to data/audio/test_esp32_mic.wav.
5. Feeds the raw PCM stream directly into the local GPU-accelerated faster-whisper STT engine.
"""

import sys
import argparse
from pathlib import Path
import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.hardware.esp32_client import esp32_client
from app.voice.transcription import transcribe_audio_file


def main():
    parser = argparse.ArgumentParser(
        description="Test ESP32-S3 INMP441 Microphone Audio Stream and PC Whisper Transcription"
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://192.168.1.5",
        help="Base URL or IP address of the ESP32-S3 hardware (e.g., http://192.168.1.5)"
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=3,
        help="Recording duration in seconds (default: 3 seconds)"
    )
    args = parser.parse_args()

    esp32_client.base_url = args.url.rstrip("/")

    print("==================================================================")
    print("  BUDDY AI — Microphone Audio Transport & Transcription Test     ")
    print(f"  Target: {esp32_client.base_url}")
    print("==================================================================")

    # 1. Health Check
    print("[1/3] Pinging ESP32...")
    health = esp32_client.check_health()
    if health.get("status") != "ok":
        print(f"[Error] ESP32 not responding at {esp32_client.base_url}. Verify Wi-Fi IP.")
        sys.exit(1)
    print(f"  -> ESP32 Online! RSSI: {health.get('rssi')} dBm")

    # 2. Record from INMP441
    print(f"\n[2/3] Recording {args.seconds} seconds from INMP441 microphone...")
    print("  >>> Speak clearly into the microphone now! <<<")
    wav_bytes = esp32_client.fetch_mic_recording(seconds=args.seconds)
    if not wav_bytes:
        print("[Error] Failed to capture audio from ESP32.")
        sys.exit(1)

    out_wav = PROJECT_ROOT / "data" / "audio" / "test_esp32_mic.wav"
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    out_wav.write_bytes(wav_bytes)
    print(f"  -> Audio saved: {out_wav} ({len(wav_bytes):,} bytes)")

    # 3. Transcribe with Whisper
    print("\n[3/3] Running Whisper Speech Recognition...")
    result = transcribe_audio_file(out_wav)
    print("\n==================================================================")
    print(f"  TRANSCRIPTION: \"{result.get('text', '').strip()}\"")
    print(f"  Language:      {result.get('language')}")
    print(f"  Confidence:    {result.get('confidence', 0.0):.2f}")
    print("==================================================================")


if __name__ == "__main__":
    main()
