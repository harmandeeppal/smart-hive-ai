# Smart Hive AI - Complete Setup & Deployment Guide

> **⚠️ NOTICE:** This document contains some outdated information. For the most up-to-date deployment guide, see:
> - [DEPLOYMENT.md](DEPLOYMENT.md) - Current deployment guide
> - [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) - Master index
> - [../BUILD_CONTAINERS_GUIDE.md](../BUILD_CONTAINERS_GUIDE.md) - Docker deployment

## Project Overview

Smart Hive AI is an IoT + Edge AI system for intelligent honeybee colony monitoring. It combines Raspberry Pi edge computing with Audio ML classification to monitor hive health and provide real-time alerts.

**Technology Stack:**
- Python 3.9+
- Edge: MQTT (Local Mosquitto Broker)
- ML: scikit-learn Random Forest (Audio Classification)
- Dashboard: Flask + SocketIO
- Containerization: Docker & Docker Compose
- Database: AWS DynamoDB (Optional)

---

## Quick Start (Development on Laptop)

### Prerequisites

- Python 3.9 or higher
- Git
- Docker & Docker Compose (optional, for production)

### Local Installation

```bash
# 1. Clone repository
git clone https://github.com/harmandeeppal/smart-hive-ai.git
cd smart-hive-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env
# Edit .env with your AWS credentials and settings
```

### Running Tests Locally

```bash
# Run all tests (20 pass, 1 skipped)
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/test_all.py::TestMLModelsExist -v
python -m pytest tests/test_all.py::TestConfiguration -v
python -m pytest tests/test_all.py::TestMockSensors -v
```

### Running Application Locally (Mock Mode)

```bash
# Set mock environment
export IS_MOCK_ENVIRONMENT=true  # On Windows: set IS_MOCK_ENVIRONMENT=true

# Run edge application
python app.py

# In another terminal, run dashboard
python dashboard/dashboard_app.py

# In another terminal, run ML inference service
python ml_inference_service.py
```

**Mock data will be generated from fake sensors for testing purposes.**

---

## Production Deployment

### Architecture

```
┌──────────────────────────────────────────────┐
│         AWS Cloud (Optional)                 │
│  ┌──────────────┐                           │
│  │ DynamoDB     │                           │
│  │ (TimeSeries) │                           │
│  └──────────────┘                           │
└──────────────────────────────────────────────┘
           ▲
           │ (Optional)
┌──────────┴──────────────────────────────────┐
│         Raspberry Pi (Edge)                  │
│  ┌────────────────────────────────────────┐ │
│  │  Docker Compose                        │ │
│  │  ┌──────────┐ ┌─────────┐ ┌──────────┐│ │
│  │  │ Edge App │ │ Audio ML│ │Dashboard ││ │
│  │  │(Sensors +│ │(RF Model│ │(Web UI + ││ │
│  │  │ Camera)  │ │ Predict)│ │ Video)   ││ │
│  │  └──────────┘ └─────────┘ └──────────┘│ │
│  │       │            ▲            │      │ │
│  │  ┌────┴────────────┴────────────┴───┐ │ │
│  │  │  Mosquitto MQTT Broker (Local) │ │ │
│  │  └────────────────────────────────┘ │ │
│  └────────────────────────────────────────┘ │
│                     ▲                        │
└─────────────────────┼────────────────────────┘
                           │
                    ┌──────────────┐
                    │  Hive Sensors│
                    │ (BME280, etc)│
                    └──────────────┘
```

### Deploying with Docker

#### 1. Prepare Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env with production values
nano .env

# Copy AWS certificates to certs/
cp your_cert.pem certs/
cp your_private.key certs/
cp AmazonRootCA1.pem certs/
```

#### 2. Build and Run

```bash
# Build all containers
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Stop services
docker-compose down
```

#### 3. Verify Deployment

```bash
# Check edge app logs
docker-compose logs smart-hive-edge

# Check ML service logs
docker-compose logs smart-hive-ml

# Check dashboard logs
docker-compose logs smart-hive-dashboard

# Test MQTT connection
mosquitto_sub -h localhost -t "hive/#"
```

---

## Configuration

### Environment Variables (.env)

```bash
# AWS IoT Core
AWS_ENDPOINT=your-endpoint.iot.us-east-1.amazonaws.com
CERT_FILE_NAME=your_certificate.pem
KEY_FILE_NAME=your_private.key

# Flask
SECRET_KEY=your-secret-key-here

# DynamoDB (optional - cloud storage)
ENABLE_DYNAMODB=false

# MQTT (Local Mosquitto Broker)
MQTT_BROKER=mosquitto  # Container name
MQTT_PORT=1883

# Feature Flags
IS_MOCK_ENVIRONMENT=false
ENABLE_AUDIO_ML=true
```

**Note:** System uses local MQTT broker. AWS IoT Core is optional for remote access.

### config.py Settings

Key configuration parameters:

```python
# Sensor intervals (seconds)
TELEMETRY_INTERVAL_SECONDS = 60  # Read sensors every 60s

# Audio ML settings
AUDIO_CONFIDENCE_THRESHOLD = 0.6  # 60% confidence minimum
AUDIO_WINDOW_SECONDS = 1.0
AUDIO_HOP_SECONDS = 0.5

# Camera settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 20

# MQTT Topics
TOPIC_TELEMETRY = "hive/telemetry"
TOPIC_AUDIO = "hive/audio"
TOPIC_CONTROL = "hive/control"
```

---

## Project Structure

```
smart-hive-ai/
├── README.md                           # Project documentation
├── config.py                           # Configuration management
├── app.py                              # Edge application (main)
├── ml_inference_service.py             # ML inference service
├── mock_components.py                  # Mock sensors for testing
├── real_components.py                  # Real hardware implementations
│
├── docker-compose.yml                  # Multi-container orchestration
├── Dockerfile.edge                     # Edge app container
├── Dockerfile.ml                       # ML service container
├── Dockerfile.dashboard                # Dashboard container
│
├── requirements.txt                    # All dependencies
├── requirements-edge.txt               # Edge app dependencies
├── requirements-ml.txt                 # ML service dependencies
├── requirements-dashboard.txt          # Dashboard dependencies
│
├── .env.example                        # Environment template
├── .gitignore                          # Git ignore rules
├── pytest.ini                          # Pytest configuration
│
├── certs/                              # AWS IoT certificates
│   ├── AmazonRootCA1.pem
│   ├── certificate.pem
│   └── private.key
│
├── models/                             # ML models
│   ├── vision_model.pt                    # YOLO vision model (6.2 MB)
│   └── audio_model.pkl                    # Audio classification model (15.8 MB)
│
├── ml_vision_model/                    # Vision processing
│   ├── vision_processor.py             # VisionProcessor class
│   ├── camera_yolo_noir.py             # Camera reference implementation
│   ├── vision_model.pt                 # Model (redundant, copy in models/)
│   └── libcamera/                      # LibCamera dependencies
│
├── ml_audio_model/                     # Audio processing
│   ├── audio_processor.py              # AudioProcessor class
│   ├── enhanced_queen_bee_detection.py # Training reference
│   └── audio_model.pkl                 # Model (redundant, copy in models/)
│
├── dashboard/                          # Web dashboard
│   ├── dashboard_app.py                # Flask application
│   ├── static/
│   │   ├── app.js                      # Frontend logic
│   │   └── styles.css                  # Styling
│   └── templates/
│       └── index.html                  # UI template
│
├── docs/                               # Documentation
│   ├── DEPLOYMENT.md                   # Deployment guide
│   ├── CONFIGURATION_GUIDE.md          # Configuration details
│   ├── TROUBLESHOOTING.md              # Common issues & solutions
│   └── ...
│
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── test_all.py                     # 20+ comprehensive tests
│   └── conftest.py                     # Pytest configuration
│
├── scripts/                            # Utility scripts
│   ├── check_dynamodb_timestamps.py
│   ├── diagnose_dynamodb.py
│   ├── update_dynamodb_timestamps.py
│   └── ...
│
└── others/                             # Miscellaneous files
```

---

## Testing

### Running Tests

```bash
# All tests (20 pass, 1 skipped)
pytest tests/ -v

# By category
pytest tests/test_all.py::TestMLModelsExist -v         # ML models exist
pytest tests/test_all.py::TestConfiguration -v         # Config correct
pytest tests/test_all.py::TestMockSensors -v           # Mock sensors work
pytest tests/test_all.py::TestDataProcessing -v        # Data payloads valid
pytest tests/test_all.py::TestPathConfiguration -v     # Paths correct
pytest tests/test_all.py::TestIntegration -v           # Integration test

# With coverage
pytest tests/ --cov=.  --cov-report=html
```

### Test Categories

| Category | Tests | Purpose |
|----------|-------|---------|
| ML Models | 3 | Verify YOLO and audio models exist |
| Configuration | 3 | Verify all config attributes present |
| Mock Sensors | 3 | Verify mock sensor data is valid |
| Data Processing | 3 | Verify MQTT payload structures |
| Paths | 3 | Verify all file paths work |
| Integration | 2 | End-to-end tests |
| **TOTAL** | **20 passed** | **Ready for deployment** |

---

## Troubleshooting

### Test Failures

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

**Permission denied (on Raspberry Pi):**
```bash
sudo -E python app.py
```

**MQTT connection failed:**
- Verify AWS_ENDPOINT in .env
- Check certificates in certs/
- Ensure AWS IoT policy allows connect/publish/subscribe

**ML models not loading:**
```bash
# Verify models exist
ls -la models/
# Should see: vision_model.pt (6.2 MB) and audio_model.pkl (15.8 MB)
```

### Common Issues

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

---

## Development Workflow

### 1. Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests before making changes
pytest tests/ -v

# Make code changes
# Run tests after changes
pytest tests/ -v

# Commit if tests pass
git add .
git commit -m "Feature: description"
```

### 2. Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_all.py::TestMLModelsExist::test_vision_model_path_exists -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

### 3. Docker Testing

```bash
# Build local
docker-compose build

# Start containers
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

### 4. Production Deployment

```bash
# Tag version
git tag v1.0.0

# Push to repository
git push origin main --tags

# Deploy to Raspberry Pi
ssh pi@hive.local
cd smart-hive-ai
git pull origin main
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Key Components

### Edge Application (app.py)

- Reads sensor data at 60-second intervals
- Publishes telemetry to MQTT
- Subscribes to control commands
- Manages application lifecycle

### ML Inference Service (ml_inference_service.py)

- Continuous vision detection (YOLO v8)
- Periodic audio classification (scikit-learn)
- Publishes detections to MQTT
- Health monitoring

### Dashboard (dashboard/dashboard_app.py)

- Real-time sensor visualization
- Detection alerts
- Historical data analysis
- Control interface

### Configuration (config.py)

- Centralized settings
- Environment variable management
- MQTT topic definitions
- Interval configuration

---

## Performance

### Expected Performance

| Component | Performance | Notes |
|-----------|-------------|-------|
| Vision Inference | 50-150 ms/frame | YOLO v8, depends on hardware |
| Audio Classification | 100-500 ms/sample | 5-second audio samples |
| Telemetry Publishing | < 100 ms | MQTT publish latency |
| Dashboard Update | 1-5 seconds | Real-time updates |

### Resource Usage

| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| Edge App | 5-10% | 50-100 MB | < 50 MB |
| ML Service | 20-40% | 200-400 MB | ~ 25 MB (binary) |
| Dashboard | 2-5% | 30-50 MB | ~ 5 MB (app) |
| **Total** | **30-55%** | **300-600 MB** | **~100 MB** |

---

## Support & Documentation

- **README**: Overview and quick start
- **DEPLOYMENT.md**: Production deployment guide
- **CONFIGURATION_GUIDE.md**: Detailed configuration
- **TROUBLESHOOTING.md**: Common issues and solutions
- **GitHub Issues**: Report bugs and request features

---

## License

This project is licensed under the MIT License - see LICENSE file for details.

---

## Version

**Project**: Smart Hive AI  
**Version**: 1.0.0  
**Last Updated**: October 2025  
**Status**: Production Ready ✅

---

**For questions or issues, please open an issue on GitHub or contact the development team.**
