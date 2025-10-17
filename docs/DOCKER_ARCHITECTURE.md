# Docker Microservices Architecture

## Overview

The Smart Hive AI system uses a **microservices architecture** with Docker containers deployed on Raspberry Pi 4. This architecture separates concerns and provides resource isolation, scalability, and maintainability.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Smart Hive Network (smart-hive-net)          │
│                                                                 │
│  ┌──────────────────────┐   ┌──────────────────────┐           │
│  │  smart-hive-edge     │   │   smart-hive-ml      │           │
│  │  (Edge Sensors)      │   │  (ML Inference)      │           │
│  │                      │   │                      │           │
│  │ • Temperature        │   │ • YOLO v8 Vision    │           │
│  │ • Humidity           │   │ • MFCC Audio        │           │
│  │ • Vibration          │   │ • Audio Classifier   │           │
│  │ • Sound Level        │   │                      │           │
│  │ • Video Capture      │   │ Resource Limits:    │           │
│  │ • MQTT (telemetry)   │   │ • 2 CPU cores       │           │
│  │                      │   │ • 1 GB RAM          │           │
│  │ Resource Limits:     │   │                      │           │
│  │ • 2 CPU cores       │   │ Topic Subscriptions: │           │
│  │ • 1 GB RAM          │   │ • hive/ml/control   │           │
│  └──────────────────────┘   └──────────────────────┘           │
│           │                            │                       │
│           │  MQTT Bridge               │                       │
│           └────────────────────────────┘                       │
│                      │                                         │
│  ┌──────────────────────────────────────────────────┐         │
│  │  smart-hive-dashboard                           │         │
│  │  (Web Dashboard)                                │         │
│  │                                                  │         │
│  │ • Subscribes: hive/telemetry                   │         │
│  │ • Subscribes: hive/ml/vision/results           │         │
│  │ • Subscribes: hive/ml/audio/results            │         │
│  │ • Subscribes: hive/ml/health                   │         │
│  │                                                  │         │
│  │ Resource Limits:                               │         │
│  │ • 1 CPU core                                   │         │
│  │ • 512 MB RAM                                   │         │
│  └──────────────────────────────────────────────────┘         │
│                                                                 │
│  ┌──────────────────────────────────────────────────┐         │
│  │  Mosquitto MQTT Broker (Optional)               │         │
│  │  (If not using AWS IoT Core)                    │         │
│  └──────────────────────────────────────────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │
         │ AWS IoT Core Connection (TLS)
         ▼
   AWS Cloud Services
   • DynamoDB
   • Cognito
   • Lambda (Optional)
```

## Containers

### 1. smart-hive-edge (Sensor Data Collection)

**Purpose:** Collect sensor data and stream video

**Dockerfile:** `Dockerfile.edge`

**Base Image:** `python:3.9-slim`

**Key Components:**
- Temperature/Humidity sensor (BME280)
- Vibration sensor (LIS3DH)
- Sound level sensor (INMP441)
- Camera device (/dev/video0)
- MQTT client for telemetry publishing
- Flask app for video streaming

**Threads Running:**
1. `start_video_server()` - HTTP video stream on port 5000
2. `s3_snapshot_loop()` - Periodic snapshot upload to S3
3. `telemetry_loop()` - Sensor data collection and MQTT publishing
4. `vision_loop()` - Simple vision detection (optional fallback)

**MQTT Topics (Published):**
- `hive/telemetry` - Sensor data (temperature, humidity, vibration, sound)
- `hive/video/snapshot` - Snapshot metadata (timestamp, S3 URL)

**MQTT Topics (Subscribed):**
- `hive/control/power` - Power control signals
- `hive/control/sensors` - Individual sensor control
- `hive/ml/control` - ML service enable/disable commands

**Resource Limits:**
- CPU: 2 cores max
- Memory: 1 GB max

**Health Check:** HTTP GET to `http://localhost:5000/health`

**Restart Policy:** `unless-stopped`

---

### 2. smart-hive-ml (Machine Learning Inference)

**Purpose:** Run ML models for queen bee detection

**Dockerfile:** `Dockerfile.ml`

**Base Image:** `python:3.9-slim`

**Key Components:**
- YOLO v8 model (best.pt) for vision detection
- Audio classifier model (queen_bee.pkl) for audio classification
- MFCC audio feature extraction
- MQTT client for results publishing
- Camera device access (/dev/video0)
- Audio device access (/dev/snd)

**Service File:** `ml_inference_service.py` (280+ lines)

**Threads Running:**
1. `vision_inference_loop()` - Continuous YOLO detection
2. `audio_inference_loop()` - Periodic audio classification
3. `health_check_loop()` - Service health reporting

**MQTT Topics (Published):**
- `hive/ml/vision/results` - YOLO detection results
  ```json
  {
    "timestamp": 1699564800,
    "model_type": "yolov8",
    "detected": true,
    "confidence": 0.95,
    "inference_time_ms": 125
  }
  ```

- `hive/ml/audio/results` - Audio classification results
  ```json
  {
    "timestamp": 1699564800,
    "model_type": "mfcc_classifier",
    "classification": "queen_present",
    "confidence": 0.87
  }
  ```

- `hive/ml/health` - Service health check
  ```json
  {
    "timestamp": 1699564800,
    "service": "ml_inference",
    "status": "healthy",
    "vision_enabled": true,
    "audio_enabled": true,
    "last_vision_inference": 1699564799,
    "last_audio_inference": 1699564750
  }
  ```

**MQTT Topics (Subscribed):**
- `hive/ml/control` - Service control commands
  ```json
  {
    "command": "enable",     // enable/disable
    "module": "vision"       // vision/audio/all
  }
  ```

**Resource Limits:**
- CPU: 2 cores max
- Memory: 1 GB max

**Device Mounts:**
- `/dev/video0` - USB camera for video capture
- `/dev/snd` - Audio device for microphone input

**Health Check:** MQTT health topic (every 60 seconds)

**Restart Policy:** `unless-stopped`

**Dependencies:**
- Depends on: `smart-hive-edge` (must be running first)

---

### 3. smart-hive-dashboard (Web Interface)

**Purpose:** Display real-time data and ML results

**Dockerfile:** `Dockerfile.dashboard`

**Base Image:** `python:3.9-slim`

**Key Components:**
- Flask web server on port 5001
- Socket.IO for real-time updates
- MQTT client for data subscription
- Web UI (HTML/CSS/JavaScript)

**MQTT Topics (Subscribed):**
- `hive/telemetry` - Sensor data
- `hive/ml/vision/results` - Vision detection results
- `hive/ml/audio/results` - Audio classification results
- `hive/ml/health` - ML service health

**Web Endpoints:**
- `GET /` - Dashboard UI
- `GET /health` - Health check
- `POST /api/control/power` - Power control
- `POST /api/control/sensors` - Sensor control

**Resource Limits:**
- CPU: 1 core max
- Memory: 512 MB max

**Health Check:** HTTP GET to `http://localhost:5001/health`

**Restart Policy:** `unless-stopped`

---

## Communication Architecture

### MQTT Topic Hierarchy

```
hive/
├── telemetry/                    (Edge → Cloud/Dashboard)
│   ├── temperature
│   ├── humidity
│   ├── vibration
│   └── sound_level
│
├── video/
│   └── snapshot                  (Edge → S3 → Dashboard)
│
├── control/
│   ├── power                     (Dashboard → Edge)
│   ├── sensors                   (Dashboard → Edge)
│   └── ml/
│       └── enable_disable        (Dashboard → ML Service)
│
└── ml/
    ├── vision/
    │   └── results               (ML Service → Dashboard)
    │
    ├── audio/
    │   └── results               (ML Service → Dashboard)
    │
    ├── health                    (ML Service → Dashboard)
    │
    └── control                   (Dashboard → ML Service)
```

### Data Flow Diagram

```
SENSORS                    CAMERA                  AUDIO
   │                          │                       │
   └──────────────┬───────────┴───────────────────────┘
                  │
            ┌─────▼─────┐
            │ Edge App  │
            │ (Thread 1)│ telemetry_loop
            └─────┬─────┘
                  │
            MQTT Publish: hive/telemetry
                  │
         ┌────────┼────────┐
         │        │        │
    ┌────▼──┐ ┌──▼───┐ ┌──▼──────────────┐
    │Broker │ │Cloud │ │ ML Service      │
    └────┬──┘ └──┬───┘ │ (Thread 1 & 2)  │
         │       │     │ vision_loop     │
         │       │     │ audio_loop      │
         │       │     └──┬──────────────┘
         │       │        │
         │ MQTT Publish: hive/ml/vision/results
         │       │        hive/ml/audio/results
         │       │        │
    ┌────▼───────▼────────▼──┐
    │   Dashboard            │
    │   (Real-time UI)       │
    │   Socket.IO Updates    │
    └────────────────────────┘
```

## Deployment

### Prerequisites
- Raspberry Pi 4 (4GB+ RAM)
- Docker Engine 20.10+
- Docker Compose 1.29+
- USB Camera (/dev/video0)
- USB Microphone with audio support

### Installation

1. **Install Docker and Docker Compose:**
```bash
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo apt-get install docker-compose
```

2. **Prepare ML Models:**
```bash
# Vision model (YOLO v8)
ls -la ml_vision_model/best.pt

# Audio model
ls -la ml_audio_model/
```

3. **Configure Environment:**
```bash
# Copy and edit config.py
cp config.py config.local.py
nano config.local.py

# Set your AWS IoT credentials:
# - AWS_REGION
# - MQTT_BROKER (AWS IoT Core endpoint)
# - Certificate files
```

4. **Build Containers:**
```bash
docker-compose build
```

5. **Deploy System:**
```bash
docker-compose up -d
```

6. **Verify Deployment:**
```bash
# Check running containers
docker-compose ps

# View container logs
docker-compose logs -f smart-hive-edge
docker-compose logs -f smart-hive-ml
docker-compose logs -f smart-hive-dashboard

# Test MQTT connectivity
mosquitto_sub -h <MQTT_BROKER> -t 'hive/#'
```

### Stopping the System
```bash
docker-compose down
```

### Viewing Logs
```bash
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f smart-hive-ml

# Last N lines
docker-compose logs --tail=50 smart-hive-edge
```

---

## Performance Optimization

### CPU Allocation Strategy

**Total Raspberry Pi 4 CPUs:** 4 cores

| Service | CPU Cores | Memory | Justification |
|---------|-----------|--------|---|
| smart-hive-edge | 2 | 1 GB | Sensors + Video capture |
| smart-hive-ml | 2 | 1 GB | ML inference (high CPU load) |
| smart-hive-dashboard | 1 | 512 MB | Web UI (low load) |
| System/Docker | Reserved | 1 GB | OS and container overhead |

### Resource Limits in docker-compose.yml

```yaml
services:
  smart-hive-edge:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M

  smart-hive-ml:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M

  smart-hive-dashboard:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### ML Model Optimization

- **YOLO v8:** Uses FP16 inference for 2x speed improvement (if supported)
- **Audio:** 10-second recording window, processed every 30 seconds
- **Frame Skipping:** Vision processes every 4th camera frame (effective 7.5 FPS @ 30 FPS source)
- **Detection Cooldown:** Prevents MQTT spam (minimum 5 seconds between detections)

---

## Monitoring and Health Checks

### Health Check Endpoints

Each container provides health check information:

**Edge App:**
```bash
curl http://localhost:5000/health
```

**Dashboard:**
```bash
curl http://localhost:5001/health
```

**ML Service (via MQTT):**
```bash
mosquitto_sub -h <MQTT_BROKER> -t 'hive/ml/health'
```

### Monitoring MQTT Topics

Monitor all activity in real-time:
```bash
# All topics
mosquitto_sub -h <MQTT_BROKER> -v -t 'hive/#'

# Only ML results
mosquitto_sub -h <MQTT_BROKER> -v -t 'hive/ml/+/results'

# Only sensor telemetry
mosquitto_sub -h <MQTT_BROKER> -v -t 'hive/telemetry'

# Only health checks
mosquitto_sub -h <MQTT_BROKER> -t 'hive/ml/health' | jq .
```

### Container Health Status

```bash
# Check specific container
docker inspect --format='{{.State.Health}}' smart-hive-ml

# Watch all containers
watch docker-compose ps

# Stream logs with timestamps
docker-compose logs --timestamps --follow
```

---

## Troubleshooting

### Container Won't Start

**Problem:** `smart-hive-ml` fails to start

**Solutions:**
1. Check camera availability:
   ```bash
   ls -la /dev/video0
   ```

2. Check audio device:
   ```bash
   arecord -l
   ```

3. Check Docker logs:
   ```bash
   docker-compose logs smart-hive-ml
   ```

4. Verify models exist:
   ```bash
   ls -la ml_vision_model/best.pt
   ls -la ml_audio_model/
   ```

### High CPU Usage

**Problem:** Container using 100% CPU

**Solutions:**
1. Check YOLO inference times:
   ```bash
   docker-compose logs smart-hive-ml | grep inference_time
   ```

2. Reduce frame processing frequency in `config.py`:
   ```python
   VISION_PROCESS_EVERY_N_FRAMES = 8  # Increase from 4
   ```

3. Monitor resource usage:
   ```bash
   docker stats
   ```

### No MQTT Messages

**Problem:** No detections published to MQTT

**Solutions:**
1. Verify MQTT broker connection:
   ```bash
   docker-compose logs smart-hive-ml | grep "MQTT"
   ```

2. Check topic subscriptions:
   ```bash
   mosquitto_sub -h <MQTT_BROKER> -t 'hive/ml/#' -v
   ```

3. Verify model is enabled:
   ```bash
   docker-compose logs smart-hive-ml | grep "enabled"
   ```

---

## File Structure

```
smart-hive-ai/
├── app.py                          # Main edge application
├── config.py                       # Configuration settings
├── docker-compose.yml              # Microservices orchestration
│
├── Dockerfile.edge                 # Edge container definition
├── Dockerfile.ml                   # ML container definition
├── Dockerfile.dashboard            # Dashboard container definition
│
├── requirements-edge.txt           # Edge dependencies
├── requirements-ml.txt             # ML dependencies
├── requirements-dashboard.txt      # Dashboard dependencies
│
├── ml_inference_service.py         # ML microservice main entry
├── ml_vision_model/
│   ├── best.pt                    # YOLOv8 pre-trained model
│   └── vision_processor.py
├── ml_audio_model/
│   ├── audio_processor.py
│   └── models/
│       └── queen_bee.pkl          # Audio classifier model
│
├── dashboard/
│   ├── dashboard_app.py           # Dashboard Flask app
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── app.js
│       └── styles.css
│
├── models/
│   └── queen_bee.tflite           # TensorFlow Lite model (fallback)
│
└── docs/
    └── DOCKER_ARCHITECTURE.md     # This file
```

---

## Future Enhancements

- [ ] Kubernetes deployment for multi-hive swarms
- [ ] Horizontal scaling of ML inference across multiple Pi units
- [ ] GPU acceleration support (Coral TPU on RPi)
- [ ] Advanced monitoring dashboard with Prometheus/Grafana
- [ ] Model A/B testing framework
- [ ] Automated retraining pipeline

---

## References

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [MQTT Specification](https://mqtt.org/)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Raspberry Pi Docker Setup](https://docs.docker.com/engine/install/debian/)
