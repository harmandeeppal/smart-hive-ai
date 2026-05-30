"""
Download Smart Hive AI model weights from Hugging Face Hub.

Run from project root before starting any service:
    python scripts/download_models.py

Or set HF_TOKEN env var for CI/Railway (no interactive login needed):
    HF_TOKEN=hf_xxx python scripts/download_models.py
"""

import os
import sys
from pathlib import Path

HF_REPO_ID = "harmandeeppal/smart-hive-ai-models"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"

MODELS = [
    "vision_model.pt",
    "audio_model.pkl",
]


def main():
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("Installing huggingface_hub ...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub", "-q"])
        from huggingface_hub import hf_hub_download

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    token = os.getenv("HF_TOKEN")  # optional for public repos

    all_ok = True
    for filename in MODELS:
        dest = MODELS_DIR / filename
        if dest.exists():
            print(f"  Already present: {filename}  ({dest.stat().st_size / 1e6:.1f} MB)")
            continue
        print(f"  Downloading {filename} from {HF_REPO_ID} ...")
        try:
            path = hf_hub_download(
                repo_id=HF_REPO_ID,
                filename=filename,
                local_dir=str(MODELS_DIR),
                token=token,
            )
            size_mb = Path(path).stat().st_size / 1e6
            print(f"  Saved: {path}  ({size_mb:.1f} MB)")
        except Exception as e:
            print(f"  ERROR downloading {filename}: {e}")
            all_ok = False

    if not all_ok:
        sys.exit(1)
    print("\nAll models ready.")


if __name__ == "__main__":
    main()
