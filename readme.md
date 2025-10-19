# Smart Hive AI# Smart Hive AI

**IoT Beehive Monitoring System with Audio ML**

A professional, production-ready IoT system for real-time beehive monitoring and AI-powered queen bee detection using Raspberry Pi edge computing.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

[![Raspberry Pi](https://img.shields.io/badge/platform-Raspberry%20Pi%204-red.svg)](https://www.raspberrypi.org/)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

---[![Tests](https://img.shields.io/badge/tests-20_passing-green.svg)]()



## 📋 Overview## 📋 Overview



Smart Hive AI is a Raspberry Pi-based beehive monitoring system that combines **real-time sensors**, **audio machine learning**, and **cloud data storage** to help beekeepers monitor hive health.Smart Hive AI is an intelligent beehive monitoring system that leverages edge computing and artificial intelligence to provide beekeepers with real-time insights into hive health and queen bee presence. The system combines multi-sensor data collection with cloud-based AWS services for a comprehensive monitoring solution.



### ✨ Current Features### ✨ Key Features



- **🌡️ Environmental Monitoring**- **🔴 Real-Time Multi-Sensor Monitoring**

  - Temperature & humidity (BME280 sensor)  - Temperature and humidity (BME280 sensor)

  - Vibration detection (LIS3DH accelerometer)  - Vibration detection (LIS3DH accelerometer)

  - Sound level measurement (INMP441 microphone)  - Sound analysis (INMP441 microphone)

  - Live video streaming with detection overlays

- **🎙️ Audio ML - Queen Bee Detection**

  - **Random Forest classifier** for audio analysis- **🤖 AI-Powered Queen Bee Detection**

  - Detects queen bee presence from hive sounds  - YOLO v8-based computer vision model for queen detection

  - Confidence-based classification (60% threshold)  - Audio classification for hive activity analysis

  - Real-time inference every 60 seconds  - Real-time inference on edge device

  - TensorFlow Lite optimization for Raspberry Pi

- **📹 Live Video Streaming**

  - USB camera support- **☁️ AWS Cloud Integration**

  - Real-time video feed in dashboard  - MQTT messaging via AWS IoT Core

  - No AI vision detection (camera for monitoring only)  - Real-time telemetry persistence in DynamoDB

  - S3 integration for image storage (optional)

- **☁️ AWS Cloud Integration**  - Secure certificate-based authentication

  - **MQTT** messaging via local broker

  - **DynamoDB** for historical data storage- **📊 Interactive Web Dashboard**

  - **AWS IoT Core** ready (optional)  - Real-time sensor visualization with gauges

  - Live video stream with AI detection indicators

- **📊 Interactive Web Dashboard**  - WebSocket-based updates for instant data refresh

  - Real-time sensor gauges  - Responsive design for mobile and desktop

  - Live video stream  - Sensor control and monitoring interface

  - Audio ML status with confidence levels

  - Waveform visualization during recording- **🐳 Docker Containerization**

  - Sensor control (toggle ON/OFF)  - Three-service architecture (edge, ML, dashboard)

  - Resource-optimized for Raspberry Pi

- **🐳 Docker Deployment**  - Easy deployment and scaling

  - 4 containerized services  - Environment isolation

  - Easy deployment via docker-compose

  - Optimized for Raspberry Pi 4- **🧪 Comprehensive Testing**

  - 20+ unit tests for core functionality

---  - ML model path validation

  - Configuration validation

## 🚀 Quick Start  - Sensor mock functionality

  - MQTT integration tests

### Prerequisites

- Raspberry Pi 4 (4GB+ RAM)## 🏗️ Architecture

- Sensors: BME280, LIS3DH, INMP441, USB camera

- Docker & Docker Compose installedThe Smart Hive AI system follows a microservices architecture with three independent containerized services:

- SD card (32GB+)

```

### Installation┌──────────────────────────────────────────────────────────────────┐

│                     RASPBERRY PI EDGE DEVICE                      │

```bash├──────────────────────────────────────────────────────────────────┤

# Clone repository│                                                                    │

git clone https://github.com/harmandeeppal/smart-hive-ai.git│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │

cd smart-hive-ai│  │   BME280        │  │   LIS3DH        │  │   INMP441       │ │

│  │ Temp/Humidity   │  │   Vibration     │  │     Sound       │ │

# Checkout stable branch│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │

git checkout feature/usb-camera-fix│           │                    │                    │           │

│           └────────────────────┼────────────────────┘           │

# Configure environment│                                │                                 │

cp .env.example .env│  ┌──────────────────────────────▼──────────────────────────────┐ │

nano .env  # Add AWS credentials│  │              DOCKER: smart-hive-edge                         │ │

│  │  ┌────────────────────────────────────────────────────────┐ │ │

# Build and start│  │  │ app.py - Edge Application                             │ │ │

docker-compose build│  │  ├────────────────────────────────────────────────────────┤ │ │

docker-compose up -d│  │  │ • Sensor data collection (60s intervals)              │ │ │

│  │  │ • MQTT publishing to AWS IoT Core                     │ │ │

# Access dashboard│  │  │ • DynamoDB persistence                               │ │ │

# Open browser: http://<raspberry-pi-ip>:5000│  │  │ • Flask video streaming server (port 5001)           │ │ │

```│  │  │ • Real-time telemetry loop                           │ │ │

│  │  └────────────────────────────────────────────────────────┘ │ │

### Verify Installation│  └──────────────┬───────────────────────────────────────┬────────┘ │

```bash│                 │                                       │          │

# Check containers│  ┌──────────────▼───────────────────────────────────────▼────────┐ │

docker ps│  │         DOCKER: smart-hive-ml (ML Microservice)               │ │

│  │  ┌────────────────────────────────────────────────────────┐  │ │

# View logs│  │  │ ml_inference_service.py - ML Processing               │  │ │

docker logs -f smart-hive-edge│  │  ├────────────────────────────────────────────────────────┤  │ │

│  │  │ • YOLO v8 vision inference                            │  │ │

# Monitor MQTT│  │  │ • Audio classification                                │  │ │

mosquitto_sub -h localhost -t 'hive/#' -v│  │  │ • Real-time detection results                         │  │ │

```│  │  │ • Resource-isolated from edge app                     │  │ │

│  │  │ • MQTT control & results topics                       │  │ │

---│  │  └────────────────────────────────────────────────────────┘  │ │

│  └──────────────┬───────────────────────────────────────┬────────┘ │

## 📖 Documentation│                 │                                       │          │

│  ┌──────────────▼───────────────────────────────────────▼────────┐ │

| Guide | Description |│  │       DOCKER: smart-hive-dashboard (Web Dashboard)            │ │

|-------|-------------|│  │  ┌────────────────────────────────────────────────────────┐  │ │

| **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** | **START HERE** - Complete documentation index |│  │  │ dashboard_app.py - Web Interface                       │  │ │

| [BUILD_CONTAINERS_GUIDE.md](BUILD_CONTAINERS_GUIDE.md) | Detailed setup & deployment |│  │  ├────────────────────────────────────────────────────────┤  │ │

| [QUICK_START.md](QUICK_START.md) | Quick commands & monitoring |│  │  │ • Flask web server (port 5000)                        │  │ │

| [AUDIO_PROCESS_DETAILED_EXPLANATION.md](AUDIO_PROCESS_DETAILED_EXPLANATION.md) | How audio ML works (800+ lines) |│  │  │ • Real-time data visualization                        │  │ │

| [USB_CAMERA_TROUBLESHOOTING.md](USB_CAMERA_TROUBLESHOOTING.md) | Camera setup & fixes |│  │  │ • Live video stream display                           │  │ │

│  │  │ • WebSocket-based updates                             │  │ │

**→ See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete guide list**│  │  │ • MQTT telemetry subscription                         │  │ │

│  │  └────────────────────────────────────────────────────────┘  │ │

---│  └──────────────┬───────────────────────────────────────┬────────┘ │

│                 │                                       │          │

## 🏗️ System Architecture└─────────────────┼───────────────────────────────────────┼──────────┘

                  │              MQTT               │

```                  │          (AWS IoT Core)         │

┌─────────────────────────────────────────────────────┐      ┌───────────▼─────────────────────────────────▼────────────┐

│              Web Dashboard (Port 5000)              │      │                    AWS CLOUD SERVICES                     │

│         Flask + SocketIO + Real-time UI             │      ├────────────────────────────────────────────────────────────┤

└────────────┬────────────────────────────────────────┘      │ ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  │

             │      │ │   IoT Core      │  │  DynamoDB    │  │      S3      │  │

    ┌────────┴────────┬──────────────┬─────────────┐      │ │  MQTT Broker    │  │   Database   │  │   Storage    │  │

    │                 │              │             │      │ └─────────────────┘  └──────────────┘  └──────────────┘  │

┌───▼────┐   ┌────────▼──┐   ┌───────▼──┐   ┌─────▼──────┐      └────────────────────────────────────────────────────────────┘

│ MQTT   │   │ Edge App  │   │ Audio ML │   │  DynamoDB  │```

│ Broker │◄──┤  Sensors  │   │ Service  │   │  (Cloud)   │

│        │   │  Camera   │   │ (Queen   │   │            │## 🛠️ System Components

│        │   │  (5001)   │   │Detection)│   │            │

└────────┘   └───────────┘   └──────────┘   └────────────┘### 1. Edge Application (`app.py`)

```- Sensor data collection and processing

- MQTT publishing to AWS IoT Core

### Container Stack:- DynamoDB data persistence

1. **mosquitto** - MQTT message broker (local)- Video streaming server

2. **smart-hive-edge** - Main app (sensors + camera streaming)- Mock/real sensor abstraction layer

3. **smart-hive-audio** - Audio ML inference service- Telemetry loop (60-second intervals)

4. **smart-hive-dashboard** - Web interface

### 2. ML Inference Microservice (`ml_inference_service.py`)

---- Independent ML processing service

- YOLO v8 vision model for queen bee detection

## 🔧 Configuration- Audio classification for hive activity

- MQTT-based control and results

### Key Settings (`config.py`):- Resource-isolated for Raspberry Pi constraints



**Audio ML:**### 3. Web Dashboard (`dashboard/dashboard_app.py`)

```python- Real-time data visualization

AUDIO_CONFIDENCE_THRESHOLD = 0.6  # 60% confidence- Live video streaming

AUDIO_WINDOW_SECONDS = 1.0        # 1-second windows- Interactive sensor controls

AUDIO_HOP_SECONDS = 0.5           # 50% overlap- WebSocket communication

```- Responsive web interface



**Camera:**### 4. Configuration Management (`config.py`)

```python- Centralized environment-based configuration

CAMERA_TYPE = "USB"          # USB webcam- AWS IoT Core settings

CAMERA_DEVICE_INDEX = 0      # First camera (/dev/video0)- MQTT topics and intervals

VIDEO_STREAM_FPS = 20        # 20 FPS streaming- Feature flags and toggles

```

## 📦 Hardware Requirements

**Telemetry:**

```python### Raspberry Pi Setup

TELEMETRY_PUBLISH_INTERVAL = 60  # Publish every 60 seconds- **Device**: Raspberry Pi 4 (2GB RAM minimum, 4GB+ recommended)

```- **Storage**: MicroSD Card (16GB minimum, Class 10 recommended)

- **Power**: 5V 3A USB-C Power Supply

See [`config.py`](config.py) for all settings.

### Sensors

---| Sensor | Model | Function | Connection |

|--------|-------|----------|-----------|

## 📊 Features Status| Temperature/Humidity | BME280 | Environmental monitoring | I2C (0x76) |

| Vibration | LIS3DH | Hive activity detection | I2C (0x19) |

| Feature | Status | Technology || Microphone | INMP441 | Sound analysis | I2S |

|---------|--------|------------|| Camera | Logitech C270 | Live video & detection | USB |

| Temperature monitoring | ✅ Working | BME280 I2C sensor |

| Humidity monitoring | ✅ Working | BME280 I2C sensor |### Connections

| Vibration monitoring | ✅ Working | LIS3DH I2C accelerometer |- **I2C Bus 1** (GPIO 2/3): BME280 + LIS3DH sensors

| Sound level | ✅ Working | INMP441 microphone |- **USB Ports**: Camera and microphone

| **Audio ML (Queen Detection)** | ✅ **Working** | Random Forest + librosa |- **Network**: Ethernet or WiFi (required for AWS)

| Live video streaming | ✅ Working | USB camera (OpenCV) |

| Web dashboard | ✅ Working | Flask + SocketIO |## 💻 Software Stack

| AWS DynamoDB | ✅ Working | Cloud data storage |

| MQTT messaging | ✅ Working | Local mosquitto broker || Component | Version | Purpose |

| ~~Vision ML~~ | ❌ Not used | Camera for streaming only ||-----------|---------|---------|

| ~~S3 Uploads~~ | ❌ Not used | Feature disabled || Python | 3.9+ | Runtime |

| Docker | Latest | Containerization |

---| Flask | 2.x | Web framework |

| MQTT (Paho) | 1.6+ | Message broker |

## 🎯 Current Capabilities| OpenCV | 4.x | Computer vision |

| TensorFlow Lite | 2.x | ML inference |

### Audio ML System| Boto3 | 1.26+ | AWS SDK |

- **Records:** 60 seconds of hive audio via INMP441 microphone| PyTorch | 2.x | Deep learning |

- **Analyzes:** Extracts 312 audio features (13 MFCC × 3 types × 8 statistics)| scikit-learn | Latest | ML algorithms |

- **Classifies:** Random Forest model predicts `queen_present` or `queen_absent`

- **Confidence:** Only accepts predictions ≥60% confidence## 🚀 Quick Start

- **Publishes:** Results to MQTT topic `hive/audio/classification`

- **Dashboard:** Shows classification, confidence, and waveform visualization### For Laptop Development (5 minutes)



### Sensor Monitoring```bash

- **Sampling:** Every 60 seconds# 1. Clone repository

- **Sensors:** Temperature, humidity, vibration, sound levelgit clone https://github.com/harmandeeppal/smart-hive-ai.git

- **Storage:** DynamoDB with NZ timezone timestampscd smart-hive-ai

- **Dashboard:** Real-time gauges with color-coded status

- **Controls:** Toggle individual sensors ON/OFF# 2. Create virtual environment

python -m venv venv

### Video Streamingsource venv/bin/activate  # Windows: venv\Scripts\activate

- **Source:** Any USB webcam

- **Resolution:** 640×480 (configurable)# 3. Install dependencies

- **Frame Rate:** 20 FPS (configurable)pip install -r requirements.txt

- **Access:** `http://<pi-ip>:5001/video_feed` (direct) or via dashboard

- **Note:** No AI vision detection (streaming only)# 4. Run tests (verify setup)

pytest tests/ -v

---

# 5. Start services in mock mode (3 terminal windows)

## 🐛 Troubleshooting

# Terminal 1: Edge application

### Common Issues:export IS_MOCK_ENVIRONMENT=true

python app.py

**Audio ML not working?**

```bash# Terminal 2: ML inference service

# Check microphonepython ml_inference_service.py

arecord -l

# Terminal 3: Dashboard

# Check audio service logscd dashboard

docker logs smart-hive-audio | grep -i classificationpython dashboard_app.py



# See: AUDIO_TROUBLESHOOTING.md# 6. Open browser

```# http://localhost:5000

```

**Camera showing broken image?**

```bash### For Raspberry Pi Deployment (10 minutes)

# Check camera device

ls -l /dev/video0```bash

# 1. Setup credentials

# Test video feedcp .env.example .env

curl -I http://localhost:5001/video_feednano .env  # Add your AWS IoT endpoint



# See: CRITICAL_FIX_BROKEN_IMAGE.md# 2. Copy AWS certificates

```cp your-certificate.pem certs/

cp your-private-key.pem certs/

**Dashboard not updating?**cp AmazonRootCA1.pem certs/

```bash

# Rebuild dashboard (files are copied into container!)# 3. Deploy with Docker

docker-compose build --no-cache dashboarddocker-compose build

docker-compose up -d dashboarddocker-compose up -d



# Hard refresh browser: Ctrl + Shift + R# 4. Monitor

```docker-compose logs -f



**→ See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete troubleshooting guides**# 5. Access dashboard

# http://<raspberry-pi-ip>:5000

---```



## 📦 Project Structure## ⚙️ Configuration



```### Environment Variables (.env)

smart-hive-ai/

├── app.py                       # Main edge application```bash

├── config.py                    # Configuration settings# AWS IoT Core

├── ml_audio_service.py          # Audio ML microserviceAWS_ENDPOINT=your-endpoint.iot.ap-southeast-2.amazonaws.com

├── dashboard/                   # Web dashboardCERT_FILE_NAME=your-certificate.pem

│   ├── dashboard_app.py         # Flask backendKEY_FILE_NAME=your-private-key.pem

│   ├── templates/index.html     # Dashboard UI

│   └── static/                  # CSS, JavaScript# Flask

├── ml_audio_model/              # Audio processingSECRET_KEY=your-secret-key-here

│   └── audio_processor.py       # Feature extraction + inference

├── models/                      # ML models# AWS Services

│   └── audio_model_pipeline.pkl # Trained Random ForestS3_BUCKET_NAME=your-bucket-name

├── real_components.py           # Raspberry Pi hardwareENABLE_S3=false  # Set to true for image uploads

├── docker-compose.yml           # Container orchestration

├── Dockerfile.*                 # Container definitions# Development

└── *.md                        # DocumentationIS_MOCK_ENVIRONMENT=false  # Set to true for laptop testing

``````



---### Hardware Configuration (`config.py`)



## 🔄 Updates & Maintenance```python

# I2C Addresses

### Deploy Updates:BME280_ADDRESS = 0x76

```bashLIS3DH_ADDRESS = 0x19

cd ~/smart-hive-ai

git pull origin feature/usb-camera-fix# Camera Settings

docker-compose build --no-cacheCAMERA_TYPE = "USB"

docker-compose up -dCAMERA_DEVICE_INDEX = 0

```

# Sensor Intervals (seconds)

### Monitor System:TELEMETRY_INTERVAL_SECONDS = 60

```bash

# All containers running?# AI Detection

docker psVISION_DETECTION_MODE = "continuous"

VISION_PROCESS_EVERY_N_FRAMES = 3

# Check logsVISION_CONFIDENCE_THRESHOLD = 0.5

docker logs -f smart-hive-edge

docker logs -f smart-hive-audio# AWS Services

docker logs -f smart-hive-dashboardDYNAMODB_TABLE = "SmartHiveTelemetry"

AWS_REGION = "ap-southeast-2"

# Monitor MQTT messages

mosquitto_sub -h localhost -t 'hive/#' -v# MQTT Topics

```TOPIC_TELEMETRY = "hive/telemetry"

TOPIC_VISION = "hive/vision"

---TOPIC_CONTROL = "hive/control"

```

## 🛠️ Technology Stack

## 📁 Project Structure

- **Hardware:** Raspberry Pi 4, BME280, LIS3DH, INMP441, USB camera

- **Languages:** Python 3.9+```

- **ML Libraries:** scikit-learn, librosa, numpysmart-hive-ai/

- **Web:** Flask, SocketIO, JavaScript├── README.md                           # This file

- **Containers:** Docker, Docker Compose├── QUICK_START.md                      # Quick reference guide

- **Cloud:** AWS DynamoDB, AWS IoT Core (optional)├── DOCUMENTATION_CLEANUP_SUMMARY.md    # Documentation overview

- **Messaging:** MQTT (Mosquitto broker)│

- **Camera:** OpenCV (cv2)├── Core Application Files

├── app.py                              # Main edge application (726 lines)

---├── config.py                           # Configuration management (244 lines)

├── ml_inference_service.py             # ML microservice (631 lines)

## 📝 Recent Improvements (October 2025)│

├── Component Abstractions

✅ **Audio ML Fully Operational:**├── mock_components.py                  # Mock sensors for testing

- Fixed sample rate auto-detection (44100Hz → 22050Hz)├── real_components.py                  # Real hardware implementations

- Corrected feature extraction (13 MFCC × 8 stats = 312 features)│

- Fixed pipeline order (scale → select)├── Dashboard Application

- Added confidence threshold configuration├── dashboard/

- Enhanced dashboard visualizations│   ├── dashboard_app.py               # Dashboard web app (267 lines)

│   ├── static/

✅ **Camera System Fixed:**│   │   ├── app.js                     # Frontend logic

- Multi-backend initialization (V4L2, auto-detect)│   │   └── styles.css                 # Dashboard styling

- Automatic warmup and retry logic│   └── templates/

- Fixed dashboard hostname mismatch (edge-app → smart-hive-edge)│       └── index.html                 # Dashboard UI

- Comprehensive troubleshooting documentation│

├── ML Models & Processors

✅ **Documentation Cleanup:**├── ml_vision_model/

- Removed obsolete/redundant files│   └── vision_processor.py            # YOLO v8 processor

- Created consolidated guides├── ml_audio_model/

- Up-to-date architecture diagrams│   └── audio_processor.py             # Audio classifier

├── models/                            # AI models directory

---│   ├── vision_model.pt                # YOLO v8 model (6.23 MB)

│   ├── audio_model.pkl                # Audio classifier (15.8 MB)

## 📄 License│   └── queen_bee.tflite               # TensorFlow Lite model

│

MIT License - See [LICENSE](LICENSE) file for details├── Docker Configuration

├── docker-compose.yml                 # Multi-container orchestration

---├── Dockerfile.edge                    # Edge app container

├── Dockerfile.dashboard               # Dashboard container

## 🤝 Contributing├── Dockerfile.ml                      # ML service container

│

This is an academic project. For issues or questions, please open a GitHub issue.├── Dependencies

├── requirements.txt                   # All dependencies

---├── requirements-edge.txt              # Edge-specific

├── requirements-dashboard.txt         # Dashboard-specific

## 📞 Support├── requirements-ml.txt                # ML-specific

│

**Documentation:** [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)  ├── AWS IoT Certificates

**Repository:** https://github.com/harmandeeppal/smart-hive-ai├── certs/

│   ├── AmazonRootCA1.pem             # AWS root CA

---│   ├── your-certificate.pem          # Device certificate

│   └── your-private-key.pem          # Private key

**Last Updated:** October 20, 2025  │

**Current Stable Branch:** `feature/usb-camera-fix`├── Documentation

├── docs/
│   ├── SETUP_AND_DEPLOYMENT.md       # Setup guide (⭐ START HERE)
│   ├── DEPLOYMENT.md                 # Production deployment
│   ├── CONFIGURATION_GUIDE.md        # Configuration reference
│   ├── VIDEO_STREAM_CONFIGURATION.md # Camera setup
│   ├── PROJECT_PLAN.md               # Project overview
│   ├── TROUBLESHOOTING.md            # Common issues & solutions
│   ├── ML_INTEGRATION_PLAN.md        # ML architecture
│   ├── ML_IMPLEMENTATION_CHECKLIST.md # ML integration steps
│   ├── ML_MODELS_IMPLEMENTATION_GUIDE.md # ML code examples
│   ├── api/                          # API documentation
│   ├── deployment/                   # Deployment scripts
│   └── troubleshooting/              # Troubleshooting guides
│
├── Testing
├── tests/
│   ├── test_all.py                   # Comprehensive test suite (21 tests)
│   └── __init__.py
│
├── Utility Scripts
├── scripts/
│   ├── check_dynamodb_timestamps.py  # DynamoDB verification
│   ├── diagnose_dynamodb.py          # DynamoDB diagnostics
│   ├── update_dynamodb_timestamps.py # Timestamp updates
│   ├── test_audio_model.py           # Audio model tests
│   ├── test_vision_model.py          # Vision model tests
│   ├── test_ml_integration.py        # ML integration tests
│   └── test_ml_microservice.py       # ML service tests
│
├── Development
├── .env.example                      # Environment template
├── .env                              # Environment variables (local)
├── .dockerignore                     # Docker ignore rules
├── .gitignore                        # Git ignore rules
└── pytest.ini                        # Pytest configuration
```

## 🧪 Testing

The project includes a comprehensive test suite with 20+ tests:

```bash
# Run all tests
pytest tests/ -v

# Run specific test class
pytest tests/test_all.py::TestMLModelsExist -v

# Run with coverage report
pytest tests/ --cov=. --cov-report=html

# Run with short output
pytest tests/ -q
```

### Test Coverage
- ✅ ML models availability and paths
- ✅ Configuration validation
- ✅ Mock sensor functionality
- ✅ MQTT integration
- ✅ Data payload structures
- ✅ Project structure integrity

**Current Status**: 20 passing, 1 skipped ✅

## 📊 Monitoring & Management

### View Container Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f smart-hive-edge
docker-compose logs -f smart-hive-ml
docker-compose logs -f smart-hive-dashboard
```

### Check Sensor Status

```bash
# Verify I2C devices
sudo i2cdetect -y 1

# Check DynamoDB writes
python scripts/check_dynamodb_timestamps.py

# Run diagnostics
python scripts/diagnose_dynamodb.py
```

### MQTT Monitoring

```bash
# Subscribe to telemetry
mosquitto_sub -h localhost -t "hive/telemetry" -v

# Subscribe to vision results
mosquitto_sub -h localhost -t "hive/vision" -v

# Subscribe to all topics
mosquitto_sub -h localhost -t "hive/#" -v
```

## 📡 Data Formats

### Telemetry Payload (hive/telemetry)

```json
{
  "timestamp": 1760526982,
  "timestamp_nz": "2025-10-16 00:16:22 NZDT",
  "temperature_c": 34.5,
  "humidity_percent": 58.0,
  "vibration_rms": 0.05,
  "sound_db": 52.0,
  "sound_frequency_hz": 200.0,
  "source": "SmartHive_Pi"
}
```

### Vision Detection Results (hive/vision)

```json
{
  "timestamp": 1760526982,
  "frame_timestamp": "2025-10-16T00:16:22+13:00",
  "queen_detected": true,
  "confidence": 0.87,
  "detection_count": 1,
  "bounding_boxes": [
    {"x": 150, "y": 200, "width": 50, "height": 60}
  ]
}
```

### Audio Classification Results (hive/audio)

```json
{
  "timestamp": 1760526982,
  "classification": "normal_activity",
  "confidence": 0.92,
  "sound_intensity": "high"
}
```

## 🐛 Troubleshooting

### I2C Connection Issues

```bash
# Verify I2C devices
sudo i2cdetect -y 1

# Fix permission issues
sudo usermod -a -G i2c pi
sudo reboot
```

### Docker Issues

```bash
# Container won't start
docker logs smart-hive-edge

# Permission denied errors
sudo chmod 777 /dev/i2c-1
sudo chmod 777 /dev/video0
sudo chmod 777 /dev/snd
```

### AWS Connection Failed

```bash
# Verify credentials
docker exec smart-hive-edge ls -la /root/.aws/

# Test AWS connection
docker exec smart-hive-edge python3 -c "import boto3; print(boto3.client('sts').get_caller_identity())"

# Check certificate files
docker exec smart-hive-edge ls -la certs/
```

### Tests Failing

```bash
# Run with verbose output
pytest tests/ -vv

# Run specific test
pytest tests/test_all.py::TestConfiguration -v

# Check test output
pytest tests/ --tb=short
```

For more detailed solutions, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 📚 Documentation Guide

Start here based on your needs:

| Goal | Document |
|------|----------|
| Get started quickly | [QUICK_START.md](QUICK_START.md) |
| Complete setup | [docs/SETUP_AND_DEPLOYMENT.md](docs/SETUP_AND_DEPLOYMENT.md) ⭐ |
| Deploy to production | [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) |
| Configure system | [docs/CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md) |
| Setup cameras | [docs/VIDEO_STREAM_CONFIGURATION.md](docs/VIDEO_STREAM_CONFIGURATION.md) |
| Understand ML | [docs/ML_INTEGRATION_PLAN.md](docs/ML_INTEGRATION_PLAN.md) |
| Implement ML | [docs/ML_IMPLEMENTATION_CHECKLIST.md](docs/ML_IMPLEMENTATION_CHECKLIST.md) |
| Fix problems | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| Project details | [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) |

## 🔄 Development Workflow

### Local Development (Mock Mode)

```python
# In config.py or .env
IS_MOCK_ENVIRONMENT = true
```

```bash
# Run individual services
python app.py                    # Edge app with mock sensors
python ml_inference_service.py   # ML service (mock)
python dashboard/dashboard_app.py # Web dashboard
```

### Testing & Validation

```bash
# Run tests
pytest tests/ -v

# Check code style
flake8 app.py config.py
black app.py config.py

# Verify imports
python -c "import app, config, ml_inference_service"
```

### Docker Development

```bash
# Build images
docker-compose build

# Run services
docker-compose up

# Development mode (with logs)
docker-compose up --build

# Stop services
docker-compose down
```

## 📈 Performance & Optimization

### Raspberry Pi Optimization

The system is optimized for Raspberry Pi 4 constraints:

- **TensorFlow Lite**: Quantized models for faster inference
- **Resource Limits**: CPU and memory constraints in docker-compose
- **Microservice Separation**: Resource isolation between services
- **Efficient Polling**: 60-second telemetry intervals
- **Frame Skipping**: Process every 3rd frame for ML inference

### ML Model Optimization

- Vision model: YOLO v8 (6.23 MB, optimized for real-time)
- Audio model: scikit-learn (15.8 MB, lightweight)
- TensorFlow Lite: Quantized for edge deployment

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make changes with proper documentation
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/ -v`)
6. Submit a pull request

### Code Style

This project follows PEP 8. Use these tools:

```bash
# Check style
flake8 app.py config.py dashboard/dashboard_app.py

# Auto-format
black app.py config.py dashboard/dashboard_app.py

# Type checking
mypy app.py config.py
```

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **TensorFlow Lite**: Efficient edge AI inference
- **AWS IoT Core**: Reliable cloud connectivity
- **OpenCV**: Computer vision capabilities
- **Raspberry Pi Foundation**: Accessible edge computing
- **Docker**: Containerization and portability

## 📞 Support

- **Documentation**: [docs/](docs/) folder
- **Quick Help**: [QUICK_START.md](QUICK_START.md)
- **Issues**: [GitHub Issues](https://github.com/harmandeeppal/smart-hive-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/harmandeeppal/smart-hive-ai/discussions)

## 🗺️ Roadmap

- [ ] Multi-hive support and management
- [ ] Mobile app for iOS/Android
- [ ] Advanced analytics and predictions
- [ ] Swarm swarming detection algorithms
- [ ] Weather data integration
- [ ] Real-time alert notifications
- [ ] Historical trend analysis
- [ ] Machine learning model retraining pipeline

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Oct 2025 | Initial production release |
| 0.9.0 | Oct 2025 | ML microservice implementation |
| 0.8.0 | Oct 2025 | Project cleanup and reorganization |

---

**Built with ❤️ for beekeeping and technology**

Last Updated: October 18, 2025  
Status: ✅ Production Ready  
Tests: ✅ 20 Passing, 1 Skipped
