# Smart Hive AI - Final Deployment Guide

## Summary of Changes

### 1. **Separate Vision and Audio Microservices** ✅

You now have **THREE independent ML containers** instead of one combined container:

- **smart-hive-vision** (NEW): YOLO v8 object detection
  - Size: ~1.2GB (lightweight, OpenCV headless only)
  - CPU: ~1 core  
  - GPU: Not needed
  - Input: `/dev/video0` (USB camera)
  - Output: `hive/vision/results` (MQTT)
  
- **smart-hive-audio** (NEW): Audio classification  
  - Size: ~800MB (no OpenCV, audio only)
  - CPU: ~0.5 core
  - GPU: Not needed
  - Input: `/dev/snd` (microphone)
  - Output: `hive/audio/results` (MQTT)

- **smart-hive-ml** (LEGACY): Combined service (optional, for compatibility)
  - Can be disabled if using separate services
  - Remove from docker-compose if not needed

### 2. **Benefits of Separation**

✅ **Independent scaling** - Run multiple vision or audio instances if needed
✅ **Better resource management** - Each service uses only what it needs
✅ **Easier debugging** - Isolate issues to specific container
✅ **Separate failure domains** - Audio failure doesn't crash vision
✅ **Faster deployment** - Build only what changed
✅ **Smaller images** - Vision doesn't include audio libs, audio doesn't include OpenCV

### 3. **AWS Configuration - NO CHANGES NEEDED** ✅

Everything is pre-configured:
- ✅ MQTT topics auto-created
- ✅ DynamoDB table ready
- ✅ SSL certificates already in `certs/` folder
- ✅ AWS credentials auto-loaded from `~/.aws/credentials`

### 4. **Deployment on Raspberry Pi**

```bash
# 1. Pull latest changes
cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization

# 2. Stop old containers
docker compose down

# 3. Clean up old images (optional)
docker system prune -af

# 4. Build new separated services
docker compose build

# 5. Start all services
docker compose up -d

# 6. Verify status
docker compose ps

# Should show:
# mosquitto          ✅ Up
# edge-app           ✅ Up
# smart-hive-vision  ✅ Up (NEW)
# smart-hive-audio   ✅ Up (NEW)
# dashboard          ✅ Up
```

### 5. **Key Files**

**New Dockerfiles:**
- `Dockerfile.vision` - Vision-only container (lightweight)
- `Dockerfile.audio` - Audio-only container (NO OpenCV)

**New Services:**
- `ml_vision_service.py` - Vision inference loop
- `ml_audio_service.py` - Audio inference loop

**Requirements:**
- `requirements-vision.txt` - Vision deps only
- `requirements-audio.txt` - Audio deps only (NO OpenCV!)
- `requirements-ml.txt` - Original combined (still available)

**Updated:**
- `docker-compose.yml` - Now includes vision and audio services

### 6. **MQTT Topics**

**Edge App publishes:**
- `hive/telemetry` → Sensor data (temperature, humidity, vibration)

**Vision Service publishes:**
- `hive/vision/results` → Detection results with confidence

**Audio Service publishes:**
- `hive/audio/results` → Audio classification results

**Dashboard subscribes to all** and displays real-time data

### 7. **Troubleshooting**

**If vision fails:**
```bash
docker compose logs smart-hive-vision --tail 100
```

**If audio fails:**
```bash
docker compose logs smart-hive-audio --tail 100
```

**If MQTT issues:**
```bash
docker compose logs mosquitto --tail 100
```

**Check all services:**
```bash
docker compose ps
docker compose logs -f
```

### 8. **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi                             │
│                                                             │
│  ┌────────────┐                                            │
│  │  Sensors   │ (BME280, LIS3DH, Camera, Microphone)      │
│  └──────┬─────┘                                            │
│         │                                                  │
│  ┌──────▼────────────────────────────────────────────┐    │
│  │            Edge App (app.py)                      │    │
│  │  - Collects sensor data                           │    │
│  │  - Publishes to MQTT (hive/telemetry)            │    │
│  └──────┬────────────────────────────────────────────┘    │
│         │                                                  │
│  ┌──────▼──────────────┐   ┌──────────────────────────┐  │
│  │ MQTT Broker         │   │   Dashboard              │  │
│  │ (mosquitto)         │   │   - Web UI (port 5000)  │  │
│  │ - Topic routing     │   │   - Real-time display   │  │
│  │ - Pub/Sub           │   │   - MQTT subscription   │  │
│  └──┬───────┬──────────┘   └──────────────────────────┘  │
│     │       │                                             │
│  ┌──▼──┐ ┌──▼──┐                                         │
│  │Vision    Audio                                        │
│  │Service   Service                                      │
│  │ (NEW!)   (NEW!)                                       │
│  │          │                                            │
│  │ YOLO v8  │ Audio                                      │
│  │Detection │ Classification                            │
│  └──────────┴──────────────────────────────────────────┘ │
│                                                           │
└───────────────────────────────────────────────────────────┘
                          ↕ MQTT
                     AWS IoT Core
                          ↕
                    DynamoDB Table
```

### 9. **Next Steps**

1. Pull latest code on your Pi
2. Rebuild containers: `docker compose build`
3. Start services: `docker compose up -d`
4. Verify: `docker compose ps`
5. Check logs: `docker compose logs -f`
6. Access dashboard: http://raspberrypi.local:5000
7. Monitor AWS IoT Console for telemetry

**Everything is ready to deploy!** 🚀
