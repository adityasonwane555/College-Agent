"""
BUDDY — Local Development Server Launcher
Starts both the FastAPI backend and Vite frontend concurrently.
"""

import sys
import subprocess
import time
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


def main():
    print("=" * 65)
    print("🤖 Starting BUDDY — Smart AI College Reception Robot")
    print("=" * 65)
    print(f"Backend directory:  {BACKEND_DIR}")
    print(f"Frontend directory: {FRONTEND_DIR}")
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
    print("✨ Both servers are running!")
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
        print("Servers stopped.")


if __name__ == "__main__":
    main()
