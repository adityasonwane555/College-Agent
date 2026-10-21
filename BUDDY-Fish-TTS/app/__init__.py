"""
BUDDY-Fish-TTS Application Package
"""

from .tts_engine import FishTTSEngine
from .config import tts_config

__all__ = ["FishTTSEngine", "tts_config"]
