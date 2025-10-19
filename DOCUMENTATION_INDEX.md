# Smart Hive AI - Documentation Index
**Last Updated:** October 20, 2025

---

## 📚 **Current System Overview**

Smart Hive AI is a Raspberry Pi-based beehive monitoring system with:
- ✅ **Sensors:** Temperature, Humidity, Vibration, Sound (Audio ML)
- ✅ **Camera:** Live video streaming (no AI detection)
- ✅ **Dashboard:** Real-time web interface
- ✅ **Cloud:** AWS IoT Core + DynamoDB for data storage
- ❌ **S3:** Not used (disabled)
- ❌ **Vision ML:** Not used (camera for streaming only)

---

## 🚀 **Quick Start (For New Users)**

### 1. Hardware Requirements
- Raspberry Pi 4 (4GB+ RAM recommended)
- BME280 sensor (Temperature/Humidity)
- LIS3DH sensor (Vibration)
- INMP441 microphone (Sound/Audio ML)
- USB camera (any USB webcam)
- SD card (32GB+)

### 2. Software Setup
```bash
# Clone repository
git clone https://github.com/harmandeeppal/smart-hive-ai.git
cd smart-hive-ai

# Setup (use appropriate branch)
git checkout feature/usb-camera-fix  # Latest stable

# See BUILD_CONTAINERS_GUIDE.md for detailed setup
```

### 3. Essential Documentation

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **BUILD_CONTAINERS_GUIDE.md** | Initial setup & deployment | First time setup |
| **QUICK_START.md** | Quick commands & monitoring | Daily operations |
| **AUDIO_PROCESS_DETAILED_EXPLANATION.md** | How audio ML works | Understanding audio system |
| **AUDIO_TROUBLESHOOTING.md** | Fix audio issues | When audio ML fails |
| **USB_CAMERA_TROUBLESHOOTING.md** | Fix camera issues | When video feed broken |
| **CRITICAL_FIX_BROKEN_IMAGE.md** | Dashboard video fix | Broken image in dashboard |

---

## 📋 **System Architecture**

### **Container Stack:**
```
┌─────────────────┐
│   Dashboard     │  Port 5000 - Web UI
│  (Flask + JS)   │
└────────┬────────┘
         │
    ┌────┴────────────────┬────────────┐
    │                     │            │
┌───▼──────┐   ┌─────────▼──┐   ┌────▼─────┐
│ Edge App │   │ Audio ML   │   │ MQTT     │
│ (Sensors)│   │ (Service)  │   │ Broker   │
│  Camera  │   │            │   │          │
└──────────┘   └────────────┘   └──────────┘
```

### **Active Containers:**
1. **mosquitto** - MQTT message broker
2. **smart-hive-edge** - Main app (sensors + camera)
3. **smart-hive-audio** - Audio ML inference service
4. **smart-hive-dashboard** - Web dashboard

### **Disabled/Removed:**
- ~~smart-hive-vision~~ - Vision ML not used
- ~~S3 uploads~~ - Not implemented

---

## 🔧 **Configuration Files**

### **Essential:**
- `config.py` - Main configuration (sensor settings, ML thresholds)
- `.env` - AWS credentials, environment settings
- `docker-compose.yml` - Container orchestration

### **Key Settings:**

**Audio ML:**
```python
AUDIO_CONFIDENCE_THRESHOLD = 0.6  # 60% confidence for queen detection
AUDIO_WINDOW_SECONDS = 1.0        # Analysis window
AUDIO_HOP_SECONDS = 0.5           # Overlap
```

**Camera:**
```python
CAMERA_TYPE = "USB"          # USB camera
CAMERA_DEVICE_INDEX = 0      # First camera
CAMERA_WIDTH = 640           # Resolution
CAMERA_HEIGHT = 480
VIDEO_STREAM_FPS = 20        # Frame rate
```

**Sensors:**
```python
TELEMETRY_PUBLISH_INTERVAL = 60  # Publish every 60 seconds
```

---

## 🎯 **Common Tasks**

### **Deploy/Update System:**
```bash
cd ~/smart-hive-ai
git pull origin feature/usb-camera-fix
docker-compose build --no-cache
docker-compose up -d
```

### **Monitor System:**
```bash
# Check all containers
docker ps

# View logs
docker logs -f smart-hive-edge
docker logs -f smart-hive-audio
docker logs -f smart-hive-dashboard

# Monitor telemetry
mosquitto_sub -h localhost -t 'hive/#' -v
```

### **Access Dashboard:**
```
http://192.168.88.16:5000
```
Replace IP with your Raspberry Pi's IP address.

---

## 🐛 **Troubleshooting**

### **Audio ML Not Working:**
→ Read: `AUDIO_TROUBLESHOOTING.md`

Common fixes:
```bash
# Check microphone
arecord -l

# Restart audio service
docker-compose restart smart-hive-audio

# Check logs
docker logs smart-hive-audio | grep -i "queen\|confidence\|classification"
```

### **Camera Not Working:**
→ Read: `USB_CAMERA_TROUBLESHOOTING.md` and `CRITICAL_FIX_BROKEN_IMAGE.md`

Common fixes:
```bash
# Check camera device
ls -l /dev/video0

# Restart edge-app
docker-compose restart edge-app

# Test video feed
curl -I http://localhost:5001/video_feed
```

### **Dashboard Not Updating:**
```bash
# Rebuild dashboard (files copied into container)
docker-compose build --no-cache dashboard
docker-compose up -d dashboard

# Hard refresh browser
Ctrl + Shift + R
```

---

## 📊 **Data Flow**

### **Sensor Data:**
```
Sensors → edge-app → MQTT → Dashboard (real-time)
                  ↓
               DynamoDB (storage)
```

### **Audio ML:**
```
Microphone → Audio Service → ML Model → Classification → MQTT → Dashboard
```

### **Video Stream:**
```
USB Camera → edge-app:5001/video_feed → Dashboard proxy → Browser
```

---

## ⚙️ **Features Status**

| Feature | Status | Notes |
|---------|--------|-------|
| Temperature monitoring | ✅ Working | BME280 sensor |
| Humidity monitoring | ✅ Working | BME280 sensor |
| Vibration monitoring | ✅ Working | LIS3DH sensor |
| Sound level monitoring | ✅ Working | INMP441 microphone |
| **Audio ML (Queen Detection)** | ✅ **Working** | Random Forest classifier |
| Live video streaming | ✅ Working | USB camera |
| Dashboard controls | ✅ Working | Toggle sensors ON/OFF |
| AWS IoT Core | ✅ Working | MQTT telemetry |
| DynamoDB storage | ✅ Working | Historical data |
| ~~Vision ML~~ | ❌ Disabled | Not used |
| ~~S3 Uploads~~ | ❌ Disabled | Not implemented |

---

## 📖 **Detailed Documentation**

### **Setup & Deployment:**
- `BUILD_CONTAINERS_GUIDE.md` - Complete deployment guide
- `QUICK_START.md` - Quick reference commands

### **Audio ML System:**
- `AUDIO_PROCESS_DETAILED_EXPLANATION.md` - How it works (800+ lines)
- `AUDIO_TROUBLESHOOTING.md` - Common issues & fixes
- `AUDIO_CONFIDENCE_THRESHOLD_GUIDE.md` - Tuning guide
- `AUDIO_DASHBOARD_ENHANCEMENTS.md` - Dashboard features

### **Camera System:**
- `USB_CAMERA_TROUBLESHOOTING.md` - Comprehensive guide
- `CAMERA_DEBUGGING_COMMANDS.md` - Diagnostic commands
- `CRITICAL_FIX_BROKEN_IMAGE.md` - Dashboard video fix
- `CAMERA_DEPLOYMENT_UPDATE.md` - Recent fixes

### **Advanced:**
- `docs/CONFIGURATION_GUIDE.md` - Detailed config options
- `docs/DEPLOYMENT.md` - Production deployment
- `docs/TROUBLESHOOTING.md` - General troubleshooting

---

## 🔄 **Update History**

### **October 2025 - Current Stable**
- ✅ Audio ML fully operational (Random Forest classifier)
- ✅ USB camera working with robust initialization
- ✅ Dashboard enhancements (waveforms, confidence warnings)
- ✅ Container hostname fixes
- ❌ Removed Vision ML (not needed)
- ❌ Removed S3 uploads (not used)

### **Key Improvements:**
1. Audio sample rate auto-detection (44100Hz → 22050Hz resampling)
2. Feature extraction fix (13 MFCC × 8 stats = 312 features)
3. Pipeline order correction (scale → select)
4. Camera multi-backend initialization (V4L2, auto-detect)
5. Dashboard video proxy hostname fix (edge-app → smart-hive-edge)

---

## 📞 **Support**

### **For Issues:**
1. Check relevant troubleshooting guide (see table above)
2. Check container logs: `docker logs <container-name>`
3. Run diagnostic scripts (in camera/audio docs)
4. Check MQTT messages: `mosquitto_sub -h localhost -t 'hive/#' -v`

### **For Updates:**
```bash
git pull origin feature/usb-camera-fix
docker-compose build --no-cache
docker-compose up -d
```

---

## 🗂️ **File Structure**

```
smart-hive-ai/
├── README.md                    # This file
├── DOCUMENTATION_INDEX.md       # This file (alias)
├── config.py                    # Main configuration
├── app.py                       # Edge application
├── ml_audio_service.py          # Audio ML service
├── dashboard/                   # Web dashboard
├── ml_audio_model/              # Audio processor
├── models/                      # ML models
├── docs/                        # Additional documentation
└── *.md                        # Specific guides (see table above)
```

---

## ✅ **Quick Health Check**

```bash
# 1. All containers running?
docker ps | grep smart-hive

# 2. Audio ML working?
docker logs smart-hive-audio | tail -20

# 3. Camera working?
curl -I http://localhost:5001/video_feed

# 4. Dashboard accessible?
curl -I http://localhost:5000

# 5. MQTT messages flowing?
timeout 10 mosquitto_sub -h localhost -t 'hive/#' -v
```

All should return success! ✅

---

**Remember:** Always rebuild containers after code changes, and hard refresh browser after dashboard changes!
