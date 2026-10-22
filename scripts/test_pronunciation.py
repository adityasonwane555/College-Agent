import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.voice.synthesis import extract_spoken_text

test_samples = [
    "Welcome to APCOER Pune!",
    "Anantrao Pawar College of Engineering & Research (APCOER), Pune.",
    "APCOER's campus is located in Parvati, Pune.",
    "The institution was established under ABMSP trust.",
    "APCOER is affiliated with SPPU and approved by DTE and AICTE.",
    "The HOD of Computer Engineering is Dr. Rama Gaikwad.",
    "You can contact the TPO for campus placements.",
    "All details about A-P-C-O-E-R are available here.",
    "Visit apcoer and abmsp today!"
]

for s in test_samples:
    spoken = extract_spoken_text(s)
    print(f"Original: {s}")
    print(f"Spoken:   {spoken}")
    print("-" * 50)
