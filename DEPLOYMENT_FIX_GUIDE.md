# 🚀 Option A Deployment Fix Guide

## Current Status
✅ MQTT broker (mosquitto) - **WORKING** (listening on 0.0.0.0:1883)  
✅ Edge-app - **RUNNING** (capturing frames but frame publishing logs missing)  
✅ Vision service - **CONNECTED** (to MQTT, subscribed to topic)  
❌ Vision model - **MISSING** (model file not found in Docker image)  
❓ Frame publishing - **UNCLEAR** (no publish confirmation logs)

## What We Fixed
- ✅ Mosquitto "local only mode" issue (created mosquitto.conf)
- ✅ Docker container-to-container MQTT communication
- ✅ Vision service MQTT connection retry logic
- ✅ MQTT client version compatibility
- ⏳ Added debug logging to frame publisher (just pushed)

---

## 📋 Fix Instructions (Run on Raspberry Pi)

### Step 1: Pull Latest Code with Debug Logging
```bash
cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization
```

### Step 2: Verify Model File Exists Locally
```bash
# Check if model file is on Pi
ls -lh ~/smart-hive-ai/models/vision_model.pt

# If it doesn't exist, that's a git LFS issue
# For now, we'll use a workaround
```

**If the file doesn't exist**: The model may be tracked with Git LFS. Run:
```bash
# Install Git LFS
sudo apt-get install -y git-lfs

# Pull LFS files
git lfs pull
git lfs checkout
```

### Step 3: Rebuild Docker Images
```bash
# Rebuild all images to include latest code with debug logging
docker compose build

# This takes ~5-10 minutes on Pi, rebuilds all 5 services
```

### Step 4: Stop and Restart Services
```bash
docker compose down
docker compose up -d
sleep 15
```

### Step 5: Verify All Components

**Check Edge-App Frame Publishing:**
```bash
docker logs smart-hive-edge | grep -i "camera\|frame\|publish" | tail -20
# Should show:
# ✅ "📹 Camera frame publisher started"
# ✅ "📤 Published XXX bytes to hive/telemetry/camera/frame" (every 5 seconds)
```

**Check Vision Service MQTT Connection:**
```bash
docker logs smart-hive-vision | grep -i "mqtt\|connected\|frame" | tail -10
# Should show:
# ✅ "✅ MQTT connected successfully"
# ✅ "📨 Subscribed to: hive/telemetry/camera/frame"
# ✅ "Model loaded successfully" (once model is in place)
```

**Check Mosquitto Listener:**
```bash
docker logs mosquitto | grep -i "listening\|port 1883" | tail -5
# Should show:
# ✅ "Opening ipv4 listen socket on port 1883"
# ✅ NOT "local only mode"
```

**Test Frame Flow (1-frame test):**
```bash
# Terminal 1 - Subscribe to frames for 10 seconds
timeout 10 docker exec mosquitto mosquitto_sub -t "hive/telemetry/camera/frame" -C 1 | wc -c
# Should return: a number like 45000 (bytes received)
```

**Check All Services Status:**
```bash
docker compose ps
# Expected output:
# ✅ mosquitto    - Up
# ✅ smart-hive-edge    - Up
# ✅ smart-hive-vision  - Up (health: starting or healthy)
# ⏸️  smart-hive-audio   - Restarting (not critical for Option A)
# ⏸️  smart-hive-dashboard - Up or Restarting (not critical for Option A)
```

---

## 🔍 Troubleshooting Checklist

### Issue: "Model file not found: models/vision_model.pt"

**Cause**: Model file not copied into Docker image (either not cloned or not in build context)

**Fixes** (try in order):

1. **Check local file exists**
   ```bash
   ls -lh ~/smart-hive-ai/models/
   # Should show: vision_model.pt and queen_bee.tflite
   ```

2. **If files don't exist, pull with Git LFS**
   ```bash
   cd ~/smart-hive-ai
   git lfs install
   git lfs pull
   git lfs checkout
   ls -lh models/
   ```

3. **Rebuild with no cache (forces fresh copy)**
   ```bash
   docker compose build --no-cache smart-hive-vision
   docker compose restart smart-hive-vision
   ```

4. **Verify model in running container**
   ```bash
   docker exec smart-hive-vision ls -lh /app/models/
   # Should show vision_model.pt
   ```

---

### Issue: "Frame Publishing Not Confirming"

**Expected Behavior**: Edge-app logs should show "📤 Published XXX bytes" every 5 seconds

**Checks**:

1. **Verify publisher is running**
   ```bash
   docker logs smart-hive-edge | grep "Camera frame publisher"
   # Should show: "📹 Camera frame publisher started"
   ```

2. **Check frame capture is working**
   ```bash
   docker logs smart-hive-edge | grep "captured test frame"
   # Should show: "Camera successfully captured test frame: (480, 640, 3)"
   ```

3. **Check MQTT client is connected**
   ```bash
   docker logs smart-hive-edge | grep "MQTT"
   # Should show MQTT connection messages
   ```

4. **If no publish logs, check ENABLE_CAMERA_FRAME_PUBLISHING**
   ```bash
   grep "ENABLE_CAMERA_FRAME_PUBLISHING" ~/smart-hive-ai/config.py
   # Should show: True
   ```

5. **Manually test MQTT publish from edge-app container**
   ```bash
   docker exec smart-hive-edge \
     mosquitto_pub -h mosquitto -p 1883 \
     -t "hive/telemetry/camera/frame" \
     -m "test" -v
   # Should show: "Sending PUBLISH..."
   ```

---

### Issue: Vision Service Still Showing Unhealthy

**Wait for health check**:
```bash
# Health check takes 30 seconds, gives 3 retries
# Watch real-time:
watch -n 2 'docker compose ps'
# Press Ctrl+C to exit

# Should eventually show: "Up (healthy)"
```

**If it stays unhealthy after model fix**:
```bash
# Check health check command
docker exec smart-hive-vision python -c "import cv2; from ultralytics import YOLO; print('OK')"

# If that fails, rebuild without cache
docker compose build --no-cache smart-hive-vision
```

---

## 📊 Expected End-to-End Frame Flow

```
1. Edge-App (3 FPS)
   └─> Captures frame (480x640 RGB)
   └─> Resizes to 50% (240x320)
   └─> Compresses to JPEG (80% quality) = ~40-50KB
   └─> ✅ Publishes to "hive/telemetry/camera/frame"

2. Mosquitto MQTT Broker
   └─> Receives frame on topic
   └─> ✅ Broadcasts to all subscribers

3. Vision Service (subscribes to same topic)
   └─> ✅ Receives JPEG frame
   └─> Decodes to OpenCV format
   └─> ✅ Runs YOLO inference
   └─> ✅ Publishes results to "hive/vision/results"

4. Result: NO /dev/video0 CONFLICTS! ✅
```

---

## ✅ Success Indicators

**Frame flow is working when you see**:

```bash
# Edge-app logs (every 5 seconds)
📤 Published 45873 bytes to hive/telemetry/camera/frame

# Vision service logs (every 5 seconds, if model present)
📥 Received frame from MQTT (45873 bytes)
🎯 YOLO inference: 2 detections (confidence: 0.85, 0.72)
📤 Published results to hive/vision/results
```

**To test**:
```bash
# Get one frame to verify it's flowing
timeout 10 docker exec mosquitto mosquitto_sub -t "hive/telemetry/camera/frame" -C 1 | wc -c
# Returns: ~45000 ✅

# Get vision results
timeout 10 docker exec mosquitto mosquitto_sub -t "hive/vision/results" -C 1
# Returns: {"frame_id": 123, "detections": [...]} ✅
```

---

## 🎯 Next Steps After Fixes

1. **Verify model loads** - Check logs for "Model loaded successfully"
2. **Test frame publishing** - Run mosquitto_sub to receive actual frames
3. **Test vision inference** - Check vision results being published
4. **Verify no device conflicts** - ps aux | grep /dev/video0 should only show edge-app
5. **Document baseline performance** - Record CPU, memory, FPS metrics
6. **Create completion summary** - Option A deployment complete!

---

## 📝 Git Commit Tracking

| Commit | Message | Issue Fixed |
|--------|---------|-------------|
| 4798221 | fix: Configure mosquitto to listen on all interfaces | Mosquitto "local only mode" |
| d4784f9 | fix: Add MQTT connection retry logic | Connection timing |
| 3f286e1 | fix: Handle paho-mqtt version compatibility | MQTT version mismatch |
| 6ec7c2b | fix: Handle missing certificate filenames | Cert path errors |
| c7eef54 | feat: Implement Option A - MQTT frame transmission | Architecture design |
| a630bde | debug: Add logging to frame publisher for diagnostics | Frame publishing verification |

---

## 🆘 Emergency Debug Commands

```bash
# See ALL logs from edge-app
docker logs smart-hive-edge

# See ALL logs from vision service
docker logs smart-hive-vision

# Real-time logs (follow mode)
docker logs -f smart-hive-edge

# Check MQTT broker connections
docker logs mosquitto | grep "New connection\|client"

# List all MQTT topics with data
docker exec mosquitto mosquitto_sub -h localhost -t "#" -v -C 5

# Check system resources
docker stats

# Inspect Docker network
docker network inspect smart-hive-ai_smart-hive-net
```

---

**Status**: Ready for fresh deployment on Pi ✅
