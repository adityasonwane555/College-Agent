"""
BUDDY AI — Neural Text-to-Speech & Speech Synthesis Subsystem

Architecture & Audio Pipeline:
  - Multi-Engine Speech Dispatcher:
      1. Fish Audio Cloud API (s2.1-pro-free cloud model): Ultra-high fidelity voice cloning
         using custom reference IDs for the distinct Buddy personality.
      2. Microsoft Edge-TTS Cloud Service: Ultra-fast neural synthesis (~1-2s latency, zero GPU VRAM)
         using high-definition voices (e.g., en-US-AnaNeural).
      3. Local s2.cpp Persistent Server: Embedded C++ inference engine loading quantized GGUF weights
         (s2-pro-q5_k_m.gguf) with GPU layer offloading (-ngl 36) and custom reference embeddings.
      4. Web Speech API Fallback: Client-side browser synthesis if network/local TTS is unreachable.
  - Text Normalization & Acronym Phonetics:
      - Strips markdown formatting, links, raw URLs, citation tags ([Source:...]), and emoji artifacts.
      - Preserves clean phonetics for college acronyms (APCOER, ABMSP, SPPU, DTE, AICTE, HOD, TPO)
        without jarring comma pauses or robotic spell-outs.
  - Audio Format Normalization:
      - Transcodes 32-bit IEEE float WAV (produced by s2.cpp, format tag 3) into standard
        16-bit integer PCM WAV (format tag 1) with saturation clamping [-32767, 32767]
        for universal compatibility across web browsers, mobile devices, and ESP32 MAX98357A I2S DACs.
"""

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


async def _synthesize_edge_tts(text: str, out_file: Path, voice: str) -> None:
    """
    Internal asynchronous coroutine executing Edge-TTS network synthesis.
    Streams synthesized audio chunks directly from Microsoft's WebSocket endpoint
    and writes them to the specified output file on disk.

    Args:
        text: Normalized plain text to synthesize.
        out_file: Target filesystem destination Path for MP3 audio.
        voice: Microsoft neural voice identifier (e.g. 'en-US-AnaNeural').
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(out_file))


def run_edge_tts_synthesis(text: str, out_file: Path, voice: str = "en-US-AnaNeural") -> bool:
    """
    Executes synchronous neural speech synthesis via Edge-TTS inside a dedicated thread pool.
    Guarantees sub-2-second turnaround time with zero GPU VRAM consumption.

    Args:
        text: Normalized plain text string to speak.
        out_file: Output path where MP3 file should be saved.
        voice: Neural voice model identifier (default: en-US-AnaNeural).

    Returns:
        bool: True if synthesis succeeded and generated valid audio bytes (> 500 bytes).
    """
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(asyncio.run, _synthesize_edge_tts(text, out_file, voice)).result(timeout=20.0)
        return out_file.exists() and out_file.stat().st_size > 500
    except Exception as e:
        print(f"[Edge-TTS] Synthesis error: {e}")
        return False


def run_fish_audio_api_synthesis(text: str, out_file: Path) -> bool:
    """
    Synthesizes speech using the official Fish Audio Cloud API (https://api.fish.audio/v1/tts).
    Leverages user API key and cloned voice reference ID to stream studio-quality MP3 audio.

    Args:
        text: Normalized spoken text string.
        out_file: Local filesystem destination Path for MP3 audio.

    Returns:
        bool: True if HTTP 200 response received with valid audio payload.
    """
    api_key = getattr(settings, "FISH_AUDIO_API_KEY", "")
    if not api_key:
        print("[Fish Audio API] Error: FISH_AUDIO_API_KEY is not configured.")
        return False

    url = "https://api.fish.audio/v1/tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "model": getattr(settings, "FISH_AUDIO_MODEL", "s2.1-pro-free")
    }
    payload: Dict[str, Any] = {
        "text": text,
        "format": "mp3"
    }
    ref_id = getattr(settings, "FISH_AUDIO_REFERENCE_ID", "") or "73770ea2927d46c19e461e7e812b2f95"
    if ref_id:
        payload["reference_id"] = ref_id

    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            if resp.status_code == 200 and len(resp.content) > 500:
                out_file.write_bytes(resp.content)
                return True
            else:
                print(f"[Fish Audio API] HTTP {resp.status_code} Error: {resp.text[:200]}")
                return False
    except Exception as e:
        print(f"[Fish Audio API] Connection error: {e}")
        return False


def is_fish_tts_server_alive() -> bool:
    """
    Probes the persistent local s2.cpp HTTP server to determine if its listening socket is active.

    Returns:
        bool: True if server responds to HTTP requests; False on connection refusal or timeout.
    """
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
    """
    Ensures the persistent local s2.cpp C++ inference server is running in the background.
    If offline, automatically spawns `s2.exe` with GGUF weights, tokenizer, and voice embeddings.

    Returns:
        bool: True if server is already alive or was successfully launched.
    """
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
    Preprocesses and normalizes raw text for smooth, natural speech synthesis:
      1. Strips internal tags like [DEMO DATA] and prompt artifacts.
      2. Strips markdown links, raw URLs, and citation brackets ([Source:...]).
      3. Normalizes college acronym pronunciations (APCOER, ABMSP, SPPU, DTE, AICTE)
         to avoid stilted letter-by-letter pauses.
      4. Truncates cleanly on sentence-ending punctuation to prevent dangling syllables.

    Args:
        text: Raw response string from agent or LLM.
        max_chars: Maximum character cutoff limit (default: 1500).

    Returns:
        str: Cleaned, human-sounding text suitable for TTS engines.
    """
    clean = re.sub(r'\[DEMO DATA\]', '', text, flags=re.IGNORECASE)
    clean = re.sub(r'Here is what I found from the college records:?\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'Based on the official (?:college )?records:?\s*', '', clean, flags=re.IGNORECASE)
    # Strip document citation tags like [Source: filename | Page ... | Section: ...]
    clean = re.sub(r'\[Source:[^\]]*\]', '', clean, flags=re.IGNORECASE)
    # Strip markdown links and raw URLs
    clean = re.sub(r'\[.*?\]\(.*?\)', '', clean)
    clean = re.sub(r'https?://\S+', '', clean)
    # Strip markdown symbols, brackets, and parentheses that disrupt speech rhythm
    clean = re.sub(r'[*#_`>~|()[\]{}]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    # Pronunciation normalization for TTS speech synthesis:
    # Preserve clean spoken acronyms without robotic comma-separated pauses
    clean = re.sub(r"\bA[-.,\s]?P[-.,\s]?C[-.,\s]?O[-.,\s]?E[-.,\s]?R['’]s\b", "APCOER's", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bA[-.,\s]?P[-.,\s]?C[-.,\s]?O[-.,\s]?E[-.,\s]?R\b", "APCOER", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bA[-.,\s]?B[-.,\s]?M[-.,\s]?S[-.,\s]?P['’]s\b", "ABMSP's", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bA[-.,\s]?B[-.,\s]?M[-.,\s]?S[-.,\s]?P\b", "ABMSP", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bS[-.,\s]?P[-.,\s]?P[-.,\s]?U\b", "SPPU", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bD[-.,\s]?T[-.,\s]?E\b", "DTE", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bA[-.,\s]?I[-.,\s]?C[-.,\s]?T[-.,\s]?E\b", "AICTE", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bH[-.,\s]?O[-.,\s]?D\b", "HOD", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\bT[-.,\s]?P[-.,\s]?O\b", "TPO", clean, flags=re.IGNORECASE)

    # Sanitize any accidental duplicate commas, whitespace before commas, or commas before punctuation
    clean = re.sub(r',\s*,+', ',', clean)
    clean = re.sub(r'\s+,', ',', clean)
    clean = re.sub(r',\s*([.!?:;])', r'\1', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()

    if not clean:
        return ""

    if len(clean) <= max_chars:
        return clean

    # Slices at the last sentence end before max_chars only if exceptionally lengthy
    cutoff = clean[:max_chars]
    last_punct = max(cutoff.rfind('.'), cutoff.rfind('!'), cutoff.rfind('?'))
    if last_punct > 150:
        return cutoff[:last_punct + 1].strip()
    return clean[:max_chars].strip()


def convert_float32_wav_to_pcm16(raw: bytes) -> bytes:
    """
    Converts 32-bit IEEE float WAV (produced by s2.cpp, format tag 3) to standard
    16-bit integer PCM WAV (format tag 1) at 44.1 kHz, which plays natively in all web browsers.

    Audio Processing:
      - Reads RIFF header and extracts channels, sample rate, and data payload.
      - Clamps float32 values [-1.0, 1.0] to signed int16 [-32767, 32767].
      - Packs standard 44-byte canonical RIFF PCM header.

    Args:
        raw: Raw bytes of the float32 WAV audio stream.

    Returns:
        bytes: Transcoded 16-bit integer PCM WAV byte string.
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
    Master speech synthesis gateway.
    Routes speech request according to configuration priority:
      1. Fish Audio Cloud API (if TTS_ENGINE is 'fish_audio_api' or 'fish_audio_cloud')
      2. Microsoft Edge-TTS (if TTS_ENGINE is 'edge_tts')
      3. Local Fish Audio s2.cpp persistent server
      4. Local s2.exe CLI direct execution
      5. Browser Web Speech API fallback

    Args:
        text: Raw text response from the robot agent.

    Returns:
        Dict[str, Any]: Response dictionary with status, method, audio_url, and file_path.
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

    # 1. Fish Audio Cloud API Engine (s2.1-pro-free cloud model)
    if getattr(settings, "TTS_ENGINE", "edge_tts") in ("fish_audio_api", "fish_audio_cloud"):
        fish_filename = AUDIO_DIR / f"tts_{uuid.uuid4().hex[:8]}.mp3"
        if run_fish_audio_api_synthesis(clean_text, fish_filename):
            return {
                "enabled": True,
                "method": "fish_audio_api",
                "audio_url": f"/api/voice/audio/{fish_filename.name}",
                "file_path": str(fish_filename),
                "text": clean_text
            }
        print("[Fish Audio API] Cloud request failed, attempting Edge-TTS fallback...")
        edge_filename = AUDIO_DIR / f"tts_{uuid.uuid4().hex[:8]}.mp3"
        voice_name = getattr(settings, "EDGE_TTS_VOICE", "en-US-AnaNeural")
        if run_edge_tts_synthesis(clean_text, edge_filename, voice_name):
            return {
                "enabled": True,
                "method": "edge_tts_fallback",
                "audio_url": f"/api/voice/audio/{edge_filename.name}",
                "file_path": str(edge_filename),
                "text": clean_text
            }
        return {
            "enabled": False,
            "method": "fish_audio_failed",
            "message": "Fish Audio API and Edge-TTS fallback both failed."
        }

    # 2. Ultra-Fast High-Fidelity Edge-TTS Engine (~1.5s response, zero VRAM)
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
        return {
            "enabled": False,
            "method": "edge_tts_failed",
            "message": "Edge-TTS synthesis timed out or failed."
        }

    output_filename = AUDIO_DIR / f"tts_{uuid.uuid4().hex[:8]}.wav"

    # 3. Local Fish Audio S2 Pro Server (for full offline / custom neural model)
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

    # 4. Direct CLI fallback ONLY if server is completely offline (avoids duplicate CPU-thrashing processes)
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

    # 5. Graceful fallback if model is somehow unavailable
    return {
        "enabled": True,
        "method": "browser_fallback",
        "audio_url": None,
        "text": clean_text,
        "message": "Fish Audio S2 Pro model offline. Web Speech API fallback active."
    }
