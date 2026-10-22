#!/usr/bin/env python3
"""
BUDDY AI — Test Speaker Audio Stream (Test 9 Tool)
Generates synthesized neural speech on the PC and streams it to the MAX98357A speaker on the ESP32.
"""

import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.hardware.esp32_client import esp32_client
from app.voice.synthesis import synthesize_speech


def main():
    parser = argparse.ArgumentParser(description="Test ESP32 MAX98357A Speaker Audio Stream")
    parser.add_argument("--url", type=str, default="http://192.168.1.5", help="ESP32 IP or URL")
    parser.add_argument("--text", type=str, default="Welcome to Anantrao Pawar College of Engineering and Research, Pune. How can I assist you today?", help="Text to speak")
    args = parser.parse_args()

    esp32_client.base_url = args.url.rstrip("/")

    print("==================================================================")
    print("  BUDDY AI — Speaker Audio Streaming Test (PC -> ESP32)          ")
    print(f"  Target: {esp32_client.base_url}")
    print("==================================================================")

    # 1. Health Check
    print("[1/3] Pinging ESP32...")
    health = esp32_client.check_health()
    if health.get("status") != "ok":
        print(f"[Error] ESP32 not responding at {esp32_client.base_url}. Verify Wi-Fi IP.")
        sys.exit(1)
    print(f"  -> ESP32 Online! RSSI: {health.get('rssi')} dBm")

    # 2. Update Display
    print("\n[2/3] Updating ST7789 Display...")
    esp32_client.update_display("BUDDY Speaking", args.text[:60] + "...")

    # 3. Synthesize Speech
    print(f"\n[3/3] Synthesizing speech: \"{args.text}\"...")
    tts_result = synthesize_speech(args.text)
    file_path = tts_result.get("file_path")
    if not file_path or not Path(file_path).exists():
        print("[Error] Failed to generate speech WAV file.")
        sys.exit(1)

    wav_bytes = Path(file_path).read_bytes()
    print(f"  -> Synthesized WAV ({len(wav_bytes):,} bytes). Streaming to MAX98357A speaker...")

    # 4. Stream to ESP32
    success = esp32_client.stream_wav_to_speaker(wav_bytes)
    if success:
        print("\n==================================================================")
        print("  >>> AUDIO STREAMED & PLAYED SUCCESSFULLY! PASS <<<              ")
        print("==================================================================")
    else:
        print("[Error] Failed to stream audio to ESP32 speaker.")


if __name__ == "__main__":
    main()
