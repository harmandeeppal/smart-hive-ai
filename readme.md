# Smart Hive AI

A professional IoT system for real-time beehive monitoring and AI-powered queen bee detection using Raspberry Pi edge computing.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-compose-blue.svg)](https://docs.docker.com/compose/)

## Overview

Smart Hive AI is an intelligent beehive monitoring system that combines environmental sensing, audio analysis, vibration detection, and computer vision to provide beekeepers with real-time insights into hive health and queen bee presence.

### Key Features

- **Multi-Sensor Data Collection**: Temperature, humidity, vibration, and sound monitoring
- **AI-Powered Queen Detection**: TensorFlow Lite-based computer vision for queen bee identification
- **Real-Time Video Streaming**: Live hive camera feed with detection overlays
- **Cloud Integration**: AWS IoT Core for MQTT messaging and DynamoDB for data persistence
- **Interactive Dashboard**: Web-based UI for monitoring and sensor control
- **Edge Computing**: Raspberry Pi-based processing for low-latency detection
- **NZ Timezone Support**: Configurable timezone display for local monitoring

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Raspberry Pi Edge Device                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   BME280     │  │   LIS3DH     │  │   INMP441    │          │
│  │ Temp/Humidity│  │  Vibration   │  │    Sound     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                  │
│                            │                                      │
│                  ┌─────────▼─────────┐                           │
│                  │   Edge Application │                           │
│                  │  (app.py)          │                           │
│                  └─────────┬─────────┘                           │
│                            │                                      │
│         ┌──────────────────┼──────────────────┐                 │
│         │                  │                  │                  │
│    ┌────▼────┐      ┌─────▼─────┐     ┌─────▼─────┐            │
│    │ MQTT    │      │ Video     │     │ DynamoDB  │            │
│    │ Publisher│     │ Streaming │     │ Writer    │            │
│    └────┬────┘      └─────┬─────┘     └─────┬─────┘            │
│         │                  │                  │                  │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          │   AWS Cloud      │                  │
      ┌───▼───┐          ┌───▼───┐         ┌───▼───┐
      │  IoT  │          │ Users │         │ Dynamo│
      │ Core  │          │       │         │  DB   │
      └───┬───┘          └───────┘         └───────┘
          │
     ┌────▼────┐
     │Dashboard│
     │  (Web)  │
     └─────────┘
```

## Hardware Requirements

### Raspberry Pi Configuration
- Raspberry Pi 4 (2GB RAM minimum, 4GB recommended)
- MicroSD Card (16GB minimum, Class 10)
- 5V 3A USB-C Power Supply

### Sensors
- **BME280**: Temperature and humidity sensor (I2C address: 0x76)
- **LIS3DH**: 3-axis accelerometer for vibration detection (I2C address: 0x19)
- **INMP441**: I2S MEMS microphone for sound analysis
- **Logitech C270**: USB webcam for video capture

### Connections
- I2C Bus 1 (GPIO 2/3): BME280 and LIS3DH
- USB Ports: Webcam and microphone
- Internet: Ethernet or WiFi for AWS connectivity

## Software Stack

- **Operating System**: Raspberry Pi OS (64-bit recommended)
- **Runtime**: Python 3.9+
- **Container Platform**: Docker and Docker Compose
- **ML Framework**: TensorFlow Lite 2.x
- **Web Framework**: Flask 2.x
- **MQTT Client**: Paho MQTT 1.6+
- **AWS SDK**: Boto3 1.26+
- **Computer Vision**: OpenCV 4.x

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/harmandeeppal/smart-hive-ai.git
cd smart-hive-ai
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env
```

Required environment variables:
```bash
AWS_ENDPOINT=your-iot-endpoint.iot.ap-southeast-2.amazonaws.com
CERT_FILE_NAME=your-certificate.pem.crt
KEY_FILE_NAME=your-private.pem.key
SECRET_KEY=your-flask-secret-key
S3_BUCKET_NAME=your-s3-bucket
ENABLE_S3=false
```

### 3. Add AWS Certificates

Place your AWS IoT certificates in the `certs/` directory:
```bash
certs/
├── AmazonRootCA1.pem
├── your-certificate.pem.crt
└── your-private.pem.key
```

### 4. Deploy with Docker

```bash
docker compose up -d
```

### 5. Access Dashboard

Open browser and navigate to:
```
http://raspberrypi.local:5000
```

## Configuration

### Hardware Settings

Edit `config.py` to match your hardware:

```python
# I2C Addresses
BME280_ADDRESS = 0x76
LIS3DH_ADDRESS = 0x19

# Camera Configuration
CAMERA_TYPE = "USB"
CAMERA_DEVICE_INDEX = 0

# Sensor Intervals
TELEMETRY_INTERVAL_SECONDS = 60
```

### AI Detection Settings

```python
# Detection Mode
VISION_DETECTION_MODE = "continuous"  # or "interval"

# Processing Frequency
VISION_PROCESS_EVERY_N_FRAMES = 3  # Process every 3rd frame

# Confidence Threshold
VISION_CONFIDENCE_THRESHOLD = 0.5  # 50% minimum confidence
```

### AWS Configuration

```python
# DynamoDB
DYNAMODB_TABLE = "SmartHiveTelemetry"
ENABLE_DYNAMODB = True
AWS_REGION = "ap-southeast-2"

# MQTT Topics
TOPIC_TELEMETRY = "hive/telemetry"
TOPIC_VISION = "hive/vision"
TOPIC_CONTROL = "hive/control"
```

## Project Structure

```
smart-hive-ai/
├── app.py                      # Main edge application
├── config.py                   # Configuration management
├── mock_components.py          # Mock sensors for testing
├── real_components.py          # Real hardware implementations
├── docker-compose.yml          # Container orchestration
├── Dockerfile.edge             # Edge application container
├── Dockerfile.dashboard        # Dashboard container
├── requirements-edge.txt       # Edge dependencies
├── requirements-dashboard.txt  # Dashboard dependencies
├── certs/                      # AWS IoT certificates
├── dashboard/                  # Web dashboard application
│   ├── dashboard_app.py
│   ├── static/
│   └── templates/
├── docs/                       # Documentation
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── CONFIGURATION.md
│   ├── TROUBLESHOOTING.md
│   └── API.md
├── models/                     # AI models
│   └── queen_bee.tflite
├── scripts/                    # Utility scripts
│   ├── check_dynamodb_timestamps.py
│   ├── diagnose_dynamodb.py
│   └── update_dynamodb_timestamps.py
└── tests/                      # Test suite
    └── __init__.py
```

## Development

### Local Development with Mock Sensors

For development without Raspberry Pi hardware:

```python
# In config.py
IS_MOCK_ENVIRONMENT = True
```

Run locally:
```bash
python app.py
```

### Running Tests

```bash
pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines:
```bash
# Check code style
flake8 app.py config.py

# Format code
black app.py config.py
```

## Monitoring

### View Container Logs

```bash
# Edge application logs
docker logs -f smart-hive-edge

# Dashboard logs
docker logs -f smart-hive-dashboard
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

## Troubleshooting

### Common Issues

**I2C Permission Denied**
```bash
sudo usermod -a -G i2c pi
sudo reboot
```

**Container Cannot Access Sensors**
```yaml
# In docker-compose.yml, ensure:
devices:
  - /dev/i2c-1:/dev/i2c-1
  - /dev/video0:/dev/video0
privileged: true
```

**AWS Connection Failed**
```bash
# Verify credentials are mounted
docker exec smart-hive-edge ls -la /root/.aws/

# Test AWS connection
docker exec smart-hive-edge python3 -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

For detailed troubleshooting, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## API Reference

### MQTT Topics

**hive/telemetry**
```json
{
  "timestamp": 1760526982,
  "timestamp_nz": "2025-10-16 00:16:22 NZDT",
  "temperature": 34.5,
  "humidity": 58.0,
  "vibration_rms": 0.05,
  "sound_db": 52.0,
  "sound_freq": 200.0
}
```

**hive/vision**
```json
{
  "timestamp": 1760526982,
  "queen_detected": true,
  "confidence": 0.87,
  "frame_timestamp": "2025-10-16T00:16:22+13:00"
}
```

For complete API documentation, see [docs/API.md](docs/API.md)

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make changes with proper documentation
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- TensorFlow Lite for efficient edge AI inference
- AWS IoT Core for reliable cloud connectivity
- OpenCV community for computer vision tools
- Raspberry Pi Foundation for accessible edge computing

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/harmandeeppal/smart-hive-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/harmandeeppal/smart-hive-ai/discussions)

## Roadmap

- [ ] Multi-hive support
- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Swarm prediction algorithms
- [ ] Weather integration
- [ ] Alert notification system

---

**Built with passion for beekeeping and technology** 

