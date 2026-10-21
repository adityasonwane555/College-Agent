"""
Downloads Fish Audio S2 Pro GGUF model from Hugging Face.
"""

import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID = "rodrigomt/s2-pro-gguf"
FILENAME = "s2-pro-q5_k_m.gguf"

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

target_file = MODELS_DIR / FILENAME

if target_file.exists() and target_file.stat().st_size > 1024 * 1024 * 1000:
    print(f"Model already downloaded: {target_file} ({target_file.stat().st_size / (1024**3):.2f} GB)")
    sys.exit(0)

print(f"Starting download of {FILENAME} from {REPO_ID} ...")
print(f"Target location: {target_file}")
print("This file is approximately 3.8 GB. Progress will be displayed below.")

try:
    downloaded_path = hf_hub_download(
        repo_id=REPO_ID,
        filename=FILENAME,
        local_dir=str(MODELS_DIR),
        local_dir_use_symlinks=False
    )
    print(f"\nDownload completed successfully: {downloaded_path}")
except Exception as e:
    print(f"\nDownload failed: {e}")
    sys.exit(1)
