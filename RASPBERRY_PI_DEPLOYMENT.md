# 🚀 Raspberry Pi Deployment Guide

## Current Status
✅ All code merged to `main` branch  
✅ Repository cleaned up and organized  
⚠️ Services on Pi are running OLD code (before fixes)

---

## 📋 What Needs to be Fixed on Pi

1. **Audio Classification** - Returns "unknown" (missing packages: librosa, scikit-learn, sounddevice)
2. **Camera/Video Feed** - Not showing (circular dependency issue)
3. **Dashboard UI** - Old interface (missing toggle improvements)
4. **Microphone Detection** - Not auto-detecting Samson Meteorite Mic

---

## 🔧 Step-by-Step Deployment on Raspberry Pi

### Step 1: Pull Latest Code from Main Branch

```bash
# SSH into your Raspberry Pi
ssh pi@192.168.88.16

# Navigate to project directory
cd ~/smart-hive-ai

# Check current branch
git branch

# Switch to main if not already
git checkout main

# Pull latest changes
git pull origin main

# Verify you got the latest code
git log --oneline -5
```

**Expected output:**
```
11f212c docs: Clean up obsolete markdown files and config
888e8bf fix: Camera initialization, microphone device selection, and UI improvements
9313f3f fix: Camera initialization, microphone device selection, and UI improvements
fad0d42 feat: Add independent video and AI vision toggle controls
...
```

---

### Step 2: Stop All Services

```bash
cd ~/smart-hive-ai
docker compose down
```

---

### Step 3: Clean Docker Cache (Important!)

```bash
# Remove old images to force rebuild
docker rmi edge-app:latest 2>/dev/null
docker rmi smart-hive-audio:latest 2>/dev/null
docker rmi dashboard:latest 2>/dev/null

# Clean build cache
docker builder prune -f
```

---

### Step 4: Rebuild Services with Fixes

**⚠️ CRITICAL: Use correct service names!**

Service names in docker-compose.yml:
- `edge-app` (NOT smart-hive-edge-app)
- `smart-hive-audio` 
- `dashboard`

```bash
cd ~/smart-hive-ai

# Rebuild all three services (takes 15-20 minutes)
echo "🔨 Building edge-app (camera/video fixes)..."
docker compose build --no-cache edge-app

echo "🔨 Building audio service (ML packages)..."
docker compose build --no-cache smart-hive-audio

echo "🔨 Building dashboard (UI improvements)..."
docker compose build --no-cache dashboard
```

**During audio service build, you MUST see:**
```
Step X/Y : RUN pip install -r requirements-audio.txt
Collecting librosa==0.10.0
Collecting scikit-learn==1.3.0
Collecting sounddevice==0.4.6
Building wheels for librosa... (takes 5-8 minutes on Pi)
Successfully installed librosa-0.10.0 scikit-learn-1.3.0 sounddevice-0.4.6
```

**If you DON'T see this, the build is using cache! Stop and run Step 3 again.**

---

### Step 5: Start All Services

```bash
docker compose up -d

# Wait for services to initialize
sleep 20

# Check all services are running
docker compose ps
```

**Expected output:**
```
NAME                    STATUS          PORTS
mosquitto               Up             1883/tcp, 9001/tcp
smart-hive-edge-app     Up             
smart-hive-audio        Up             
smart-hive-vision       Up             
smart-hive-dashboard    Up             0.0.0.0:5000->5000/tcp
```

---

### Step 6: Verify Camera Fix

```bash
docker logs smart-hive-edge-app 2>&1 | grep -i camera | tail -10
```

**Expected (SUCCESS):**
```
✅ Camera initialized successfully (640x480)
✅ Camera available: True
```

**If you see errors:**
```
❌ Camera initialization failed
```
Then check:
```bash
# Verify USB camera is connected
ls -la /dev/video*

# Should show: /dev/video0
```

---

### Step 7: Verify Audio Service & Packages

```bash
docker logs smart-hive-audio 2>&1 | head -30
```

**Expected (SUCCESS):**
```
INFO: ✅ AudioProcessor imported successfully
INFO: Loading audio model from models/audio_model.pkl
INFO: ✅ Audio model loaded successfully  ← THIS IS THE KEY LINE!
INFO: Model expects 13 MFCC features
INFO: 📱 Using microphone: Samson Meteorite Mic (device 1)  ← NEW!
INFO: ✅ Audio processor initialized
INFO: 🎤 Audio service ready (on-demand recording mode)
```

**If you still see ERROR about missing packages:**
```
ERROR: ❌ Required packages not installed
```
Then the rebuild didn't work. Go back to Step 3 and try again.

---

### Step 8: Test Audio Classification

```bash
# Trigger a recording
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'

# Wait for recording to complete
sleep 7

# Check results
docker logs smart-hive-audio --tail 20
```

**Expected (SUCCESS):**
```
INFO: 📨 Control message: hive/audio/control = {"command":"record_and_classify","duration_sec":5}
INFO: 🎤 Recording requested: 5 seconds
INFO: 📱 Using microphone: Samson Meteorite Mic (device 1)
INFO: 🎙️ Starting 5s recording...
INFO: ⏺ Recording for 5 seconds...
INFO: ✅ Recording complete (110250 samples)
INFO: 🔊 Audio stats: mean=0.0012, max=0.1543, min=-0.1621
INFO: 📊 Extracting MFCC features...
INFO: ✅ Audio features extracted: shape=(431, 13)
INFO: 🤖 Running classification...
INFO: ✅ Classification: queen_present (confidence: 0.87)  ← NOT "unknown"!
INFO: ✅ Audio results published to: hive/audio/results
```

**If still returns "unknown":**
- Packages not installed (check Step 7)
- Or model file corrupted
- Or no sound detected (check microphone)

---

### Step 9: Test Dashboard & UI

```bash
# Open in browser on your computer
# http://192.168.88.16:5000

# Hard refresh to clear cache
# Windows: Ctrl+Shift+R
# Mac: Cmd+Shift+R
```

**Expected UI Changes:**
- ✅ Card title: "AI Vision and Live Video Feed" (not "Live Video Feed")
- ✅ Two separate toggle buttons: "📹 Video: ON" and "🤖 AI Vision: OFF"
- ✅ Buttons are BLUE when ON (matching temperature/humidity sensors)
- ✅ Buttons are GREY when OFF
- ✅ Video feed showing (or helpful error message if camera issue)

**Test the toggles:**
1. Click "📹 Video: OFF" → Video feed should go dark/greyscale
2. Click "📹 Video: ON" → Video feed should restore
3. Click "🤖 AI Vision: ON" → Should see YOLO bounding boxes on video
4. Click "🤖 AI Vision: OFF" → Raw video without annotations

**Test audio recording:**
1. Click "🎙️ Record Audio (5s)" button
2. Should see waveform visualization during recording
3. After 5 seconds, should show classification result (not "unknown")
4. Result should be "Queen Bee Present" or "Queen Bee Absent"

---

## ✅ Success Checklist

Run through this checklist after deployment:

```bash
# 1. Camera working
docker logs smart-hive-edge-app | grep "Camera initialized successfully"

# 2. Audio packages installed
docker logs smart-hive-audio | grep "Audio model loaded successfully"

# 3. Microphone detected
docker logs smart-hive-audio | grep "Using microphone: Samson"

# 4. Test audio classification
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'
sleep 7
docker logs smart-hive-audio --tail 5 | grep "Classification:"

# 5. Check dashboard accessible
curl -s http://localhost:5000 | grep "AI Vision and Live Video Feed"
```

**All checks should return results (not empty).**

---

## 🐛 Troubleshooting

### Problem: Audio still returns "unknown"

**Solution 1: Nuclear rebuild**
```bash
docker compose down
docker rmi smart-hive-audio:latest
docker system prune -a -f
docker compose build --no-cache smart-hive-audio
docker compose up -d smart-hive-audio
```

**Solution 2: Check model file**
```bash
ls -lh models/audio_model.pkl
# Should be ~16MB

# If missing, you need to train the model
```

### Problem: Camera not showing

**Check 1: Hardware connected**
```bash
ls -la /dev/video*
v4l2-ctl --list-devices
```

**Check 2: Permissions**
```bash
# Add pi user to video group
sudo usermod -a -G video pi

# Restart docker
docker compose restart edge-app
```

**Check 3: Camera in use**
```bash
# Check if another process is using camera
sudo lsof /dev/video0
```

### Problem: Dashboard shows old UI

**Solution: Clear browser cache**
1. Hard refresh: Ctrl+Shift+R
2. Clear cache in browser settings
3. Try incognito/private window
4. Check dashboard container logs:
```bash
docker logs smart-hive-dashboard | grep "static"
```

### Problem: Microphone not detected

**Check available devices:**
```bash
docker exec smart-hive-audio python3 -c "
import sounddevice as sd
devices = sd.query_devices()
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        print(f'Device {i}: {d[\"name\"]} (inputs: {d[\"max_input_channels\"]})')
"
```

**Expected output:**
```
Device 0: bcm2835 Headphones (inputs: 0)
Device 1: Samson Meteorite Mic (inputs: 1)  ← Your mic
Device 2: C270 HD WEBCAM (inputs: 1)        ← Webcam mic
```

---

## 📊 Monitoring Commands

**View all logs:**
```bash
docker compose logs -f
```

**View specific service:**
```bash
docker logs -f smart-hive-audio
docker logs -f smart-hive-edge-app
docker logs -f smart-hive-dashboard
```

**Check service health:**
```bash
docker compose ps
docker stats --no-stream
```

**Monitor MQTT messages:**
```bash
# Subscribe to all topics
docker exec mosquitto mosquitto_sub -v -t '#'

# Subscribe to specific topics
docker exec mosquitto mosquitto_sub -v -t 'hive/audio/results'
docker exec mosquitto mosquitto_sub -v -t 'hive/vision/results'
docker exec mosquitto mosquitto_sub -v -t 'hive/status/#'
```

---

## 🎯 Quick Reference

**Service Names (docker-compose.yml):**
- `edge-app` → Container: `smart-hive-edge-app`
- `smart-hive-audio` → Container: `smart-hive-audio`
- `dashboard` → Container: `smart-hive-dashboard`

**Important Files:**
- Audio model: `models/audio_model.pkl` (16MB)
- Vision model: `yolov8n.pt` (6.2MB)
- Config: `config.py`
- Requirements: `requirements-audio.txt`, `requirements-edge.txt`, `requirements-dashboard.txt`

**MQTT Topics:**
- Control: `hive/audio/control`, `hive/control/video`, `hive/control/ai_vision`
- Results: `hive/audio/results`, `hive/vision/results`
- Status: `hive/status/video`, `hive/status/ai_vision`

---

## 📝 Summary

1. **Pull latest code** from main branch
2. **Clean Docker cache** to force rebuild
3. **Rebuild services** with `--no-cache` flag
4. **Verify logs** for success messages
5. **Test functionality** (audio, camera, dashboard)
6. **Monitor** system with docker logs

**Expected Results:**
- ✅ Audio classification returns "queen_present" or "queen_absent" (NOT "unknown")
- ✅ Camera shows live video feed
- ✅ Dashboard has blue toggle buttons and correct title
- ✅ Microphone auto-detected (Samson Meteorite Mic)
- ✅ All features working as expected

Good luck! 🚀🐝
