#!/usr/bin/env bash
# Codespaces one-time setup — runs after container creation
set -e

echo "============================================"
echo "  Smart Hive AI — Codespaces Setup"
echo "============================================"

# System dependencies
echo ""
echo "Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
    mosquitto \
    libsndfile1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    > /dev/null 2>&1
echo "  Done."

# Create conda environment from demo/environment.yml
echo ""
echo "Creating conda environment (smart-hive-demo)..."
echo "  This installs PyTorch, scikit-learn, librosa, etc."
echo "  May take 5-10 minutes on first run..."
conda env create -f demo/environment.yml --quiet
echo "  Done."

# Copy .env.demo if it doesn't exist
if [ ! -f .env.demo ]; then
    cp demo/.env.demo.example .env.demo
    echo ""
    echo "Created .env.demo from template."
fi

# Generate sample audio (needed for audio waveform)
echo ""
echo "Generating demo audio (5 min bee colony sample)..."
conda run -n smart-hive-demo python demo/generate_sample_audio.py
echo "  Done."

# Generate sample video (needed for vision demo)
echo ""
echo "Generating demo video (1 min synthetic hive)..."
conda run -n smart-hive-demo python demo/generate_sample_video.py
echo "  Done."

# Download ML models from Hugging Face Hub
if [ -n "$HF_TOKEN" ]; then
    echo ""
    echo "Downloading ML models from Hugging Face Hub..."
    conda run -n smart-hive-demo python scripts/download_models.py
    echo "  Done."
else
    echo ""
    echo "WARNING: HF_TOKEN not set — ML models will not be downloaded."
    echo "Set it in: GitHub → Settings → Codespaces → Secrets → HF_TOKEN"
fi

echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  To start the demo:"
echo "    conda activate smart-hive-demo"
echo "    python demo/run_demo.py"
echo ""
echo "  Dashboard opens at:"
echo "    http://localhost:5000"
echo "  Password: smarthive"
echo "============================================"
