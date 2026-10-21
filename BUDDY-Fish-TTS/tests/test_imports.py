"""
Tests that core modules import cleanly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_imports():
    from app.config import tts_config
    assert tts_config is not None
    assert tts_config.TEMPERATURE == 0.7

    from app.tts_engine import FishTTSEngine
    engine = FishTTSEngine()
    assert engine is not None
