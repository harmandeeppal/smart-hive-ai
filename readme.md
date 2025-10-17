# Smart Hive AI

A professional, production-ready IoT system for real-time beehive monitoring and AI-powered queen bee detection using Raspberry Pi edge computing.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)
[![Tests](https://img.shields.io/badge/tests-20_passing-green.svg)]()

## 📋 Overview

Smart Hive AI is an intelligent beehive monitoring system that leverages edge computing and artificial intelligence to provide beekeepers with real-time insights into hive health and queen bee presence. The system combines multi-sensor data collection with cloud-based AWS services for a comprehensive monitoring solution.

### ✨ Key Features

- **🔴 Real-Time Multi-Sensor Monitoring**
  - Temperature and humidity (BME280 sensor)
  - Vibration detection (LIS3DH accelerometer)
  - Sound analysis (INMP441 microphone)
  - Live video streaming with detection overlays

- **🤖 AI-Powered Queen Bee Detection**
  - YOLO v8-based computer vision model for queen detection
  - Audio classification for hive activity analysis
  - Real-time inference on edge device
  - TensorFlow Lite optimization for Raspberry Pi

- **☁️ AWS Cloud Integration**
  - MQTT messaging via AWS IoT Core
  - Real-time telemetry persistence in DynamoDB
  - S3 integration for image storage (optional)
  - Secure certificate-based authentication

- **📊 Interactive Web Dashboard**
  - Real-time sensor visualization with gauges
  - Live video stream with AI detection indicators
  - WebSocket-based updates for instant data refresh
  - Responsive design for mobile and desktop
  - Sensor control and monitoring interface

- **🐳 Docker Containerization**
  - Three-service architecture (edge, ML, dashboard)
  - Resource-optimized for Raspberry Pi
  - Easy deployment and scaling
  - Environment isolation

- **🧪 Comprehensive Testing**
  - 20+ unit tests for core functionality
  - ML model path validation
  - Configuration validation
  - Sensor mock functionality
  - MQTT integration tests

## 🏗️ Architecture

The Smart Hive AI system follows a microservices architecture with three independent containerized services:

```
┌──────────────────────────────────────────────────────────────────┐
│                     RASPBERRY PI EDGE DEVICE                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   BME280        │  │   LIS3DH        │  │   INMP441       │ │
│  │ Temp/Humidity   │  │   Vibration     │  │     Sound       │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                │                                 │
│  ┌──────────────────────────────▼──────────────────────────────┐ │
│  │              DOCKER: smart-hive-edge                         │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │ app.py - Edge Application                             │ │ │
│  │  ├────────────────────────────────────────────────────────┤ │ │
│  │  │ • Sensor data collection (60s intervals)              │ │ │
│  │  │ • MQTT publishing to AWS IoT Core                     │ │ │
│  │  │ • DynamoDB persistence                               │ │ │
│  │  │ • Flask video streaming server (port 5001)           │ │ │
│  │  │ • Real-time telemetry loop                           │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └──────────────┬───────────────────────────────────────┬────────┘ │
│                 │                                       │          │
│  ┌──────────────▼───────────────────────────────────────▼────────┐ │
│  │         DOCKER: smart-hive-ml (ML Microservice)               │ │
│  │  ┌────────────────────────────────────────────────────────┐  │ │
│  │  │ ml_inference_service.py - ML Processing               │  │ │
│  │  ├────────────────────────────────────────────────────────┤  │ │
│  │  │ • YOLO v8 vision inference                            │  │ │
│  │  │ • Audio classification                                │  │ │
│  │  │ • Real-time detection results                         │  │ │
│  │  │ • Resource-isolated from edge app                     │  │ │
│  │  │ • MQTT control & results topics                       │  │ │
│  │  └────────────────────────────────────────────────────────┘  │ │
│  └──────────────┬───────────────────────────────────────┬────────┘ │
│                 │                                       │          │
│  ┌──────────────▼───────────────────────────────────────▼────────┐ │
│  │       DOCKER: smart-hive-dashboard (Web Dashboard)            │ │
│  │  ┌────────────────────────────────────────────────────────┐  │ │
│  │  │ dashboard_app.py - Web Interface                       │  │ │
│  │  ├────────────────────────────────────────────────────────┤  │ │
│  │  │ • Flask web server (port 5000)                        │  │ │
│  │  │ • Real-time data visualization                        │  │ │
│  │  │ • Live video stream display                           │  │ │
│  │  │ • WebSocket-based updates                             │  │ │
│  │  │ • MQTT telemetry subscription                         │  │ │
│  │  └────────────────────────────────────────────────────────┘  │ │
│  └──────────────┬───────────────────────────────────────┬────────┘ │
│                 │                                       │          │
└─────────────────┼───────────────────────────────────────┼──────────┘
                  │              MQTT               │
                  │          (AWS IoT Core)         │
      ┌───────────▼─────────────────────────────────▼────────────┐
      │                    AWS CLOUD SERVICES                     │
      ├────────────────────────────────────────────────────────────┤
      │ ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐  │
      │ │   IoT Core      │  │  DynamoDB    │  │      S3      │  │
      │ │  MQTT Broker    │  │   Database   │  │   Storage    │  │
      │ └─────────────────┘  └──────────────┘  └──────────────┘  │
      └────────────────────────────────────────────────────────────┘
```

## 🛠️ System Components

### 1. Edge Application (`app.py`)
- Sensor data collection and processing
- MQTT publishing to AWS IoT Core
- DynamoDB data persistence
- Video streaming server
- Mock/real sensor abstraction layer
- Telemetry loop (60-second intervals)

### 2. ML Inference Microservice (`ml_inference_service.py`)
- Independent ML processing service
- YOLO v8 vision model for queen bee detection
- Audio classification for hive activity
- MQTT-based control and results
- Resource-isolated for Raspberry Pi constraints

### 3. Web Dashboard (`dashboard/dashboard_app.py`)
- Real-time data visualization
- Live video streaming
- Interactive sensor controls
- WebSocket communication
- Responsive web interface

### 4. Configuration Management (`config.py`)
- Centralized environment-based configuration
- AWS IoT Core settings
- MQTT topics and intervals
- Feature flags and toggles

## 📦 Hardware Requirements

### Raspberry Pi Setup
- **Device**: Raspberry Pi 4 (2GB RAM minimum, 4GB+ recommended)
- **Storage**: MicroSD Card (16GB minimum, Class 10 recommended)
- **Power**: 5V 3A USB-C Power Supply

### Sensors
| Sensor | Model | Function | Connection |
|--------|-------|----------|-----------|
| Temperature/Humidity | BME280 | Environmental monitoring | I2C (0x76) |
| Vibration | LIS3DH | Hive activity detection | I2C (0x19) |
| Microphone | INMP441 | Sound analysis | I2S |
| Camera | Logitech C270 | Live video & detection | USB |

### Connections
- **I2C Bus 1** (GPIO 2/3): BME280 + LIS3DH sensors
- **USB Ports**: Camera and microphone
- **Network**: Ethernet or WiFi (required for AWS)

## 💻 Software Stack

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.9+ | Runtime |
| Docker | Latest | Containerization |
| Flask | 2.x | Web framework |
| MQTT (Paho) | 1.6+ | Message broker |
| OpenCV | 4.x | Computer vision |
| TensorFlow Lite | 2.x | ML inference |
| Boto3 | 1.26+ | AWS SDK |
| PyTorch | 2.x | Deep learning |
| scikit-learn | Latest | ML algorithms |

## 🚀 Quick Start

### For Laptop Development (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/harmandeeppal/smart-hive-ai.git
cd smart-hive-ai

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run tests (verify setup)
pytest tests/ -v

# 5. Start services in mock mode (3 terminal windows)

# Terminal 1: Edge application
export IS_MOCK_ENVIRONMENT=true
python app.py

# Terminal 2: ML inference service
python ml_inference_service.py

# Terminal 3: Dashboard
cd dashboard
python dashboard_app.py

# 6. Open browser
# http://localhost:5000
```

### For Raspberry Pi Deployment (10 minutes)

```bash
# 1. Setup credentials
cp .env.example .env
nano .env  # Add your AWS IoT endpoint

# 2. Copy AWS certificates
cp your-certificate.pem certs/
cp your-private-key.pem certs/
cp AmazonRootCA1.pem certs/

# 3. Deploy with Docker
docker-compose build
docker-compose up -d

# 4. Monitor
docker-compose logs -f

# 5. Access dashboard
# http://<raspberry-pi-ip>:5000
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# AWS IoT Core
AWS_ENDPOINT=your-endpoint.iot.ap-southeast-2.amazonaws.com
CERT_FILE_NAME=your-certificate.pem
KEY_FILE_NAME=your-private-key.pem

# Flask
SECRET_KEY=your-secret-key-here

# AWS Services
S3_BUCKET_NAME=your-bucket-name
ENABLE_S3=false  # Set to true for image uploads

# Development
IS_MOCK_ENVIRONMENT=false  # Set to true for laptop testing
```

### Hardware Configuration (`config.py`)

```python
# I2C Addresses
BME280_ADDRESS = 0x76
LIS3DH_ADDRESS = 0x19

# Camera Settings
CAMERA_TYPE = "USB"
CAMERA_DEVICE_INDEX = 0

# Sensor Intervals (seconds)
TELEMETRY_INTERVAL_SECONDS = 60

# AI Detection
VISION_DETECTION_MODE = "continuous"
VISION_PROCESS_EVERY_N_FRAMES = 3
VISION_CONFIDENCE_THRESHOLD = 0.5

# AWS Services
DYNAMODB_TABLE = "SmartHiveTelemetry"
AWS_REGION = "ap-southeast-2"

# MQTT Topics
TOPIC_TELEMETRY = "hive/telemetry"
TOPIC_VISION = "hive/vision"
TOPIC_CONTROL = "hive/control"
```

## 📁 Project Structure

```
smart-hive-ai/
├── README.md                           # This file
├── QUICK_START.md                      # Quick reference guide
├── DOCUMENTATION_CLEANUP_SUMMARY.md    # Documentation overview
│
├── Core Application Files
├── app.py                              # Main edge application (726 lines)
├── config.py                           # Configuration management (244 lines)
├── ml_inference_service.py             # ML microservice (631 lines)
│
├── Component Abstractions
├── mock_components.py                  # Mock sensors for testing
├── real_components.py                  # Real hardware implementations
│
├── Dashboard Application
├── dashboard/
│   ├── dashboard_app.py               # Dashboard web app (267 lines)
│   ├── static/
│   │   ├── app.js                     # Frontend logic
│   │   └── styles.css                 # Dashboard styling
│   └── templates/
│       └── index.html                 # Dashboard UI
│
├── ML Models & Processors
├── ml_vision_model/
│   └── vision_processor.py            # YOLO v8 processor
├── ml_audio_model/
│   └── audio_processor.py             # Audio classifier
├── models/                            # AI models directory
│   ├── vision_model.pt                # YOLO v8 model (6.23 MB)
│   ├── audio_model.pkl                # Audio classifier (15.8 MB)
│   └── queen_bee.tflite               # TensorFlow Lite model
│
├── Docker Configuration
├── docker-compose.yml                 # Multi-container orchestration
├── Dockerfile.edge                    # Edge app container
├── Dockerfile.dashboard               # Dashboard container
├── Dockerfile.ml                      # ML service container
│
├── Dependencies
├── requirements.txt                   # All dependencies
├── requirements-edge.txt              # Edge-specific
├── requirements-dashboard.txt         # Dashboard-specific
├── requirements-ml.txt                # ML-specific
│
├── AWS IoT Certificates
├── certs/
│   ├── AmazonRootCA1.pem             # AWS root CA
│   ├── your-certificate.pem          # Device certificate
│   └── your-private-key.pem          # Private key
│
├── Documentation
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
