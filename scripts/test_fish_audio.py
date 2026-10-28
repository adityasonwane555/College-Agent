"""
BUDDY AI — Fish Audio Cloud API Benchmark & Test Script
Tests the Fish Audio Cloud API (https://api.fish.audio/v1/tts) with the configured key.
"""

import sys
import time
import httpx
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Adjust path to import backend config
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings

def test_fish_audio_tts(text: str, output_path: str = "welcome.mp3"):
    api_key = getattr(settings, "FISH_AUDIO_API_KEY", "")
    if not api_key:
        print("❌ Error: FISH_AUDIO_API_KEY is not set in .env or settings.")
        return False

    model = getattr(settings, "FISH_AUDIO_MODEL", "s2.1-pro-free")
    ref_id = getattr(settings, "FISH_AUDIO_REFERENCE_ID", "")

    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": model
    }
    payload = {
        "text": text,
        "format": "mp3"
    }
    if ref_id:
        payload["reference_id"] = ref_id

    print("=" * 60)
    print("🐟 Testing Fish Audio Cloud TTS API")
    print("=" * 60)
    print(f"Endpoint:  {url}")
    print(f"Model:     {model}")
    print(f"Voice ID:  {ref_id or '(default)'}")
    print(f"API Key:   {api_key[:12]}...{api_key[-6:]}")
    print(f"Text:      \"{text}\"")
    print(f"Output:    {output_path}")
    print()
    print("Connecting to Fish Audio Cloud...")

    start_time = time.time()
    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            elapsed = time.time() - start_time

            print(f"HTTP Status: {resp.status_code}")
            print(f"Latency:     {elapsed:.2f} seconds")

            if resp.status_code == 200:
                audio_bytes = resp.content
                out_p = Path(output_path)
                out_p.write_bytes(audio_bytes)
                print(f"Audio Size:  {len(audio_bytes):,} bytes ({len(audio_bytes) / 1024:.1f} KB)")
                print(f"✅ Success! Audio file written to: {out_p.resolve()}")

                # Try to inspect duration with PyAV
                try:
                    import av
                    container = av.open(str(out_p))
                    stream = container.streams.audio[0]
                    duration = float(stream.duration * stream.time_base) if stream.duration else 0.0
                    print(f"Sample Rate: {stream.sample_rate} Hz")
                    print(f"Channels:    {stream.channels}")
                    print(f"Duration:    {duration:.2f} seconds")
                    if duration > 0:
                        rtf = elapsed / duration
                        print(f"Real-Time Factor (RTF): {rtf:.2f}x ({'faster than real-time' if rtf < 1.0 else 'generation latency'})")
                except Exception:
                    pass

                print()
                print("✨ You can play this audio file directly in your media player.")
                return True
            else:
                print(f"❌ API Error: HTTP {resp.status_code}")
                print(f"Response: {resp.text[:300]}")
                return False

    except httpx.TimeoutException:
        print(f"❌ Timeout error: Fish Audio did not respond within 45 seconds.")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Fish Audio Cloud TTS API")
    parser.add_argument("--text", type=str, default="Hello! Welcome to Fish Audio.", help="Text to speak")
    parser.add_argument("--out", type=str, default="welcome.mp3", help="Output audio file path")
    args = parser.parse_args()

    test_fish_audio_tts(args.text, args.out)
