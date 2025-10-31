# Configuration Guide

Use this guide alongside `config.py` to understand the key configuration surfaces in Smart Hive AI.

## Timing
```python
TELEMETRY_INTERVAL_SECONDS = 5
TELEMETRY_PUBLISH_INTERVAL = 60
```
- `TELEMETRY_INTERVAL_SECONDS` controls how often the edge app polls sensors (used in mock environments).
- `TELEMETRY_PUBLISH_INTERVAL` defines the publish cadence to MQTT in production.
- Increase the value if you want to reduce bandwidth or DynamoDB writes; decrease it for faster feedback.

## Camera
```python
CAMERA_TYPE = "USB"
CAMERA_DEVICE_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
VIDEO_STREAM_FPS = 20
```
- Set `CAMERA_TYPE` to `"CSI"` if you are using a Raspberry Pi ribbon cable camera and ensure the underlying driver is enabled.
- For multiple cameras adjust `CAMERA_DEVICE_INDEX`.

## Audio
```python
AUDIO_SAMPLE_RATE = 22050
AUDIO_RECORD_DURATION_SEC = 30
AUDIO_WINDOW_SECONDS = 1.0
AUDIO_HOP_SECONDS = 0.5
AUDIO_CONFIDENCE_THRESHOLD = 0.6
AUDIO_AGGREGATION_METHOD = "max_proba"
```
- Longer recording durations provide more windows for classification.
- Adjust the threshold based on desired sensitivity (see `audio/confidence-threshold.md`).
- Changing the aggregation method requires understanding how probabilities should combine (default `max_proba` is safest for sporadic queen piping).

## Vision (optional)
```python
ENABLE_VISION_MODEL = True
VISION_MODEL_PATH = "models/vision_model.pt"
VISION_CONFIDENCE_THRESHOLD = 0.7
VISION_PROCESS_EVERY_N_FRAMES = 3
```
- Disable the vision model if you have not deployed a YOLO model. Leaving it enabled without the file will result in warnings but no detections.
- A higher confidence threshold reduces false positives when using generic YOLO weights.

## MQTT Topics
```python
TOPIC_TELEMETRY = "hive/telemetry"
TOPIC_AUDIO_RESULTS = "hive/audio/classification"
TOPIC_VISION_RESULTS = "hive/vision/detection"
TOPIC_CONTROL = "hive/control"
```
- Keep topic names consistent across services and dashboards.
- If you change topics, update both producer (edge/audio/vision services) and consumers (dashboard widgets, external subscribers).

## Feature Flags
```python
IS_MOCK_ENVIRONMENT = False
ENABLE_DYNAMODB = True
AUDIO_SAVE_RECORDINGS = False
```
- `IS_MOCK_ENVIRONMENT` swaps hardware drivers for mock implementations—set to `True` only on development machines without sensors.
- Disable `ENABLE_DYNAMODB` if you do not want to push telemetry to AWS.
- Toggle `AUDIO_SAVE_RECORDINGS` to capture WAV files for offline labelling.

## Credentials and Certificates
Environment variables loaded via `.env` supply the following values:
- `AWS_ENDPOINT`, `CERT_FILE_NAME`, `KEY_FILE_NAME` – used when connecting to AWS IoT Core or TLS-enabled brokers.
- `SECRET_KEY` – Flask session secret for the dashboard.

Ensure certificate files are placed under `certs/` and the names match the entries above.

## Rebuilding After Changes
Whenever you update `config.py`, rebuild and restart the affected services so container images pick up the new values:
```bash
docker compose build --no-cache smart-hive-edge smart-hive-audio smart-hive-vision
docker compose up -d smart-hive-edge smart-hive-audio smart-hive-vision
```
Restart only the services that depend on the changed settings.
