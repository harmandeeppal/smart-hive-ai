# CORRECT Deployment Commands for Raspberry Pi

## ⚠️ Service Names in docker-compose.yml

The correct service names are:
- `edge-app` (NOT smart-hive-edge-app)
- `smart-hive-audio`
- `dashboard` (NOT smart-hive-dashboard)

---

## 🚀 CORRECT Rebuild Commands

Run these commands on your Raspberry Pi:

```bash
# Stop all services first
docker compose down

# Rebuild with correct service names (takes 15-20 minutes)
docker compose build --no-cache edge-app smart-hive-audio dashboard

# Start services
docker compose up -d

# Wait for startup
sleep 20

# Check edge-app (video/camera)
docker logs smart-hive-edge-app | grep "Camera"

# Check audio service
docker logs smart-hive-audio | grep -E "Audio model|microphone|packages"

# Test audio classification
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'
sleep 6
docker logs smart-hive-audio --tail 15
```

---

## 🔍 Current Issue: Audio Packages STILL Not Installed

Your logs show:
```
ERROR: ❌ Required packages not installed. Install with: pip install librosa scikit-learn sounddevice
```

This means the `build --no-cache` command **was NOT executed** because the service name was wrong!

### Fix Now:

```bash
# Navigate to project
cd ~/smart-hive-ai

# Make sure you have latest code
git pull origin feature/project-cleanup-and-ml-reorganization

# Stop audio service
docker compose stop smart-hive-audio

# Remove container AND image
docker compose rm -f smart-hive-audio
docker rmi smart-hive-audio:latest

# Clean Docker build cache
docker builder prune -f

# Rebuild audio service (THIS IS THE KEY STEP - takes 8-12 minutes)
docker compose build --no-cache smart-hive-audio

# You should see during build:
# Step X: Installing requirements-audio.txt
# Collecting librosa==0.10.0
# Collecting scikit-learn==1.3.0
# Collecting sounddevice==0.4.6
# Building wheels for librosa... (takes 5-8 minutes)
# Successfully installed librosa-0.10.0 scikit-learn-1.3.0 sounddevice-0.4.6

# Start audio service
docker compose up -d smart-hive-audio

# Wait 10 seconds
sleep 10

# Verify packages installed
docker logs smart-hive-audio 2>&1 | head -20
```

**Expected after rebuild:**
```
✅ Audio model loaded successfully  ← This line MUST appear!
Model expects 13 MFCC features
📱 Using microphone: Samson Meteorite Mic (device 1)
🎤 Audio service ready
```

---

## 🎥 For Video/Camera (edge-app)

```bash
# Rebuild edge-app with camera fix
docker compose build --no-cache edge-app

# Start edge-app
docker compose up -d edge-app

# Check camera initialization
docker logs smart-hive-edge-app | grep "Camera"
```

**Expected:**
```
✅ Camera initialized successfully (640x480)
```

---

## 🖥️ For Dashboard UI Updates

```bash
# Rebuild dashboard
docker compose build --no-cache dashboard

# Restart dashboard
docker compose up -d dashboard

# Open in browser
# http://192.168.88.16:5000
# Hard refresh: Ctrl+Shift+R
```

**Expected:**
- Title: "AI Vision and Live Video Feed"
- Blue toggle buttons (like other sensors)

---

## 📋 Quick All-in-One Script

Copy-paste this entire block:

```bash
cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization

# Stop all
docker compose down

# Clean old images
docker rmi edge-app:latest smart-hive-audio:latest dashboard:latest 2>/dev/null
docker builder prune -f

# Rebuild all three services (15-20 minutes total)
echo "🔨 Building edge-app (camera/video)..."
docker compose build --no-cache edge-app

echo "🔨 Building audio service (ML classification)..."
docker compose build --no-cache smart-hive-audio

echo "🔨 Building dashboard (UI)..."
docker compose build --no-cache dashboard

# Start everything
docker compose up -d

# Wait for services to start
sleep 20

# Verify
echo ""
echo "=== Edge-app (Camera) Status ==="
docker logs smart-hive-edge-app 2>&1 | grep -E "Camera|camera" | tail -5

echo ""
echo "=== Audio Service Status ==="
docker logs smart-hive-audio 2>&1 | grep -E "Audio model|microphone|packages" | tail -10

echo ""
echo "=== Testing Audio Classification ==="
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'
sleep 7
docker logs smart-hive-audio --tail 15

echo ""
echo "✅ Deployment complete!"
echo "🌐 Dashboard: http://192.168.88.16:5000"
echo "🔄 Hard refresh: Ctrl+Shift+R"
```

---

## ✅ Success Indicators

**Audio Service Working:**
```
✅ Audio model loaded successfully
📱 Using microphone: Samson Meteorite Mic (device 1)
⏺ Recording for 5 seconds...
✅ Recording complete (110250 samples)
✅ Classification: queen_present (confidence: 0.87)  ← NOT "unknown"!
```

**Camera Working:**
```
✅ Camera initialized successfully (640x480)
✅ Camera available: 640x480
```

**Dashboard:**
- Video feed showing OR helpful error message
- Blue toggle buttons
- Audio classification completing

---

## 🐛 If Still "unknown" After Rebuild

**This means Docker used cache despite --no-cache!**

Try this nuclear option:

```bash
# Stop everything
docker compose down

# Remove EVERYTHING
docker system prune -a --volumes -f

# WARNING: This removes ALL unused Docker images/containers/volumes
# Only do this if you're sure!

# Rebuild from completely clean state
docker compose build --no-cache smart-hive-audio
docker compose up -d

# Check
docker logs smart-hive-audio 2>&1 | grep "Audio model"
```

---

## 📝 Summary

**Problem 1:** Used wrong service name `smart-hive-edge-app` → should be `edge-app`  
**Problem 2:** Audio rebuild didn't happen → packages still missing → returns "unknown"  
**Solution:** Use correct service names and rebuild audio service properly

**CRITICAL:** The audio service build takes 8-12 minutes. Watch for "Installing librosa" during the build!
