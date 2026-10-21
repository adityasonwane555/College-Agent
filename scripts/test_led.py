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


def send_state(url: str, state: str, amplitude: float = 0.0) -> bool:
    target_url = f"{url}/api/state"
    payload = {"state": state, "amplitude": amplitude}
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


def main():
    parser = argparse.ArgumentParser(description="Test BUDDY AI ESP32 RGB LED Controller")
    parser.add_argument("--url", default="http://192.168.1.100", help="ESP32 IP or base URL (e.g. http://192.168.1.105)")
    parser.add_argument("--state", choices=VALID_STATES, help="Send a single specific state to the ESP32")
    parser.add_argument("--amplitude", type=float, default=0.0, help="Optional audio amplitude (0.0 - 1.0) for SPEAKING state")
    parser.add_argument("--status", action="store_true", help="Check device health and status")
    parser.add_argument("--cycle", action="store_true", help="Cycle through all animation states in sequence")

    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    if args.status:
        test_status(base_url)
    elif args.state:
        send_state(base_url, args.state, args.amplitude)
    elif args.cycle:
        run_cycle(base_url)
    else:
        # Default action: check status and prompt
        test_status(base_url)
        print("\nTip: Use --cycle to view all animations, or --state <NAME> to set a specific state.")


if __name__ == "__main__":
    main()
