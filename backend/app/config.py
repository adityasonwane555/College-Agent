import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = WORKSPACE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    # Ollama Local AI Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TIMEOUT_SECONDS: float = 45.0

    # Google Gemini AI Integration (Fast Cloud Reasoning)
    GEMINI_API_KEY: str = "AQ.Ab8RN6JpG7AZR3MwGV9mesuACdNifMuN4MYOdK8bVnKPWD1uMQ"
    GEMINI_MODEL: str = "gemini-flash-latest"
    GEMINI_ENABLED: bool = True

    # Fallback to smart simulated assistant if Ollama is not yet downloaded/running
    MOCK_AI_FALLBACK: bool = True

    # Database
    DATABASE_PATH: str = str(DATA_DIR / "buddy.db")

    # Internet Web Search
    WEB_SEARCH_ENABLED: bool = False
    SEARXNG_BASE_URL: str = "http://localhost:8080"
    WEB_SEARCH_TIMEOUT_SECONDS: float = 10.0

    # Speech Recognition (faster-whisper on NVIDIA CUDA)
    STT_MODEL: str = "base"
    STT_DEVICE: str = "cuda"
    STT_LANGUAGE: str = "en"

    # Text to Speech (edge_tts for instant sub-second neural voice, fish_audio for local S2 Pro)
    TTS_ENABLED: bool = True
    TTS_ENGINE: str = "edge_tts"
    EDGE_TTS_VOICE: str = "en-US-AnaNeural"
    FISH_TTS_SERVER_URL: str = "http://127.0.0.1:3030"
    FISH_TTS_DIR: str = str(WORKSPACE_DIR / "BUDDY-Fish-TTS")
    TTS_VOICE_PATH: str = ""
    TTS_PIPER_BINARY: str = "piper"

    # CORS and Server
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8000

    # Admin Security
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "buddyadmin2026"
    ADMIN_TOKEN_SECRET: str = "buddy-secret-token-key-2026"

    # Agent Limits
    MAX_TOOL_ITERATIONS: int = 5
    SESSION_MAX_HISTORY: int = 15

    model_config = SettingsConfigDict(
        env_file=str(WORKSPACE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
