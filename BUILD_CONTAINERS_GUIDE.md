# 🚀 Smart Hive AI - Complete Container Build Guide for Raspberry Pi

## 📋 Overview

This guide walks you through building all Docker containers from scratch on your Raspberry Pi.

**Services to Build:**
- ✅ `mosquitto` - MQTT broker (official image, no build needed)
- ✅ `edge-app` - Sensor collection & video streaming
- ✅ `smart-hive-vision` - YOLO vision inference
- ✅ `smart-hive-audio` - Audio classification
- ✅ `dashboard` - Web interface

---

## 🔧 Prerequisites

### 1. Ensure Docker is Installed

```bash
docker --version
docker-compose --version

# If not installed:
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo reboot
```

### 2. Verify Required Files Exist

```bash
cd ~/smart-hive-ai

# Check Dockerfiles exist
ls -la Dockerfile.*

# Expected output:
# Dockerfile.audio
# Dockerfile.dashboard
# Dockerfile.edge
# Dockerfile.vision

# Check requirements files
ls -la requirements-*.txt

# Expected output:
# requirements-audio.txt
# requirements-dashboard.txt
# requirements-edge.txt
# requirements-vision.txt

# Check .env file exists
ls -la .env

# Check certificates exist
ls -la certs/
```

---

## 🧹 Step 1: Clean Slate (Remove Old Builds)

```bash
cd ~/smart-hive-ai

# Stop all running containers
docker-compose down

# Remove old images (if any exist)
docker rmi smart-hive-edge:latest 2>/dev/null
docker rmi smart-hive-vision:latest 2>/dev/null
docker rmi smart-hive-audio:latest 2>/dev/null
docker rmi smart-hive-dashboard:latest 2>/dev/null

# Clean build cache
docker builder prune -af

# Verify cleanup
docker images | grep smart-hive
# (Should show nothing)
```

---

## 🏗️ Step 2: Build Containers (Sequential Approach)

Build one at a time to catch errors early. Each build will take 5-20 minutes on Raspberry Pi.

### Build 1: Dashboard (Fastest, ~3-5 minutes)

```bash
cd ~/smart-hive-ai

echo "🔨 Building Dashboard..."
docker-compose build --no-cache dashboard

# Verify
docker images | grep dashboard
```

**Expected Output:**
```
smart-hive-dashboard    latest    abc123    2 minutes ago    450MB
```

**What to Look For:**
- ✅ `Successfully installed Flask Flask-SocketIO paho-mqtt`
- ✅ `naming to docker.io/library/smart-hive-dashboard:latest`

---

### Build 2: Edge App (~10-15 minutes)

```bash
echo "🔨 Building Edge App..."
docker-compose build --no-cache edge-app

# Verify
docker images | grep edge
```

**Expected Output:**
```
smart-hive-edge    latest    def456    12 minutes ago    1.2GB
```

**What to Look For:**
- ✅ `Successfully installed opencv-python paho-mqtt boto3 adafruit-circuitpython-bme280`
- ✅ `Successfully installed tflite-runtime`
- ⚠️ If you see "Could not find tflite-runtime", that's OK (it gets installed from Google Coral repo)

---

### Build 3: Vision Service (~15-20 minutes)

```bash
echo "🔨 Building Vision Service (YOLO)..."
docker-compose build --no-cache smart-hive-vision

# Verify
docker images | grep vision
```

**Expected Output:**
```
smart-hive-vision    latest    ghi789    18 minutes ago    1.5GB
```

**What to Look For:**
- ✅ `Successfully installed ultralytics opencv-python-headless numpy`
- ✅ `Building wheel for opencv-python-headless` (takes 5-10 minutes)

**Common Issue:**
If build fails with "numpy version conflict":
```bash
# Edit requirements-vision.txt
nano requirements-vision.txt

# Change:
numpy==1.24.3  # to
numpy>=1.24.0,<2.0
```

---

### Build 4: Audio Service (~10-15 minutes)

```bash
echo "🔨 Building Audio Service..."
docker-compose build --no-cache smart-hive-audio

# Verify
docker images | grep audio
```

**Expected Output:**
```
smart-hive-audio    latest    jkl012    13 minutes ago    1.3GB
```

**What to Look For:**
- ✅ `Successfully installed librosa scikit-learn sounddevice scipy`
- ✅ `Building wheel for librosa` (takes 5-8 minutes)

**⚠️ This is the most critical build!** Audio classification was failing because these packages were missing.

---

## 🚀 Step 3: Start All Services

```bash
cd ~/smart-hive-ai

# Start everything in detached mode
docker-compose up -d

# Wait for services to initialize
sleep 20

# Check all services are running
docker-compose ps
```

**Expected Output:**
```
NAME                    STATUS          PORTS
mosquitto               Up              1883/tcp, 8883/tcp
smart-hive-edge         Up              5001/tcp
smart-hive-vision       Up              
smart-hive-audio        Up              
smart-hive-dashboard    Up              0.0.0.0:5000->5000/tcp
```

---

## ✅ Step 4: Verify Each Service

### Check Edge App
```bash
docker logs smart-hive-edge --tail 50

# Look for:
# ✅ "Camera initialized successfully (640x480)"
# ✅ "Connected to AWS IoT Core"
# ✅ "BME280 sensor initialized"
# ✅ "Starting telemetry loop..."
```

### Check Vision Service
```bash
docker logs smart-hive-vision --tail 50

# Look for:
# ✅ "VisionProcessor imported successfully"
# ✅ "YOLO model loaded: models/vision_model.pt"
# ✅ "Subscribed to hive/telemetry/camera/frame"
# ✅ "Vision Inference Service running..."
```

### Check Audio Service (Most Important!)
```bash
docker logs smart-hive-audio --tail 50

# Look for:
# ✅ "AudioProcessor imported successfully"
# ✅ "librosa version: 0.10.0"
# ✅ "Subscribed to hive/control/audio/record"
# ✅ "Audio Inference Service running..."
```

**If you see:**
- ❌ `ModuleNotFoundError: No module named 'librosa'` → Build failed, rebuild with `--no-cache`
- ❌ `AudioProcessor import failed` → Check logs: `docker logs smart-hive-audio`

### Check Dashboard
```bash
docker logs smart-hive-dashboard --tail 50

# Look for:
# ✅ "Dashboard server started on port 5000"
# ✅ "Connected to MQTT broker: mosquitto"
```

---

## 🧪 Step 5: Test Audio Classification

**Trigger an audio recording:**
```bash
# Via MQTT (from another terminal)
docker exec -it mosquitto mosquitto_pub \
  -h localhost \
  -t "hive/control/audio/record" \
  -m '{"duration": 10}'

# Or via Dashboard UI:
# Go to http://192.168.88.16:5000
# Click "Record Audio" button
```

**Check result:**
```bash
docker logs smart-hive-audio --tail 20

# Expected (SUCCESS):
# ✅ "Audio recording started (10 seconds)..."
# ✅ "Audio features extracted: 13 MFCCs"
# ✅ "Classification result: queen_present (confidence: 0.87)"

# Not Expected (FAILURE - means packages missing):
# ❌ "Classification result: unknown"
# ❌ "Error extracting features"
```

---

## 🎯 Quick Build All-in-One Command

If you're confident and want to build everything at once:

```bash
cd ~/smart-hive-ai

# Clean everything
docker-compose down
docker builder prune -af

# Build all services (takes 40-55 minutes total)
docker-compose build --no-cache

# Start everything
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## 🔧 Troubleshooting

### Issue: "Build failed: No space left on device"

```bash
# Clean up old images and containers
docker system prune -a --volumes -f

# Check disk space
df -h
```

### Issue: "Cannot connect to MQTT broker"

```bash
# Restart mosquitto
docker-compose restart mosquitto

# Check it's running
docker logs mosquitto
```

### Issue: "Audio still returns 'unknown'"

```bash
# Verify librosa is installed in container
docker exec -it smart-hive-audio python -c "import librosa; print(librosa.__version__)"

# Expected: 0.10.0
# If error: Rebuild with --no-cache
docker-compose build --no-cache smart-hive-audio
docker-compose up -d smart-hive-audio
```

### Issue: "Camera not found"

```bash
# Check camera device exists
ls -la /dev/video*

# Check edge-app has access
docker exec -it smart-hive-edge ls -la /dev/video0
```

---

## 📊 Build Time Summary

On Raspberry Pi 4 (4GB RAM):
- Dashboard: 3-5 minutes
- Edge App: 10-15 minutes
- Vision Service: 15-20 minutes (YOLO + OpenCV compilation)
- Audio Service: 10-15 minutes (librosa compilation)
- **Total: 40-55 minutes**

---

## ✅ Success Checklist

- [ ] All 5 services show "Up" in `docker-compose ps`
- [ ] Edge app logs show "Camera initialized successfully"
- [ ] Vision service logs show "YOLO model loaded"
- [ ] Audio service logs show "AudioProcessor imported successfully"
- [ ] Dashboard accessible at http://[pi-ip]:5000
- [ ] Audio classification returns valid results (not "unknown")
- [ ] Video stream shows on dashboard
- [ ] MQTT messages flowing (check dashboard real-time updates)

---

## 🎉 Next Steps

Once all containers are built and running:

1. **Test Video Feed:** http://192.168.88.16:5000
2. **Test Audio Recording:** Click "Record Audio" button
3. **Verify AWS Integration:** Check DynamoDB for new telemetry entries
4. **Monitor Logs:** `docker-compose logs -f`

---

## 📝 Important Notes

- **Always use `--no-cache`** when rebuilding to ensure dependencies install fresh
- **Audio service** was the main issue - verify `librosa`, `scikit-learn`, and `sounddevice` install successfully
- **Vision service** takes longest due to YOLO/OpenCV compilation
- **Edge app** needs hardware access (camera, I2C, audio devices)
- **Don't skip verification steps** - catch issues early!

---

## 🆘 Need Help?

If any build fails:

1. **Save the error log:**
   ```bash
   docker-compose build --no-cache [service-name] 2>&1 | tee build-error.log
   ```

2. **Check specific service logs:**
   ```bash
   docker logs [service-name] > service-error.log
   ```

3. **Verify requirements file:**
   ```bash
   cat requirements-[service].txt
   ```

Good luck with your deployment! 🐝
