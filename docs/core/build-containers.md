# Container Build Guide (Raspberry Pi)

This guide covers clean rebuilds of the Smart Hive AI container stack. Use it when refreshing dependencies, onboarding a new device, or recovering from a broken image build.

## Services
- `mosquitto` (pulls from Docker Hub, no build step).
- `smart-hive-edge` (Dockerfile.edge).
- `smart-hive-audio` (Dockerfile.audio).
- `smart-hive-vision` (Dockerfile.vision, optional).
- `smart-hive-dashboard` (Dockerfile.dashboard).

## Preparation
```bash
cd ~/smart-hive-ai
docker compose down
docker system prune -af   # optional, frees disk space
```

Ensure all Dockerfiles and requirements files are present:
```bash
ls Dockerfile.*
ls requirements-*.txt
```

## Build Options

### A. Sequential (recommended for first-time setup)
```bash
docker compose build --no-cache smart-hive-dashboard
docker compose build --no-cache smart-hive-edge
docker compose build --no-cache smart-hive-audio
docker compose build --no-cache smart-hive-vision   # skip if not using vision
```

### B. All services in one pass
```bash
docker compose build --no-cache
```

## Expected Outputs
- `smart-hive-dashboard`: ~450 MB image, install logs for Flask, Socket.IO, and front-end dependencies.
- `smart-hive-edge`: ~1.2 GB image, OpenCV and sensor libraries compiled; log ends with `Successfully tagged smart-hive-edge:latest`.
- `smart-hive-audio`: ~900 MB image, includes librosa, scikit-learn, and sounddevice.
- `smart-hive-vision`: ~1.4 GB image, installs ultralytics/YOLO when enabled.

Check the result with:
```bash
docker images | grep smart-hive
```

## Common Build Failures
| Symptom | Resolution |
| --- | --- |
| `No space left on device` | Run `docker system prune -af`, then rerun the build. Ensure at least 8 GB free. |
| Pypi download errors | Confirm the Pi has internet access. Retry the build; temporary network issues are common. |
| `gcc: internal compiler error` | The Pi is running out of RAM. Close other processes or enable swap. |
| `sounddevice` wheel failure | Ensure `portaudio19-dev` is installed on the host: `sudo apt install portaudio19-dev`. |

## Post-Build Steps
```bash
docker compose up -d
docker compose logs -f
```
Watch for:
- Edge service reporting the camera backend and resolution.
- Audio service announcing the loaded model and confidence threshold.
- Dashboard service confirming Flask is listening on port 5000.

If using the vision service, verify it loads `vision_model.pt` and subscribes to the MQTT frame topic. Disable the service if you do not intend to use it to save resources.

Keep this procedure handy whenever dependency updates or library changes require a clean rebuild.
