# Dashboard MQTT Integration & Audio Recording - Fix Summary

**Date:** October 18, 2025  
**Commits:** 18f343c → 0a36156

---

## 🐛 **Issues Fixed**

### **1. Dashboard Not Receiving MQTT Updates** ✅
**Problem:** Dashboard showed "--" for all sensor values  
**Root Cause:** Vision service published to `hive/vision/results` but dashboard subscribed to different topic  

**Fix:**
- Updated `ml_vision_service.py` to use `config.TOPIC_VISION_RESULTS` 
- This ensures vision service publishes to the correct topic defined in config
- Dashboard now receives real-time vision detection updates

---

### **2. Missing Audio Recording Button** ✅
**Problem:** No way to trigger audio analysis from dashboard  
**Requirement:** 1-minute recording button with progress indicator

**Solution Implemented:**

#### **Frontend (Dashboard UI):**
- ✅ Added new "AI Audio Analysis" card to `dashboard/templates/index.html`
- ✅ Added "🎤 Record 1 Minute & Analyze" button
- ✅ Added recording progress bar (0-60 seconds countdown)
- ✅ Added classification results display (Queen/Queenless)
- ✅ Added confidence score display
- ✅ Added last analysis timestamp
- ✅ Added CSS styling in `dashboard/static/styles.css`

#### **Backend (Dashboard Server):**
- ✅ Added `trigger_audio_recording` socket.io handler in `dashboard_app.py`
- ✅ Publishes MQTT command to `hive/audio/control` topic
- ✅ Sends acknowledgment to client when recording starts
- ✅ Added `audio_ml_update` listener for results

#### **Audio Service:**
- ✅ Changed from continuous to on-demand recording mode
- ✅ Subscribes to `hive/audio/control` for recording triggers
- ✅ Publishes results to `config.TOPIC_AUDIO_RESULTS` (`hive/audio/classification`)
- ✅ Supports configurable recording duration (default 60 seconds)

#### **JavaScript (app.js):**
- ✅ Added socket.io listener for `audio_ml_update` events
- ✅ Added socket.io listener for `recording_started` events
- ✅ Added `updateAudioMLStatus()` function to display results
- ✅ Added `startRecordingProgress()` function for progress bar
- ✅ Added button click handler to trigger recording

---

## 📊 **New Data Flow**

### **Audio Recording Flow:**
```
User clicks "Record" button (Dashboard)
    ↓
Dashboard emits 'trigger_audio_recording' via Socket.IO
    ↓
Dashboard publishes to MQTT: hive/audio/control
    {
        "command": "record_and_classify",
        "duration_sec": 60
    }
    ↓
Audio Service receives command
    ↓
Audio Service records for 60 seconds
    ↓
Audio Service runs ML classification
    ↓
Audio Service publishes to MQTT: hive/audio/classification
    {
        "timestamp": "2025-10-18T...",
        "model_type": "audio_ml_classifier",
        "results": {
            "classification": "queen_present",
            "confidence": 0.85
        }
    }
    ↓
Dashboard receives via MQTT subscription
    ↓
Dashboard emits 'audio_ml_update' via Socket.IO
    ↓
UI updates with classification results
```

### **Telemetry Flow (Fixed):**
```
Edge-app publishes sensor data
    ↓
MQTT: hive/telemetry
    ↓
Dashboard subscribes and receives
    ↓
Dashboard emits 'telemetry_update' via Socket.IO
    ↓
JavaScript updates UI (temperature, humidity, etc.)
```

### **Vision Detection Flow (Fixed):**
```
Vision Service detects object
    ↓
MQTT: hive/vision/detection (config.TOPIC_VISION_RESULTS)
    ↓
Dashboard subscribes and receives
    ↓
Dashboard emits 'vision_update' via Socket.IO
    ↓
JavaScript updates AI status
```

---

## 🎨 **New Dashboard Features**

### **Audio ML Analysis Card:**
![Audio Card Layout]
```
┌─────────────────────────────────────┐
│  AI Audio Analysis                  │
├─────────────────────────────────────┤
│  Ready to record                    │
│                                     │
│  Classification: Queen Present      │
│  Confidence: 85.3%                  │
│                                     │
│  ┌───────────────────────────────┐ │
│  │  🎤 Record 1 Minute & Analyze │ │
│  └───────────────────────────────┘ │
│                                     │
│  [▓▓▓▓▓▓▓░░░░░░░░] 35s / 60s      │
│                                     │
│  Status: Recording...               │
│  Last Analysis: 14:35:22 NZDT      │
└─────────────────────────────────────┘
```

### **Recording States:**

**Idle State:**
- Button enabled: "🎤 Record 1 Minute & Analyze"
- Status: "Idle"
- Classification: "--"

**Recording State:**
- Button disabled (greyed out)
- Progress bar visible with countdown
- Status: "Recording..."
- Text: "Recording: 35s / 60s"

**Processing State:**
- Button disabled
- Progress bar at 100%
- Status: "Processing audio..."

**Complete State:**
- Button re-enabled
- Progress bar hidden
- Classification displayed (e.g., "Queen Present")
- Confidence displayed (e.g., "85.3%")
- Last analysis timestamp updated

---

## 🚀 **Deployment Steps**

### **On Your Laptop (Already Done):**
```bash
✅ Fixed vision MQTT topic
✅ Added audio recording UI
✅ Added backend handlers
✅ Updated audio service
✅ Committed and pushed to GitHub
```

### **On Raspberry Pi:**

#### **Step 1: Pull Latest Code (3 minutes)**
```bash
ssh pi@192.168.88.16
cd ~/smart-hive-ai

git pull origin feature/project-cleanup-and-ml-reorganization

# Verify latest commit
git log --oneline -1
# Should show: "0a36156 feat: Add dashboard MQTT integration and audio recording button"
```

#### **Step 2: Rebuild All Affected Containers (15 minutes)**
```bash
# Stop services
docker compose stop smart-hive-vision smart-hive-audio smart-hive-dashboard

# Remove old containers
docker rm smart-hive-vision smart-hive-audio smart-hive-dashboard

# Remove old images to force rebuild
docker rmi smart-hive-vision:latest smart-hive-audio:latest smart-hive-dashboard:latest

# Rebuild vision service (will download YOLOv8n model ~6MB)
docker compose build --no-cache smart-hive-vision

# Rebuild audio service (updated dependencies)
docker compose build --no-cache smart-hive-audio

# Rebuild dashboard (new UI and handlers)
docker compose build --no-cache smart-hive-dashboard

# Start all services
docker compose up -d
```

#### **Step 3: Verify Deployment (5 minutes)**
```bash
# Check all containers running
docker ps

# Should see all 5 containers "Up"

# Check vision service YOLO model
docker logs smart-hive-vision | grep "YOLO model loaded"
# Expected: "✅ YOLO model loaded successfully (pretrained YOLOv8n)"

# Check audio service ready
docker logs smart-hive-audio | grep "Audio service ready"
# Expected: "🎤 Audio service ready (on-demand recording mode)"

# Check dashboard running
docker logs smart-hive-dashboard | tail -10
# Should show Flask running on port 5000
```

#### **Step 4: Test Dashboard (5 minutes)**
```bash
# Test dashboard access
curl -I http://192.168.88.16:5000

# Should return: HTTP/1.1 200 OK
```

**Open browser:** http://192.168.88.16:5000

**Expected to see:**
- ✅ Temperature/Humidity values updating (if edge-app publishing)
- ✅ Video feed showing camera stream
- ✅ NEW: "AI Audio Analysis" card with record button
- ✅ All sensor values updating in real-time

#### **Step 5: Test Audio Recording**
1. Click "🎤 Record 1 Minute & Analyze" button
2. Progress bar should appear with countdown (0-60s)
3. Button should be disabled during recording
4. After 60 seconds, should see "Processing audio..."
5. Results should appear:
   - Classification: "Queen Present" or "Queenless Colony"
   - Confidence: X.X%
   - Last Analysis: timestamp

**Check logs:**
```bash
# Watch audio service logs
docker logs -f smart-hive-audio

# Expected output:
# 📨 Control message: hive/audio/control = {"command": "record_and_classify", ...}
# 🎤 Recording requested: 60 seconds
# 🎙️  Starting 60s recording...
# ✅ Audio results published: queen_present
```

---

## 🔧 **Configuration Reference**

### **MQTT Topics Used:**

| Topic | Publisher | Subscriber | Purpose |
|-------|-----------|------------|---------|
| `hive/telemetry` | Edge-app | Dashboard | Sensor data |
| `hive/telemetry/camera/frame` | Edge-app | Vision Service | JPEG frames |
| `hive/vision/detection` | Vision Service | Dashboard | Detection results |
| `hive/audio/classification` | Audio Service | Dashboard | Audio analysis |
| `hive/audio/control` | Dashboard | Audio Service | Recording trigger |
| `hive/control` | Dashboard | Edge-app | Sensor toggle |

### **Config Values:**
```python
# From config.py
TOPIC_VISION_RESULTS = "hive/vision/detection"
TOPIC_AUDIO_RESULTS = "hive/audio/classification"
AUDIO_RECORD_DURATION_SEC = 30  # Can be overridden by dashboard
```

---

## ✅ **Success Criteria**

System is fully operational when:

1. ✅ Dashboard loads at http://192.168.88.16:5000
2. ✅ Sensor values update in real-time (temperature, humidity, etc.)
3. ✅ Video feed shows camera stream
4. ✅ Audio recording button is visible and clickable
5. ✅ Clicking record button triggers 60-second countdown
6. ✅ After recording, classification results appear
7. ✅ Vision detections show in AI status (if objects visible)

---

## 🐛 **Troubleshooting**

### **Dashboard shows "--" for sensors:**
```bash
# Check edge-app is publishing
docker logs smart-hive-edge | grep "Published Telemetry"

# Check mosquitto broker
docker logs mosquitto | tail -20

# Check dashboard MQTT connection
docker logs smart-hive-dashboard | grep "MQTT"
```

### **Audio recording button not working:**
```bash
# Check browser console (F12)
# Look for JavaScript errors

# Check dashboard logs
docker logs smart-hive-dashboard | grep "Audio recording trigger"

# Check audio service logs
docker logs smart-hive-audio | grep "Control message"
```

### **No audio results after recording:**
```bash
# Check if audio processor is initialized
docker logs smart-hive-audio | grep "AudioProcessor"

# Check for missing dependencies
docker logs smart-hive-audio | grep -i error

# May show: "No module named 'librosa'" - rebuild with updated requirements
```

### **Vision detections not showing:**
```bash
# Check vision service MQTT topic
docker logs smart-hive-vision | grep "Detection published"

# Check dashboard subscription
docker logs smart-hive-dashboard | grep "Subscribed to.*vision"
```

---

## 📝 **Files Modified**

| File | Changes |
|------|---------|
| `ml_vision_service.py` | Use config.TOPIC_VISION_RESULTS instead of hardcoded topic |
| `ml_audio_service.py` | On-demand recording mode, subscribe to control topic |
| `dashboard/dashboard_app.py` | Add audio recording trigger handler |
| `dashboard/templates/index.html` | Add audio ML analysis card |
| `dashboard/static/app.js` | Add audio recording logic and result display |
| `dashboard/static/styles.css` | Add audio card styling |

---

## 🎯 **Next Steps**

After successful deployment:

1. **Test end-to-end flow:**
   - Trigger audio recording
   - Verify results appear in dashboard
   - Check MQTT message flow

2. **If audio ML fails:**
   - Check if `models/audio_model.pkl` exists
   - Verify librosa and dependencies installed
   - May need to train/regenerate audio model

3. **Production improvements:**
   - Train queen-specific YOLO model (current is generic YOLOv8n)
   - Validate audio model accuracy
   - Add recording duration selector (30s, 60s, 120s options)
   - Add audio waveform visualization

4. **Merge to main branch:**
   ```bash
   git checkout main
   git merge feature/project-cleanup-and-ml-reorganization
   git push origin main
   ```

---

**Status:** Ready for deployment ✅  
**Estimated deployment time:** 25-30 minutes  
**Risk level:** Low (backward compatible, graceful degradation if audio model missing)
