"""
Upload Smart Hive AI models to Hugging Face Hub.

Run once (from project root, with smart-hive-demo env active):
    python scripts/upload_models_to_hf.py

Prerequisites:
    pip install huggingface_hub
    huggingface-cli login   (or set HF_TOKEN env var)

What this uploads:
    models/vision_model.pt   — YOLOv8 queen bee detection model
    models/audio_model.pkl   — scikit-learn beehive audio classifier
"""

import sys
from pathlib import Path
from huggingface_hub import HfApi, create_repo

HF_REPO_ID = "harmandeeppal/smart-hive-ai-models"
ROOT       = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"

UPLOAD_FILES = [
    ("vision_model.pt",  "YOLOv8 fine-tuned queen bee detection (CPU-compatible)"),
    ("audio_model.pkl",  "scikit-learn beehive audio health classifier"),
]


def main():
    api = HfApi()

    # Verify login
    try:
        user = api.whoami()
        print(f"Logged in as: {user['name']}")
    except Exception:
        print("ERROR: Not logged in to Hugging Face.")
        print("Run:  huggingface-cli login")
        sys.exit(1)

    # Create repo if it doesn't exist
    try:
        create_repo(HF_REPO_ID, repo_type="model", exist_ok=True, private=False)
        print(f"Repository ready: https://huggingface.co/{HF_REPO_ID}")
    except Exception as e:
        print(f"ERROR creating repo: {e}")
        sys.exit(1)

    # Upload each model file
    for filename, description in UPLOAD_FILES:
        local_path = MODELS_DIR / filename
        if not local_path.exists():
            print(f"SKIP: {filename} not found at {local_path}")
            continue

        size_mb = local_path.stat().st_size / (1024 * 1024)
        print(f"\nUploading {filename} ({size_mb:.1f} MB) ...")
        api.upload_file(
            path_or_fileobj=str(local_path),
            path_in_repo=filename,
            repo_id=HF_REPO_ID,
            repo_type="model",
            commit_message=f"Upload {filename}: {description}",
        )
        print(f"  Done → https://huggingface.co/{HF_REPO_ID}/blob/main/{filename}")

    # Upload a model card
    model_card = f"""---
license: mit
tags:
  - yolo
  - object-detection
  - audio-classification
  - beekeeping
  - edge-ai
  - raspberry-pi
---

# Smart Hive AI — Model Weights

Models used by the [Smart Hive AI](https://github.com/harmandeeppal/smart-hive-ai) project,
an edge-first beehive monitoring system running on Raspberry Pi 4.

## Models

### `vision_model.pt`
YOLOv8n fine-tuned on beehive imagery for queen bee detection.
- Input: 640×480 JPEG frames (via MQTT)
- Confidence threshold: 0.35 (demo) / 0.50 (production)
- CPU-compatible, no GPU required

### `audio_model.pkl`
scikit-learn pipeline (MFCC features → classifier) for beehive health classification.
- Input: 30-second audio windows at 22 050 Hz
- Classes: `queen_present`, `queen_absent`
- Trained with numpy 2.x / scikit-learn 1.7.2

## Usage

```python
from huggingface_hub import hf_hub_download

vision_path = hf_hub_download("{HF_REPO_ID}", "vision_model.pt")
audio_path  = hf_hub_download("{HF_REPO_ID}", "audio_model.pkl")
```
"""
    api.upload_file(
        path_or_fileobj=model_card.encode(),
        path_in_repo="README.md",
        repo_id=HF_REPO_ID,
        repo_type="model",
        commit_message="Add model card",
    )
    print(f"\n Model card uploaded.")
    print(f"\n All models live at: https://huggingface.co/{HF_REPO_ID}")


if __name__ == "__main__":
    main()
