FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy requirements first for better caching
COPY requirements-ml.txt .

# Install Python dependencies with headless OpenCV first
# Using --no-cache-dir to minimize image size during build
# CRITICAL: ultralytics will try to install opencv-python, so we need to:
# 1. Install headless OpenCV first
# 2. Install all requirements (which may pull in GUI opencv)
# 3. Uninstall GUI version and force-reinstall headless version
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir opencv-python-headless==4.8.0.76 && \
    pip install --no-cache-dir -r requirements-ml.txt || true && \
    pip uninstall -y opencv-python && \
    pip install --no-cache-dir --force-reinstall opencv-python-headless==4.8.0.76 && \
    find /usr/local -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Copy ML models (after dependencies to leverage layer caching)
COPY models/ ./models/

# Copy ML processor code
COPY ml_vision_model/ ./ml_vision_model/
COPY ml_audio_model/ ./ml_audio_model/

# Copy configuration and main service
COPY config.py .
COPY ml_inference_service.py .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import cv2; print('OK')" || exit 1

# Run the ML inference service
CMD ["python", "ml_inference_service.py"]
