import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from ..config import settings

# 1. Patch PyAV for newer versions where metadata_errors was removed from av.open
try:
    import av
    _orig_av_open = av.open

    def _safe_av_open(*args, **kwargs):
        kwargs.pop("metadata_errors", None)
        return _orig_av_open(*args, **kwargs)

    av.open = _safe_av_open
except Exception:
    pass

# 2. Register NVIDIA CUDA and cuDNN DLL directories for Windows Python
def _setup_cuda_dlls():
    cuda_x64 = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.4\bin\x64")
    if cuda_x64.exists() and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(cuda_x64))
            os.environ["PATH"] = f"{cuda_x64};{os.environ.get('PATH', '')}"
        except Exception:
            pass

    cuda_bin = Path(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.4\bin")
    if cuda_bin.exists() and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(cuda_bin))
            os.environ["PATH"] = f"{cuda_bin};{os.environ.get('PATH', '')}"
        except Exception:
            pass

    # Virtualenv nvidia package DLLs (cublas, cudnn, etc.)
    site_packages = Path(sys.prefix) / "Lib" / "site-packages"
    for pkg in ["cublas", "cudnn", "cuda_nvrtc", "cuda_runtime"]:
        bin_dir = site_packages / "nvidia" / pkg / "bin"
        if bin_dir.exists() and hasattr(os, "add_dll_directory"):
            try:
                os.add_dll_directory(str(bin_dir))
                os.environ["PATH"] = f"{bin_dir};{os.environ.get('PATH', '')}"
            except Exception:
                pass

_setup_cuda_dlls()

_whisper_model = None


def is_whisper_installed() -> bool:
    """Checks whether faster-whisper package is installed without downloading model weights."""
    try:
        import faster_whisper
        return True
    except ImportError:
        return False


def get_whisper_model(force_cpu: bool = False):
    """Lazily loads the faster-whisper model only when transcription is explicitly requested."""
    global _whisper_model
    if force_cpu or _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            device = "cpu" if force_cpu else settings.STT_DEVICE
            compute_type = "int8" if device == "cpu" else "float16"
            try:
                model = WhisperModel(
                    settings.STT_MODEL,
                    device=device,
                    compute_type=compute_type
                )
                if not force_cpu:
                    _whisper_model = model
                return model
            except Exception as cuda_err:
                if device == "cuda":
                    print(f"[Whisper] CUDA load failed ({cuda_err}), falling back to CPU int8...")
                    _whisper_model = WhisperModel(settings.STT_MODEL, device="cpu", compute_type="int8")
                    return _whisper_model
                else:
                    raise cuda_err
        except Exception as e:
            print(f"[Whisper] faster-whisper model ({settings.STT_MODEL}) not initialized: {e}")
            if not force_cpu:
                _whisper_model = False
            return None
    return _whisper_model


def transcribe_audio_file(file_path: Path) -> Dict[str, Any]:
    """Transcribes an audio file locally using faster-whisper with automatic CUDA -> CPU fallback."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        return {
            "success": False,
            "text": "",
            "error": "Audio file is empty or missing."
        }

    if not is_whisper_installed():
        return {
            "success": False,
            "text": "",
            "error": "faster-whisper is not installed. Please install it or use browser speech recognition."
        }

    # Attempt 1: Default device (CUDA if available)
    try:
        model = get_whisper_model()
        if not model:
            return {
                "success": False,
                "text": "",
                "error": "faster-whisper model could not be loaded."
            }

        segments, info = model.transcribe(
            str(file_path),
            language=settings.STT_LANGUAGE if settings.STT_LANGUAGE != "auto" else None,
            beam_size=5
        )
        transcribed_text = " ".join([seg.text.strip() for seg in segments]).strip()

        return {
            "success": True,
            "text": transcribed_text,
            "detected_language": info.language,
            "duration": info.duration
        }
    except Exception as primary_err:
        print(f"[Whisper] Primary transcription attempt failed: {primary_err}")
        # Attempt 2: Transparent CPU fallback if CUDA throws runtime/DLL errors
        try:
            print("[Whisper] Retrying with CPU int8 fallback...")
            cpu_model = get_whisper_model(force_cpu=True)
            if cpu_model:
                global _whisper_model
                _whisper_model = cpu_model  # Cache CPU model permanently to avoid CUDA error overhead on future calls
                segments, info = cpu_model.transcribe(
                    str(file_path),
                    language=settings.STT_LANGUAGE if settings.STT_LANGUAGE != "auto" else None,
                    beam_size=3
                )
                transcribed_text = " ".join([seg.text.strip() for seg in segments]).strip()
                return {
                    "success": True,
                    "text": transcribed_text,
                    "detected_language": info.language,
                    "duration": info.duration,
                    "fallback": "cpu_int8"
                }
        except Exception as cpu_err:
            print(f"[Whisper] CPU fallback also failed: {cpu_err}")

        return {
            "success": False,
            "text": "",
            "error": f"Transcription error: {str(primary_err)}"
        }
