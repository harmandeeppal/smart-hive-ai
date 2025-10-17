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

# Install Python dependencies with headless OpenCV
# Simplified for faster builds on Raspberry Pi
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir 'numpy==1.24.3' 'opencv-python-headless==4.8.0.76' && \
    pip install --no-cache-dir -r requirements-ml.txt --no-deps && \
    pip install --no-cache-dir ultralytics scikit-learn librosa boto3 paho-mqtt python-dotenv && \
    pip uninstall -y opencv-python 2>/dev/null || true && \
    pip install --no-cache-dir --force-reinstall 'numpy==1.24.3' 'opencv-python-headless==4.8.0.76' && \
    rm -rf /root/.cache/pip/* /tmp/* /var/tmp/*

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
