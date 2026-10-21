import os
import sys
import wave
import time
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from .config import tts_config


class FishTTSEngine:
    """
    Local Text-To-Speech engine using Fish Audio S2 Pro GGUF and s2.cpp.
    Provides fast, high-quality offline inference without paid cloud APIs.
    """

    def __init__(self, config=None):
        self.config = config or tts_config
        self.server_process: Optional[subprocess.Popen] = None
        self.is_loaded: bool = False

    def validate_prerequisites(self) -> Dict[str, Any]:
        """Validates existence of binary, model weights, and tokenizer."""
        binary = Path(self.config.S2_BINARY_PATH)
        model = Path(self.config.MODEL_PATH)
        tokenizer = Path(self.config.TOKENIZER_PATH)

        issues = []
        if not binary.exists():
            issues.append(f"s2.exe binary not found at '{binary}'. Please build s2.cpp first.")
        if not model.exists():
            issues.append(f"GGUF model file not found at '{model}'. Run scripts/download_model.py.")
        if not tokenizer.exists():
            issues.append(f"tokenizer.json not found at '{tokenizer}'.")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "binary_path": str(binary),
            "model_path": str(model),
            "tokenizer_path": str(tokenizer)
        }

    def get_gpu_memory_mb(self) -> Optional[float]:
        """Queries current NVIDIA GPU memory usage via nvidia-smi."""
        try:
            cmd = ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(result.stdout.strip().split("\n")[0])
        except Exception:
            return None

    def load(self, start_server: bool = False) -> Dict[str, Any]:
        """
        Initializes the TTS engine.
        Optionally launches persistent s2 HTTP server for instant multi-turn synthesis.
        """
        check = self.validate_prerequisites()
        if not check["valid"]:
            raise RuntimeError(f"Cannot load FishTTSEngine: {'; '.join(check['issues'])}")

        if start_server and not self.server_process:
            cmd = [
                self.config.S2_BINARY_PATH,
                "-m", self.config.MODEL_PATH,
                "-t", self.config.TOKENIZER_PATH,
                "--server",
                "-H", self.config.SERVER_HOST,
                "-P", str(self.config.SERVER_PORT)
            ]
            self.server_process = subprocess.Popen(cmd)
            time.sleep(2.0)  # Allow model initialization

        self.is_loaded = True
        return {
            "status": "ready",
            "model": Path(self.config.MODEL_PATH).name,
            "server_mode": bool(self.server_process)
        }

    def generate(
        self,
        text: str,
        output_path: Optional[str] = None,
        prompt_audio: Optional[str] = None,
        prompt_text: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generates spoken audio from text.
        
        Args:
            text: Non-empty string to synthesize.
            output_path: Destination WAV file path.
            prompt_audio: Optional reference audio for voice cloning.
            prompt_text: Optional transcript of the reference audio.
            temperature: Sampling temperature.
        """
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Synthesis text cannot be empty or whitespace.")

        check = self.validate_prerequisites()
        if not check["valid"]:
            raise FileNotFoundError(f"Missing required model assets: {'; '.join(check['issues'])}")

        # Determine output path
        if not output_path:
            out_dir = Path(self.config.OUTPUT_DIRECTORY)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_file = out_dir / f"tts_{int(time.time())}.wav"
        else:
            out_file = Path(output_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)

        # Build CLI command
        cmd = [
            self.config.S2_BINARY_PATH,
            "-m", self.config.MODEL_PATH,
            "-t", self.config.TOKENIZER_PATH,
            "-text", clean_text,
            "-o", str(out_file),
            "-temp", str(temperature if temperature is not None else self.config.TEMPERATURE),
            "-threads", str(self.config.THREADS)
        ]

        if self.config.NORMALIZE:
            cmd.append("--normalize")
        if self.config.TRIM_SILENCE:
            cmd.append("--trim-silence")

        if prompt_audio and Path(prompt_audio).exists():
            cmd.extend(["-pa", str(prompt_audio)])
            if prompt_text:
                cmd.extend(["-pt", prompt_text])

        # Record metrics
        gpu_before = self.get_gpu_memory_mb()
        start_time = time.perf_counter()

        # Run inference
        env = os.environ.copy()
        # Add DLL directory to PATH
        s2_dir = Path(self.config.S2_BINARY_PATH).parent
        env["PATH"] = f"{s2_dir};{env.get('PATH', '')}"

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )

        gen_time = time.perf_counter() - start_time
        gpu_after = self.get_gpu_memory_mb()

        if proc.returncode != 0:
            error_output = proc.stderr or proc.stdout or "Unknown engine error"
            raise RuntimeError(f"s2.exe inference failed (exit code {proc.returncode}):\n{error_output}")

        if not out_file.exists() or out_file.stat().st_size == 0:
            raise RuntimeError(f"Output audio file '{out_file}' was not created or is 0 bytes.")

        # Read WAV metadata (supports standard PCM and IEEE Float 32-bit formats)
        duration_sec = 0.0
        sample_rate = 44100
        try:
            with wave.open(str(out_file), "rb") as wf:
                frames = wf.getnframes()
                sample_rate = wf.getframerate()
                duration_sec = round(frames / float(sample_rate), 2)
        except Exception:
            try:
                import struct
                with open(str(out_file), "rb") as f:
                    riff_header = f.read(12)
                    if riff_header[:4] == b"RIFF" and riff_header[8:12] == b"WAVE":
                        byte_rate = 0
                        while True:
                            chunk_hdr = f.read(8)
                            if len(chunk_hdr) < 8:
                                break
                            chunk_id, chunk_size = struct.unpack("<4sI", chunk_hdr)
                            if chunk_id == b"fmt ":
                                fmt_data = f.read(chunk_size)
                                tag, channels, rate, b_rate, block_align, bits = struct.unpack("<HHIIHH", fmt_data[:16])
                                sample_rate = rate
                                byte_rate = b_rate
                            elif chunk_id == b"data":
                                if byte_rate > 0:
                                    duration_sec = round(chunk_size / float(byte_rate), 2)
                                f.seek(chunk_size, 1)
                            else:
                                f.seek(chunk_size, 1)
            except Exception:
                pass

        rtf = round(gen_time / duration_sec, 2) if duration_sec > 0 else 0.0

        return {
            "success": True,
            "output_path": str(out_file),
            "file_size_bytes": out_file.stat().st_size,
            "duration_seconds": duration_sec,
            "sample_rate": sample_rate,
            "generation_time_seconds": round(gen_time, 2),
            "real_time_factor": rtf,
            "gpu_memory_used_mb": gpu_after if gpu_after is not None else "N/A",
            "model_variant": Path(self.config.MODEL_PATH).name
        }

    def get_status(self) -> Dict[str, Any]:
        """Returns engine configuration and runtime health status."""
        check = self.validate_prerequisites()
        return {
            "ready": check["valid"],
            "model_loaded": self.is_loaded,
            "server_active": self.server_process is not None and self.server_process.poll() is None,
            "model_path": self.config.MODEL_PATH,
            "model_size_bytes": Path(self.config.MODEL_PATH).stat().st_size if Path(self.config.MODEL_PATH).exists() else 0,
            "gpu_memory_used_mb": self.get_gpu_memory_mb(),
            "issues": check["issues"]
        }

    def unload(self):
        """Terminates persistent server process and releases resources."""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=3)
            except Exception:
                self.server_process.kill()
            self.server_process = None
        self.is_loaded = False
