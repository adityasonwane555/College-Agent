import os
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = WORKSPACE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    # Ollama Local AI Configuration (Primary On-Device Engine)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_TIMEOUT_SECONDS: float = 60.0
    USE_LOCAL_LLM_FIRST: bool = True
    ENABLE_FAST_PATH: bool = False

    # Google Gemini Cloud AI Integration (Online Information Extraction & Web Research)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_ENABLED: bool = True

    # Groq Cloud AI Integration (High-Speed LLM & Web Research)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_ENABLED: bool = True

    # Fallback to smart simulated assistant if Ollama is not yet downloaded/running
    MOCK_AI_FALLBACK: bool = True

    # Database - Always point to workspace data/buddy.db
    DATABASE_PATH: str = str((DATA_DIR / "buddy.db").resolve())

    @field_validator("DATABASE_PATH", mode="after")
    @classmethod
    def resolve_database_path(cls, v: str) -> str:
        p = Path(v)
        if not p.is_absolute():
            # Resolve relative to root workspace dir
            cand = (WORKSPACE_DIR / p).resolve()
            if cand.exists():
                return str(cand)
            return str((DATA_DIR / "buddy.db").resolve())
        return str(p.resolve())

    # Internet Web Search
    WEB_SEARCH_ENABLED: bool = True
    SEARXNG_BASE_URL: str = "http://localhost:8080"
    WEB_SEARCH_TIMEOUT_SECONDS: float = 10.0

    # Speech Recognition (faster-whisper on NVIDIA CUDA)
    STT_MODEL: str = "base"
    STT_DEVICE: str = "cuda"
    STT_LANGUAGE: str = "en"

    # Text to Speech (edge_tts, fish_audio_api, or local fish_audio)
    TTS_ENABLED: bool = True
    TTS_ENGINE: str = "fish_audio_api"
    EDGE_TTS_VOICE: str = "en-US-AnaNeural"
    FISH_AUDIO_API_KEY: str = ""
    FISH_AUDIO_MODEL: str = "s2.1-pro-free"
    FISH_AUDIO_REFERENCE_ID: str = "73770ea2927d46c19e461e7e812b2f95"
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

    # ESP32-S3 Hardware RGB LED Controller
    ESP32_LED_ENABLED: bool = True
    ESP32_LED_URL: str = "http://192.168.1.100"  # Configurable in .env or via Web UI
    ESP32_LED_TIMEOUT_SECONDS: float = 1.0
    ESP32_LED_TOKEN: str = ""

    model_config = SettingsConfigDict(
        env_file=str(WORKSPACE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
