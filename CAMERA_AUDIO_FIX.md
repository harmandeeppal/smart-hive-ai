# Camera & Audio Fix Deployment Guide

## 🔧 Fixes Applied (Commit 9313f3f)

### 1. ✅ **Camera Video Feed Fixed**
- Removed circular dependency in vision_processor
- Direct cv2.VideoCapture initialization
- Proper test frame validation
- Better error logging

### 2. ✅ **Audio Microphone Detection**
- Auto-detect Samson Meteorite Mic
- Fallback to C270 webcam mic
- Better device selection logging

### 3. ✅ **UI Improvements**
- Title: "AI Vision and Live Video Feed"
- Blue toggle buttons (#4267B2) - matches other sensors
- Consistent ON/OFF states

---

## 🚀 Deploy on Raspberry Pi

```bash
cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization

# Rebuild with fixes (10-15 min total)
docker compose build --no-cache smart-hive-edge-app smart-hive-audio dashboard
docker compose up -d smart-hive-edge-app smart-hive-audio dashboard

sleep 15

# Check camera
docker logs smart-hive-edge-app | grep "Camera initialized"

# Check microphone
docker logs smart-hive-audio | grep "Using microphone"

# Test audio classification
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'
sleep 6
docker logs smart-hive-audio --tail 10
```

---

## ✅ Expected Results

**Camera:**
```
✅ Camera initialized successfully (640x480)
```

**Microphone:**
```
📱 Using microphone: Samson Meteorite Mic (device 1)
✅ Audio model loaded successfully
```

**Audio Test:**
```
⏺ Recording for 5 seconds...
✅ Recording complete (110250 samples)
✅ Classification: queen_present (confidence: 0.87)
```

**Dashboard (http://192.168.88.16:5000):**
- Video feed showing live camera
- Blue toggle buttons
- Audio classification completing successfully

---

## 🐛 If Issues Persist

### Camera Not Working:
```bash
# Check device exists
ls -l /dev/video0

# Check Docker access
docker exec smart-hive-edge-app ls -l /dev/video0

# Test directly
docker exec smart-hive-edge-app python3 -c "
import cv2
cam = cv2.VideoCapture(0)
print('Opened:', cam.isOpened())
ret, frame = cam.read()
print('Frame:', frame.shape if ret else 'Failed')
cam.release()
"
```

### Audio Still "unknown":
```bash
# Packages not installed - complete clean rebuild
docker compose stop smart-hive-audio
docker compose rm -f smart-hive-audio
docker rmi smart-hive-audio:latest
docker builder prune -f

docker compose build --no-cache smart-hive-audio
docker compose up -d smart-hive-audio

# Verify
docker logs smart-hive-audio | grep "Audio model loaded"
# MUST see: ✅ Audio model loaded successfully
```

### Check Microphone Devices:
```bash
docker exec smart-hive-audio python3 -c "
import sounddevice as sd
print(sd.query_devices())
"
```
