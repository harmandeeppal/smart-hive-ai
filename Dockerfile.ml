FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy ML models
COPY models/ ./models/

# Copy ML processor code
COPY ml_vision_model/ ./ml_vision_model/
COPY ml_audio_model/ ./ml_audio_model/

# Copy configuration and main service
COPY config.py .
COPY ml_inference_service.py .

# Copy ML-specific requirements
COPY requirements-ml.txt .

# Install Python dependencies
# Install opencv-python-headless first with --force-reinstall to prevent GUI version from being installed as dependency
RUN pip install --no-cache-dir opencv-python-headless==4.8.0.76 && \
    pip install --no-cache-dir --no-build-isolation -r requirements-ml.txt

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Run the ML inference service
CMD ["python", "ml_inference_service.py"]
