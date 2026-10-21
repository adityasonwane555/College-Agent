import os
import re
import sys
import json
import uuid
import time
import httpx
import subprocess
import array
import struct
import asyncio
import edge_tts
import concurrent.futures
from pathlib import Path
from typing import Dict, Any, Optional
from ..config import settings, WORKSPACE_DIR
from .audio_utils import AUDIO_DIR

# Keep track of internal server process if launched by backend
_internal_s2_process: Optional[subprocess.Popen] = None


async def _synthesize_edge_tts(text: str, out_file: Path, voice: str):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_file))


def run_edge_tts_synthesis(text: str, out_file: Path, voice: str = "en-US-AnaNeural") -> bool:
    """Ultra-fast neural speech synthesis via edge-tts (1-2s response time, zero GPU VRAM)."""
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(asyncio.run, _synthesize_edge_tts(text, out_file, voice)).result(timeout=12.0)
        return out_file.exists() and out_file.stat().st_size > 500
    except Exception as e:
        print(f"[Edge-TTS] Synthesis error: {e}")
        return False


def is_fish_tts_server_alive() -> bool:
    """Checks if the persistent s2.cpp server is responding."""
    try:
        with httpx.Client(timeout=1.5) as client:
            # s2 server returns 404 or 400 on root/unsupported paths, indicating socket is alive
            client.get(f"{settings.FISH_TTS_SERVER_URL}/")
            return True
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
    except Exception:
        return True


def ensure_fish_tts_server() -> bool:
    """Ensures the persistent s2.cpp HTTP server is running for low-latency synthesis."""
    global _internal_s2_process
    if is_fish_tts_server_alive():
        return True

    if _internal_s2_process and _internal_s2_process.poll() is None:
        return True

    s2_bin = WORKSPACE_DIR / "BUDDY-Fish-TTS" / "s2.cpp" / "build" / "Release" / "s2.exe"
    model_path = WORKSPACE_DIR / "BUDDY-Fish-TTS" / "models" / "s2-pro-q5_k_m.gguf"
    tokenizer_path = WORKSPACE_DIR / "BUDDY-Fish-TTS" / "models" / "tokenizer.json"

    if s2_bin.exists() and model_path.exists() and tokenizer_path.exists():
        try:
            env = os.environ.copy()
            env["PATH"] = f"{s2_bin.parent};{env.get('PATH', '')}"
            _internal_s2_process = subprocess.Popen(
                [
                    str(s2_bin),
                    "-m", str(model_path),
                    "-t", str(tokenizer_path),
                    "--server",
                    "-H", "127.0.0.1",
                    "-P", "3030",
                    "-v", "1",
                    "-ngl", "36",
                    "--voice", "buddy",
                    "--voice-dir", str(WORKSPACE_DIR / "BUDDY-Fish-TTS" / "voices"),
                    "-threads", str(min(os.cpu_count() or 4, 8))
                ],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Give the server a few seconds to initialize weights
            time.sleep(4.0)
            return True
        except Exception as e:
            print(f"[Fish-TTS] Failed to auto-launch s2.exe server: {e}")
            return False
    return False


def extract_spoken_text(text: str, max_chars: int = 1500) -> str:
    """
    Cleans markdown formatting, citations, URLs, and labels from response text
    and preserves complete, fluent natural dialogue for voice synthesis across full stops.
    """
    clean = re.sub(r'\[DEMO DATA\]', '', text, flags=re.IGNORECASE)
    clean = re.sub(r'Here is what I found from the college records:?\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'Based on the official (?:college )?records:?\s*', '', clean, flags=re.IGNORECASE)
    # Strip document citation tags like [Source: filename | Page ... | Section: ...]
    clean = re.sub(r'\[Source:[^\]]*\]', '', clean, flags=re.IGNORECASE)
    # Strip markdown links and raw URLs
    clean = re.sub(r'\[.*?\]\(.*?\)', '', clean)
    clean = re.sub(r'https?://\S+', '', clean)
    # Clean bullet points into smooth conversational transitions
    clean = re.sub(r'^\s*[-*•]\s*', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'[*#_`>~|]', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    if not clean:
        return ""

    if len(clean) <= max_chars:
        return clean

    # Slices at the last sentence end before max_chars only if exceptionally lengthy
    cutoff = clean[:max_chars]
    last_punct = max(cutoff.rfind('.'), cutoff.rfind('!'), cutoff.rfind('?'))
    if last_punct > 100:
        return cutoff[:last_punct + 1].strip()
    return cutoff.strip()


def convert_float32_wav_to_pcm16(raw: bytes) -> bytes:
    """
    Converts 32-bit IEEE float WAV (produced by s2.cpp, tag 3) to standard
    16-bit integer PCM WAV (tag 1) at 44.1 kHz, which plays natively in all web browsers.
    """
    if len(raw) < 44 or raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        return raw
    tag = struct.unpack('<H', raw[20:22])[0]
    if tag != 3:  # Not IEEE float, return as-is
        return raw
    channels = struct.unpack('<H', raw[22:24])[0]
    rate = struct.unpack('<I', raw[24:28])[0]
    idx = raw.find(b'data')
    if idx == -1:
        return raw
    data_size = struct.unpack('<I', raw[idx+4:idx+8])[0]
    float_bytes = raw[idx+8:idx+8+data_size]
    float_array = array.array('f', float_bytes)
    # Clamp and convert float [-1.0, 1.0] to int16 [-32767, 32767]
    int16_array = array.array('h', (max(-32767, min(32767, int(s * 32767.0))) for s in float_array))
    pcm_data = int16_array.tobytes()
    byte_rate = rate * channels * 2
    block_align = channels * 2
    fmt_chunk = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, channels, rate, byte_rate, block_align, 16)
    data_chunk = struct.pack('<4sI', b'data', len(pcm_data)) + pcm_data
    riff_size = 4 + len(fmt_chunk) + len(data_chunk)
    riff_header = struct.pack('<4sI4s', b'RIFF', riff_size, b'WAVE')
    return riff_header + fmt_chunk + data_chunk


def synthesize_speech(text: str) -> Dict[str, Any]:
    """
    Synthesizes speech using the high-fidelity Fish Audio S2 Pro model.
    Prioritizes the persistent s2.cpp HTTP server for rapid synthesis (~15s).
    Falls back to direct CLI execution via FishTTSEngine if the server is offline.
    """
    if not settings.TTS_ENABLED:
        return {
            "enabled": False,
            "method": "disabled",
            "message": "Text-to-speech is disabled in configuration."
        }

    clean_text = extract_spoken_text(text)
    if not clean_text:
        return {
            "enabled": False,
            "method": "empty",
            "message": "No speakable text found."
        }

    # 1. Ultra-Fast High-Fidelity Edge-TTS Engine (Default, ~1.5s response, zero VRAM)
    if getattr(settings, "TTS_ENGINE", "edge_tts") == "edge_tts":
        edge_filename = AUDIO_DIR / f"tts_{uuid.uuid4().hex[:8]}.mp3"
        voice_name = getattr(settings, "EDGE_TTS_VOICE", "en-US-AnaNeural")
        if run_edge_tts_synthesis(clean_text, edge_filename, voice_name):
            return {
                "enabled": True,
                "method": "edge_tts_neural",
                "audio_url": f"/api/voice/audio/{edge_filename.name}",
                "file_path": str(edge_filename),
                "text": clean_text
            }

    output_filename = AUDIO_DIR / f"tts_{uuid.uuid4().hex[:8]}.wav"

    # 2. Local Fish Audio S2 Pro Server (for full offline / custom neural model)
    server_url = f"{settings.FISH_TTS_SERVER_URL}/generate"
    try:
        ensure_fish_tts_server()
        word_count = len(clean_text.split())
        # Balanced token allocation: ~8 frames per word + 40 frames buffer.
        # Keeps speech snappy on CPU (~20-25s) while giving full headroom so words are never cut.
        max_tokens = min(max(word_count * 8 + 40, 90), 220)
        voices_dir = WORKSPACE_DIR / "BUDDY-Fish-TTS" / "voices"
        params_dict = {
            "max_new_tokens": max_tokens,
            "temperature": 0.7,
            "voice": "buddy",
            "voice_dir": str(voices_dir)
        }
        params_json = json.dumps(params_dict)

        with httpx.Client(timeout=120.0) as client:
            for attempt in range(4):
                resp = client.post(
                    server_url,
                    files={
                        "text": (None, clean_text),
                        "params": (None, params_json)
                    }
                )
                if resp.status_code == 200 and len(resp.content) > 1000:
                    pcm16_bytes = convert_float32_wav_to_pcm16(resp.content)
                    output_filename.write_bytes(pcm16_bytes)
                    return {
                        "enabled": True,
                        "method": "fish_audio_s2_pro",
                        "audio_url": f"/api/voice/audio/{output_filename.name}",
                        "file_path": str(output_filename),
                        "text": clean_text
                    }
                elif resp.status_code == 503:
                    # Server is currently generating another request, pause and retry
                    time.sleep(2.0)
    except Exception as e:
        print(f"[Fish-TTS] Server request failed: {e}")

    # 2. Direct CLI fallback ONLY if server is completely offline (avoids duplicate CPU-thrashing processes)
    if not is_fish_tts_server_alive():
        try:
            s2_bin = WORKSPACE_DIR / "BUDDY-Fish-TTS" / "s2.cpp" / "build" / "Release" / "s2.exe"
            model_path = WORKSPACE_DIR / "BUDDY-Fish-TTS" / "models" / "s2-pro-q5_k_m.gguf"
            tokenizer_path = WORKSPACE_DIR / "BUDDY-Fish-TTS" / "models" / "tokenizer.json"

            if s2_bin.exists() and model_path.exists() and tokenizer_path.exists():
                env = os.environ.copy()
                env["PATH"] = f"{s2_bin.parent};{env.get('PATH', '')}"
                cmd = [
                    str(s2_bin),
                    "-m", str(model_path),
                    "-t", str(tokenizer_path),
                    "--voice", "buddy",
                    "--voice-dir", str(WORKSPACE_DIR / "BUDDY-Fish-TTS" / "voices"),
                    "-text", clean_text,
                    "-o", str(output_filename),
                    "-max-tokens", str(max_tokens),
                    "-v", "1",
                    "-ngl", "36",
                    "--trim-silence"
                ]
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=120.0)
                if output_filename.exists() and output_filename.stat().st_size > 1000:
                    pcm16_bytes = convert_float32_wav_to_pcm16(output_filename.read_bytes())
                    output_filename.write_bytes(pcm16_bytes)
                    return {
                        "enabled": True,
                        "method": "fish_audio_s2_pro_cli",
                        "audio_url": f"/api/voice/audio/{output_filename.name}",
                        "file_path": str(output_filename),
                        "text": clean_text
                    }
        except Exception as e:
            print(f"[Fish-TTS] Direct s2.exe CLI failed: {e}")

    # 3. Graceful fallback if model is somehow unavailable
    return {
        "enabled": True,
        "method": "browser_fallback",
        "audio_url": None,
        "text": clean_text,
        "message": "Fish Audio S2 Pro model offline. Web Speech API fallback active."
    }
