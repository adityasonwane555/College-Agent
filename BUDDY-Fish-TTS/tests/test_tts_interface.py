import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from app.tts_engine import FishTTSEngine
from app.config import TTSConfig


def test_empty_text_validation():
    engine = FishTTSEngine()
    with pytest.raises(ValueError) as exc:
        engine.generate("   ")
    assert "empty" in str(exc.value).lower()


def test_missing_model_validation(tmp_path):
    custom_cfg = TTSConfig(
        MODEL_PATH=str(tmp_path / "non_existent.gguf"),
        TOKENIZER_PATH=str(tmp_path / "tokenizer.json")
    )
    engine = FishTTSEngine(custom_cfg)
    check = engine.validate_prerequisites()
    assert not check["valid"]
    assert len(check["issues"]) > 0

    with pytest.raises(FileNotFoundError):
        engine.generate("Test speech")


def test_get_status_structure():
    engine = FishTTSEngine()
    status = engine.get_status()
    assert "ready" in status
    assert "model_loaded" in status
    assert "server_active" in status
    assert "gpu_memory_used_mb" in status
