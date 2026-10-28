"""
BUDDY — Local Development Server Launcher
Starts both the FastAPI backend and Vite frontend concurrently.
"""

import sys
import os
import shutil
import subprocess
import time
import urllib.request
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

VENV_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)

UVICORN_BIN = BASE_DIR / ".venv" / "Scripts" / "uvicorn.exe"
if not UVICORN_BIN.exists():
    UVICORN_BIN = "uvicorn"


def is_ollama_running(url: str = "http://127.0.0.1:11434/api/tags") -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Buddy-Dev"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_installed_ollama_models(url: str = "http://127.0.0.1:11434/api/tags") -> list:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Buddy-Dev"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []


def ensure_ollama_server() -> subprocess.Popen | None:
    """Ensures the local Ollama LLM server is running for on-device reasoning."""
    if is_ollama_running():
        models = get_installed_ollama_models()
        print(f"🦙 Ollama server is already running on http://127.0.0.1:11434 (Installed models: {', '.join(models) or 'none'})")
        return None

    # Search for ollama executable
    ollama_path = shutil.which("ollama")
    if not ollama_path:
        local_cand = Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe"
        if local_cand.exists():
            ollama_path = str(local_cand)

    if not ollama_path:
        print("⚠️ Warning: 'ollama' executable not found on PATH. The local LLM will not be available until installed.")
        return None

    print(f"🦙 Starting Ollama server in background: {ollama_path} serve ...")
    try:
        proc = subprocess.Popen(
            [ollama_path, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        # Wait up to 10s for server to bind port
        for _ in range(20):
            time.sleep(0.5)
            if is_ollama_running():
                models = get_installed_ollama_models()
                print(f"✅ Ollama server is online and ready! (Models: {', '.join(models) or 'none'})")
                return proc
        print("⚠️ Warning: Ollama server started but did not respond on 127.0.0.1:11434 within 10 seconds.")
        return proc
    except Exception as e:
        print(f"⚠️ Failed to auto-launch Ollama server: {e}")
        return None


def main():
    print("=" * 65)
    print("🤖 Starting BUDDY — Smart AI College Reception Robot")
    print("=" * 65)
    print(f"Backend directory:  {BACKEND_DIR}")
    print(f"Frontend directory: {FRONTEND_DIR}")
    print()

    # 0. Ensure Ollama Local Model Server is running
    ollama_proc = ensure_ollama_server()
    print()

    # 1. Start FastAPI backend
    backend_cmd = [
        str(UVICORN_BIN),
        "app.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ]
    print(f"Starting Backend on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BACKEND_DIR))

    # Give backend a moment to initialize
    time.sleep(1.5)

    # 2. Start Vite frontend
    frontend_cmd = ["npm.cmd" if sys.platform == "win32" else "npm", "run", "dev"]
    print(f"Starting Frontend on http://localhost:5173 ...")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(FRONTEND_DIR))

    print()
    print("✨ All services are running!")
    print("👉 Open in your browser: http://localhost:5173")
    print("👉 Backend API docs:     http://127.0.0.1:8000/docs")
    print("Press Ctrl+C to terminate both servers.")
    print("=" * 65)

    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping BUDDY servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        if ollama_proc:
            ollama_proc.terminate()
        print("Servers stopped.")


if __name__ == "__main__":
    main()
