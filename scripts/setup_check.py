"""
BUDDY Reception Agent — Setup & Environment Verification Utility
Checks all prerequisites, dependencies, models, and database files.
"""

import sys
import shutil
from pathlib import Path

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"

sys.path.insert(0, str(BACKEND_DIR))


def check_item(title: str, passed: bool, remediation: str = ""):
    symbol = "[PASS]" if passed else "[NOTICE]"
    print(f" {symbol} {title}")
    if not passed and remediation:
        print(f"    -> Remediation: {remediation}")


def main():
    print("=" * 65)
    print("BUDDY -- System Setup & Diagnostics Check")
    print("=" * 65)

    # 1. Python Version
    py_ver = sys.version_info
    py_pass = py_ver.major == 3 and py_ver.minor >= 10
    check_item(
        f"Python Version ({py_ver.major}.{py_ver.minor}.{py_ver.micro})",
        py_pass,
        "Install Python 3.10 or newer from python.org"
    )

    # 2. Node & NPM
    node_bin = shutil.which("node")
    npm_bin = shutil.which("npm")
    check_item(
        f"Node.js Runtime ({node_bin or 'Not found'})",
        bool(node_bin),
        "Download Node.js 18+ from https://nodejs.org"
    )
    check_item(
        f"NPM Package Manager ({npm_bin or 'Not found'})",
        bool(npm_bin),
        "NPM comes bundled with Node.js"
    )

    # 3. Backend Python Packages
    packages = ["fastapi", "uvicorn", "pydantic", "httpx", "pytest", "faster_whisper", "pypdf", "bs4"]
    for pkg in packages:
        try:
            __import__(pkg)
            check_item(f"Python Package '{pkg}'", True)
        except ImportError:
            check_item(
                f"Python Package '{pkg}'",
                False,
                f"Run: pip install -r backend/requirements.txt"
            )

    # 4. Ollama Availability
    try:
        import httpx
        from app.config import settings
        ollama_url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
        resp = httpx.get(ollama_url, timeout=1.5)
        if resp.status_code == 200:
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            check_item(f"Ollama Local Server ({settings.OLLAMA_BASE_URL})", True)
            model_found = any(settings.OLLAMA_MODEL in m for m in models)
            check_item(
                f"Configured Model '{settings.OLLAMA_MODEL}'",
                model_found,
                f"Run: ollama run {settings.OLLAMA_MODEL}"
            )
        else:
            check_item(
                f"Ollama Local Server ({settings.OLLAMA_BASE_URL})",
                False,
                f"Ollama returned HTTP {resp.status_code}. Ensure Ollama is running."
            )
    except Exception:
        check_item(
            "Ollama Local Server (http://localhost:11434)",
            False,
            "Install Ollama from https://ollama.com and run: ollama run qwen3:8b (Simulated Reception AI fallback is active)."
        )

    # 5. Database Initialization
    try:
        from app.database.repository import repo
        from app.database.seed import seed_database
        from app.documents.ingestion import ingest_sample_documents
        seed_database()
        ingest_sample_documents(DATA_DIR / "sample_documents")
        depts = repo.list_departments()
        docs = repo.list_documents()
        check_item(
            f"SQLite Database & Sample College Data ({len(depts)} Depts, {len(docs)} Docs)",
            len(depts) > 0,
            "Run: python backend/app/database/seed.py"
        )
    except Exception as e:
        check_item("SQLite Database Initialization", False, f"Error: {e}")

    # 6. Frontend Dependencies
    node_modules = FRONTEND_DIR / "node_modules"
    check_item(
        "Frontend Dependencies (node_modules)",
        node_modules.exists(),
        "Run: cd frontend && npm install"
    )

    # 7. Text-To-Speech (Piper)
    piper_bin = shutil.which("piper")
    check_item(
        f"Piper Local TTS Binary ({piper_bin or 'Not installed in PATH'})",
        bool(piper_bin),
        "Piper is optional. The application automatically uses browser Web Speech API fallback when Piper is not present."
    )

    print("=" * 65)
    print("Diagnostics check finished. You can start the dev servers now!")
    print("Backend:  .venv\\Scripts\\uvicorn app.main:app --reload (in backend/)")
    print("Frontend: npm run dev (in frontend/)")
    print("=" * 65)


if __name__ == "__main__":
    main()
