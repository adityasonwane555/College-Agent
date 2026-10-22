import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.voice.transcription import transcribe_audio_file

tests = ["raw_apcoer", "hyphenated", "spaced", "spaced_dots", "commas"]
for t in tests:
    f = Path(f"data/audio/tests/edge_{t}.mp3")
    if f.exists():
        res = transcribe_audio_file(f)
        print(f"[{t:14}] -> Whisper heard: '{res.get('text')}'")
