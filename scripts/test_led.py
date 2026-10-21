#!/usr/bin/env python3
"""
BUDDY AI - ESP32 RGB LED Hardware Test Utility
Use this script to verify Wi-Fi communication and test every LED state on the ESP32-S3.

Examples:
    python scripts/test_led.py --status
    python scripts/test_led.py --state SPEAKING
    python scripts/test_led.py --cycle
    python scripts/test_led.py --url http://192.168.1.105 --cycle
"""

import sys
import time
import argparse
import httpx

VALID_STATES = [
    "BOOTING",
    "IDLE",
    "LISTENING",
    "THINKING",
    "SPEAKING",
    "INTERRUPTED",
    "ERROR",
    "COMPLETED"
]

STATE_DESCRIPTIONS = {
    "BOOTING": "Brief Cyan animation",
    "IDLE": "Gentle Dim Cyan/Blue breathing",
    "LISTENING": "Electric Blue attentive pulse",
    "THINKING": "Warm Golden Amber breathing",
    "SPEAKING": "Purple/Magenta animated breathing with vocal modulation",
    "INTERRUPTED": "Gentle Orange transition (600ms) -> IDLE",
    "ERROR": "Red pulsing alert",
    "COMPLETED": "Emerald Green acknowledgment (450ms) -> IDLE"
}


def test_status(url: str):
    print(f"\n[?] Checking ESP32 health at {url}/health ...")
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{url}/health")
            if resp.status_code == 200:
                print(f"[+] Health check OK: {resp.json()}")
            else:
                print(f"[-] Health check failed (HTTP {resp.status_code}): {resp.text}")

            resp_status = client.get(f"{url}/api/status")
            if resp_status.status_code == 200:
                print(f"[+] Device Status: {resp_status.json()}")
            else:
                print(f"[-] Status endpoint returned HTTP {resp_status.status_code}")
    except Exception as e:
        print(f"[!] Connection failed: {e}")
        print("    -> Make sure your ESP32-S3 is powered on, connected to the same Wi-Fi,")
        print("       and check the IP printed in its Serial Monitor.")


def send_state(
    url: str,
    state: str,
    amplitude: float = 0.0,
    bass: float = None,
    mid: float = None,
    treble: float = None
) -> bool:
    target_url = f"{url}/api/state"
    payload = {"state": state, "amplitude": amplitude}
    if bass is not None:
        payload["bass"] = bass
    if mid is not None:
        payload["mid"] = mid
    if treble is not None:
        payload["treble"] = treble

    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.post(target_url, json=payload)
            if resp.status_code == 200:
                print(f"[+] State successfully sent: {state} ({STATE_DESCRIPTIONS.get(state, '')})")
                return True
            else:
                print(f"[-] ESP32 error (HTTP {resp.status_code}): {resp.text}")
                return False
    except Exception as e:
        print(f"[!] Failed to send state to {target_url}: {e}")
        return False


def run_cycle(url: str, delay_sec: float = 2.5):
    print(f"\n=== Cycling through all BUDDY LED states on {url} ===")
    for st in VALID_STATES:
        print(f"\n--> Activating state: {st} ({STATE_DESCRIPTIONS.get(st, '')})")
        send_state(url, st, amplitude=0.8 if st == "SPEAKING" else 0.0)
        time.sleep(delay_sec)

    print("\n--> Returning to IDLE...")
    send_state(url, "IDLE")
    print("[+] Test cycle completed successfully!")


def run_equalizer_demo(url: str, duration_sec: float = 12.0):
    import math
    print(f"\n=== Running High/Low Note Speaker Equalizer Demo on {url} ({duration_sec}s) ===")
    print("Watch the LED:")
    print("  - Vowels / Low notes: Punchy Crimson/Magenta subwoofer kicks")
    print("  - Speech body: Vibrant Royal Purple/Violet cadence")
    print("  - Consonants / High notes: Crisp Electric Cyan/White staccato sparks")
    print("-------------------------------------------------------------------------")

    t_start = time.time()
    tick = 0
    try:
        while time.time() - t_start < duration_sec:
            tick += 1
            t = time.time() - t_start

            # Natural vocal modulation patterns
            # Low notes (vowel bass resonance: "ah", "oh", "oo")
            bass = 0.3 + 0.7 * abs(math.sin(t * 4.2))
            # Mid notes (speech body & syllabic cadence: 3.5 syllables per sec)
            mid = 0.4 + 0.6 * abs(math.cos(t * 7.5))
            # High notes (crisp consonant bursts: "s", "t", "ch", "k")
            treble = 0.95 if (tick % 4 == 0) else (0.15 + 0.35 * abs(math.sin(t * 13.0)))
            # Master volume envelope
            amp = 0.5 + 0.5 * abs(math.sin(t * 5.0))

            send_state(url, "SPEAKING", amplitude=amp, bass=bass, mid=mid, treble=treble)
            time.sleep(0.08) # ~12 updates per second

    except KeyboardInterrupt:
        pass

    print("\n--> Equalizer demo finished. Returning to IDLE...")
    send_state(url, "IDLE")
    print("[+] Equalizer test complete!")


def main():
    import os
    from pathlib import Path

    # Try reading default URL from .env if present
    default_url = "http://10.51.80.118"
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("ESP32_LED_URL="):
                default_url = line.split("=", 1)[1].strip()

    parser = argparse.ArgumentParser(description="Test BUDDY AI ESP32 RGB LED Controller")
    parser.add_argument("--url", default=default_url, help=f"ESP32 IP or base URL (default from .env: {default_url})")
    parser.add_argument("--state", choices=VALID_STATES, help="Send a single specific state to the ESP32")
    parser.add_argument("--amplitude", type=float, default=0.0, help="Optional audio amplitude (0.0 - 1.0) for SPEAKING state")
    parser.add_argument("--bass", type=float, default=None, help="Low notes intensity (0.0 - 1.0)")
    parser.add_argument("--mid", type=float, default=None, help="Mid notes intensity (0.0 - 1.0)")
    parser.add_argument("--treble", type=float, default=None, help="High notes intensity (0.0 - 1.0)")
    parser.add_argument("--status", action="store_true", help="Check device health and status")
    parser.add_argument("--cycle", action="store_true", help="Cycle through all animation states in sequence")
    parser.add_argument("--equalizer", action="store_true", help="Run real-time speaker equalizer simulation (high & low notes)")

    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    if args.status:
        test_status(base_url)
    elif args.equalizer:
        run_equalizer_demo(base_url)
    elif args.state:
        send_state(base_url, args.state, args.amplitude, args.bass, args.mid, args.treble)
    elif args.cycle:
        run_cycle(base_url)
    else:
        test_status(base_url)
        print("\nTip: Use --equalizer to see the high/low speaker effect, or --cycle to view all animations.")


if __name__ == "__main__":
    main()
