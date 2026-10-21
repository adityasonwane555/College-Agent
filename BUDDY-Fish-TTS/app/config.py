import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


class TTSConfig(BaseSettings):
    # Path to compiled s2.exe executable
    S2_BINARY_PATH: str = str(BASE_DIR / "s2.cpp" / "build" / "Release" / "s2.exe")

    # Model and Tokenizer
    MODEL_PATH: str = str(MODELS_DIR / "s2-pro-q5_k_m.gguf")
    TOKENIZER_PATH: str = str(MODELS_DIR / "tokenizer.json")

    # Output directory
    OUTPUT_DIRECTORY: str = str(OUTPUT_DIR)

    # Inference generation defaults
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.7
    TOP_K: int = 50
    MAX_TOKENS: int = 1024
    THREADS: int = 0  # 0 = auto-detect CPU threads
    NORMALIZE: bool = True
    TRIM_SILENCE: bool = True

    # Server mode (for keeping model persistent in memory)
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 3030

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


tts_config = TTSConfig()
