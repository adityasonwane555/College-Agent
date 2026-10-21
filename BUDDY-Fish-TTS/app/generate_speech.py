"""
CLI utility to generate speech using FishTTSEngine.
"""

import argparse
import sys
from pathlib import Path
if __package__ is None or __package__ == "":
    base_dir = Path(__file__).resolve().parent.parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    from app.tts_engine import FishTTSEngine
else:
    from .tts_engine import FishTTSEngine


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Generate speech using Fish Audio S2 Pro locally.")
    parser.add_argument("--text", "-t", type=str, required=True, help="Text to synthesize")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output WAV path")
    parser.add_argument("--prompt-audio", "-pa", type=str, default=None, help="Path to voice reference audio")
    parser.add_argument("--prompt-text", "-pt", type=str, default=None, help="Transcript of voice reference audio")
    parser.add_argument("--temp", type=float, default=0.7, help="Generation temperature")

    args = parser.parse_args()

    engine = FishTTSEngine()
    try:
        print(f"Synthesizing: \"{args.text}\"")
        res = engine.generate(
            text=args.text,
            output_path=args.output,
            prompt_audio=args.prompt_audio,
            prompt_text=args.prompt_text,
            temperature=args.temp
        )

        print("\n✅ Generation Succeeded!")
        print(f"  • Output file:      {res['output_path']}")
        print(f"  • File size:        {res['file_size_bytes'] / 1024:.1f} KB")
        print(f"  • Audio duration:   {res['duration_seconds']}s")
        print(f"  • Generation time:  {res['generation_time_seconds']}s")
        print(f"  • Real-time factor: {res['real_time_factor']}x")
        print(f"  • GPU Memory:       {res['gpu_memory_used_mb']} MB")
    except Exception as e:
        print(f"\n❌ Synthesis failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
