# Quick Start (Raspberry Pi)

Follow this checklist to build and launch Smart Hive AI from a clean Raspberry Pi.

## 1. Update the Pi
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git docker.io docker-compose-plugin python3-pip v4l-utils
sudo usermod -aG docker $USER
sudo usermod -aG video $USER
sudo usermod -aG audio $USER
sudo reboot
```

## 2. Clone the repository
```bash
ssh pi@<pi-ip-address>
git clone https://github.com/harmandeeppal/smart-hive-ai.git
cd smart-hive-ai
```

## 3. Configure environment variables
```bash
cp .env.example .env
nano .env   # populate MQTT, AWS, and feature flags as required
```

If you are not using AWS services, disable or remove those entries.

## 4. Verify expected files
```bash
ls Dockerfile.*
ls requirements-*.txt
ls models/
```
Ensure the audio model (`models/audio_model.pkl`) and optional vision model (`models/vision_model.pt`) are present before continuing.

## 5. Build containers
```bash
docker compose build --no-cache
```
On a Raspberry Pi 4 this takes approximately 45–55 minutes for all services.

## 6. Launch the stack
```bash
docker compose up -d
docker compose ps
```
You should see `mosquitto`, `smart-hive-edge`, `smart-hive-audio`, `smart-hive-dashboard`, and optionally `smart-hive-vision` in the `Up` state.

## 7. Sanity checks
```bash
docker logs smart-hive-edge --tail 50
docker logs smart-hive-audio --tail 20
curl -I http://localhost:5001/video_feed
curl -I http://localhost:5000
```
- Edge logs should include `Camera initialized successfully`.
- Audio logs should show `Audio processor initialised`.
- HTTP checks should return `200 OK`.

## 8. Access the dashboard
Open `http://<pi-ip-address>:5000` in a browser on the same network. Trigger a one-minute audio recording to confirm classification works end-to-end.

## 9. Keep the system updated
```bash
git pull
docker compose pull
docker compose build --no-cache
docker compose up -d
```
Run the sequence above when new commits land or dependencies change.

For deeper deployment detail, read `core/deployment.md`. Service-specific information lives in `audio/guide.md` and `camera/guide.md`.
