# Smart Hive AI

Smart Hive AI is an edge-first beehive monitoring platform that combines Raspberry Pi sensors, audio machine learning, optional vision inference, and a real-time dashboard. The goal is to give beekeepers actionable insight into hive activity while keeping the deployment lightweight enough to run entirely on-site.

## Key Capabilities
- Continuous telemetry from BME280 (temperature/humidity), LIS3DH (vibration), and INMP441 (audio) sensors.
- Audio classification microservice (scikit-learn) that flags queen activity using sliding-window analysis and configurable confidence thresholds.
- Optional YOLO-based vision service for image-based queen detection when a trained model is supplied.
- Flask dashboard that shows sensor trends, camera streaming, and audio ML status with MQTT-backed live updates.
- Docker Compose stack that runs the edge app, audio service, vision service, dashboard, and Mosquitto broker on a Raspberry Pi 4.

## Service Topology
```
Sensors / USB Camera
        |
        v
  Edge Application -- publishes telemetry & frames --> Mosquitto
        |                                             ^       ^
        +-- HTTP video feed --------------------------+       |
        v                                                     |
 Audio Service <-- windowed audio jobs via MQTT --------------+
        |
        v
 Vision Service (optional YOLO inference, uses MQTT frames)
        |
        v
 Dashboard (Flask + Socket.IO web UI)
```

## Hardware Checklist
- Raspberry Pi 4 (4 GB RAM recommended) with 32 GB microSD.
- BME280 temperature/humidity sensor (I2C).
- LIS3DH accelerometer (I2C).
- INMP441 microphone (I2S or USB adapter if preferred).
- USB webcam (tested with Logitech C270-class devices).
- Reliable 5 V / 3 A power supply and internet connectivity.

## Software Prerequisites
- Raspberry Pi OS 64-bit (Bookworm or newer) with SSH access.
- Docker 24+ and Docker Compose v2 (`docker compose` plugin).
- Git and Python 3.9+ for local development and diagnostics.
- Optional: AWS CLI if using DynamoDB or IoT Core integrations.

## Getting Started
1. Clone the repository on the Raspberry Pi.
2. Copy `.env.example` to `.env` and populate broker, AWS, and feature flags.
3. Review `docs/core/quick-start.md` for command-by-command setup.
4. Build the containers with `docker compose build --no-cache`.
5. Launch the stack with `docker compose up -d` and verify using the dashboard at `http://<pi-ip>:5000`.

Detailed deployment guidance, troubleshooting flows, and component deep dives are linked below.

## Documentation
- Project index: [`docs/index.md`](docs/index.md)
- Core guides: [`docs/core/`](docs/core/)
- Audio ML guide: [`docs/audio/guide.md`](docs/audio/guide.md)
- Camera guide: [`docs/camera/guide.md`](docs/camera/guide.md)
- Configuration & reference: [`docs/reference/`](docs/reference/)

Each guide has been refreshed to remove historical branches and deprecated services. If you need a linear onboarding path, begin with `docs/index.md`.

## Contributing
Contributions are welcome. Please:
- Run `python -m pytest` before opening a pull request.
- Keep documentation in sync with behavioural changes.
- Follow PEP 8 formatting (see `black` and `flake8` config recommendations in the docs).

## License
Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
