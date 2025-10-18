# 🎤 Audio ML Service - Complete Fix & Deployment Guide

**Date**: October 19, 2025  
**Goal**: Enable audio recording → ML classification → dashboard display

---

## 📊 Current Status

### ✅ What's Already Fixed (Code Level)
- [x] Audio service MQTT connection (local mosquitto, no TLS)
- [x] Dashboard audio recording button (triggers 60-second recording)
- [x] Dashboard MQTT subscription to `hive/audio/classification`
- [x] Socket.IO integration for real-time results

### ❌ What Needs Deployment
- [ ] Rebuild audio service container with MQTT fix
- [ ] Verify audio service starts and connects to mosquitto
- [ ] Test end-to-end: Button → Recording → Classification → Display

---

## 🔄 Complete Audio Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AUDIO CLASSIFICATION FLOW                        │
└─────────────────────────────────────────────────────────────────────┘

1. USER ACTION:
   Dashboard → Click "Record 1 Minute & Analyze" button
   
2. DASHBOARD (Socket.IO Event):
   JavaScript → socket.emit('trigger_audio_recording', {duration: 60})
   
3. DASHBOARD BACKEND (Python):
   dashboard_app.py → Publishes MQTT message:
   Topic: hive/audio/control
   Payload: {
     "command": "record_and_classify",
     "duration_sec": 60,
     "timestamp": 1234567890
   }
   
4. AUDIO SERVICE (Subscriber):
   ml_audio_service.py → Receives MQTT message
   → on_message() → Sets recording_requested = True
   
5. AUDIO RECORDING:
   AudioProcessor.record_and_classify(duration_sec=60):
   → record_audio() → Captures 60 seconds from microphone
   → extract_features() → Generates mel spectrogram, MFCCs
   → classify() → Runs ML model (scikit-learn classifier)
   
6. AUDIO SERVICE (Publisher):
   Publishes classification results:
   Topic: hive/audio/classification
   Payload: {
     "timestamp": "2025-10-19T01:30:00",
     "model_type": "audio_ml_classifier",
     "results": {
       "classification": "queen_present",  # or "queen_absent"
       "confidence": 0.87,
       "duration": 60.0,
       "status": "complete"
     }
   }
   
7. DASHBOARD (Subscriber):
   dashboard_app.py → on_message() receives result
   → socketio.emit('audio_classification_update', results)
   
8. BROWSER (JavaScript):
   Receives Socket.IO event
   → Updates UI:
     - Classification: "Queen Present" (or "Queen Absent")
     - Confidence: "87%"
     - Status: "Complete"
```

---

## 🚀 Deployment Steps

### Step 1: Pull Latest Code

```bash
cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization
```

**Expected Changes**:
- `ml_audio_service.py` - MQTT connection fix (no TLS)
- `dashboard/dashboard_app.py` - Audio recording handler
- `dashboard/templates/index.html` - Audio recording button
- `dashboard/static/app.js` - Socket.IO audio events

### Step 2: Verify Audio Model Exists

The audio service needs a pretrained ML model:

```bash
# Check if model exists
ls -lh models/audio_model.pkl

# If missing, check alternative location
ls -lh ml_audio_model/*.pkl
```

**If model missing**, you'll need to:
- Train a model using your audio dataset
- Or use a placeholder (service will fail gracefully)

### Step 3: Rebuild Audio Service Container

```bash
# Build audio service with latest code
docker compose build smart-hive-audio

# Start/restart the service
docker compose up -d smart-hive-audio
```

**Build Time**: ~5-10 minutes (installs librosa, scipy, scikit-learn)

### Step 4: Verify Audio Service Started

```bash
# Check container status
docker ps | grep audio

# Check logs for successful startup
docker logs smart-hive-audio 2>&1 | tail -30
```

**Expected Output**:
```
✅ AudioProcessor imported successfully
Connecting to local MQTT broker: mosquitto:1883
✅ MQTT connected to mosquitto:1883
✅ MQTT connected successfully
✅ Audio processor initialized
🎤 Audio service ready (on-demand recording mode)
```

**If you see errors**:
```
❌ MQTT connection failed
⚠️  Audio processor init failed: No such file or directory: 'models/audio_model.pkl'
⚠️  Audio processor not available
```

### Step 5: Verify MQTT Subscription

```bash
# Check if audio service subscribed to control topic
docker exec mosquitto mosquitto_sub -v -t 'hive/audio/#' -C 1 &

# Publish test command
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":10}'

# Check audio service logs
docker logs smart-hive-audio 2>&1 | tail -5
```

**Expected**:
```
📨 Control message: hive/audio/control = {"command":"record_and_classify","duration_sec":10}
🎤 Recording requested: 10 seconds
🎙️  Starting 10s recording...
```

### Step 6: Test from Dashboard

1. **Open Dashboard**: http://192.168.88.16:5000
2. **Go to "AI Audio Analysis" section**
3. **Click**: "🎤 Record 1 Minute & Analyze" button
4. **Observe**:
   - Button text changes to "Recording... (60s remaining)"
   - Progress bar appears
   - Status shows "Recording in progress"

5. **After 60 seconds**:
   - Classification appears: "Queen Present" or "Queen Absent"
   - Confidence shows: "87%" (example)
   - Status: "Complete"

### Step 7: Monitor Logs During Test

```bash
# Terminal 1: Watch audio service
docker logs -f smart-hive-audio

# Terminal 2: Watch dashboard
docker logs -f smart-hive-dashboard

# Terminal 3: Watch MQTT traffic
docker exec mosquitto mosquitto_sub -v -t '#'
```

---

## 🔧 Troubleshooting

### Issue 1: "Audio processor disabled" Error

**Symptom**:
```json
{
  "error": "Audio processor disabled",
  "status": "failed"
}
```

**Causes**:
1. Audio service not connected to MQTT → Check logs for connection errors
2. Audio model file missing → Check `models/audio_model.pkl` exists
3. Audio service container not running → `docker ps | grep audio`

**Fix**:
```bash
# Rebuild audio service
docker compose build smart-hive-audio
docker compose up -d smart-hive-audio

# Check initialization
docker logs smart-hive-audio 2>&1 | grep -E "processor|MQTT|Error"
```

### Issue 2: No Response from Audio Service

**Symptom**: Button clicks but nothing happens (no recording starts)

**Check**:
```bash
# 1. Is audio service receiving MQTT messages?
docker logs smart-hive-audio 2>&1 | grep "Control message"

# 2. Is dashboard publishing correctly?
docker logs smart-hive-dashboard 2>&1 | grep "audio recording command"

# 3. Is mosquitto running?
docker ps | grep mosquitto
```

**Fix**:
```bash
# Restart mosquitto
docker compose restart mosquitto

# Restart audio service
docker compose restart smart-hive-audio
```

### Issue 3: Microphone Not Accessible

**Symptom**:
```
OSError: [Errno -9996] Invalid input device
```

**Check**:
```bash
# List audio devices
docker exec smart-hive-audio arecord -l

# Expected: Should show Samson USB microphone
```

**Fix**:
```bash
# Verify /dev/snd is mounted
docker inspect smart-hive-audio | grep -A 5 Devices

# Should show: "/dev/snd:/dev/snd"
```

### Issue 4: Model File Missing

**Symptom**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'models/audio_model.pkl'
```

**Temporary Fix** (allows service to start):
```bash
# Create empty placeholder (service will warn but won't crash)
mkdir -p models
touch models/audio_model.pkl
```

**Permanent Fix**: Train audio classification model
- Use your queen bee audio dataset
- Train scikit-learn classifier
- Save as `models/audio_model.pkl`

### Issue 5: Dashboard Not Showing Results

**Symptom**: Recording completes but classification doesn't appear

**Check**:
```bash
# 1. Is audio service publishing results?
docker exec mosquitto mosquitto_sub -t 'hive/audio/classification' -C 1

# 2. Is dashboard receiving MQTT messages?
docker logs smart-hive-dashboard 2>&1 | grep "audio/classification"

# 3. Is Socket.IO emitting events?
docker logs smart-hive-dashboard 2>&1 | grep "audio_classification_update"
```

**Fix**: Check browser console (F12) for Socket.IO errors

---

## 📊 Expected Behavior After Fix

### ✅ Successful Recording Flow

**Dashboard Logs**:
```
Audio recording trigger received: {'duration': 60}
Published audio recording command with result: (0, 123)
📥 Received MQTT message on topic: hive/audio/classification
   Payload: {'timestamp': '2025-10-19T01:30:00', 'model_type': 'audio_ml_classifier', 'results': {'classification': 'queen_present', 'confidence': 0.87}}
```

**Audio Service Logs**:
```
📨 Control message: hive/audio/control = {"command":"record_and_classify","duration_sec":60}
🎤 Recording requested: 60 seconds
🎙️  Starting 60s recording...
✅ Audio features extracted: (60.0s, 13 MFCCs)
✅ Classification complete: queen_present (confidence: 0.87)
✅ Audio results published: queen_present
```

**Dashboard UI**:
```
AI Audio Analysis
─────────────────────────────────────
Ready to record

Classification: Queen Present
Confidence: 87%

[🎤 Record 1 Minute & Analyze]

Status: Complete
Last Analysis: 2 minutes ago
```

---

## 🎯 Quick Start Commands

Copy-paste these commands to deploy audio service:

```bash
# 1. Pull latest code
cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization

# 2. Check audio model exists (optional)
ls -lh models/audio_model.pkl || echo "⚠️  Model missing - will need to train or use placeholder"

# 3. Rebuild audio service
docker compose build smart-hive-audio

# 4. Start audio service
docker compose up -d smart-hive-audio

# 5. Wait for initialization
sleep 10

# 6. Verify startup
docker logs smart-hive-audio 2>&1 | tail -20

# 7. Test MQTT subscription
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'

# 8. Check response
docker logs smart-hive-audio 2>&1 | tail -10
```

---

## 📝 Files Modified (Already Committed)

### 1. `ml_audio_service.py` (Line 62-88)
**Change**: Removed TLS setup, connect to local mosquitto
```python
# BEFORE:
self.mqtt_client.tls_set(ca_certs=config.CA_CERT, ...)
self.mqtt_client.connect(config.AWS_ENDPOINT, 8883)

# AFTER:
self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
```

### 2. `dashboard/dashboard_app.py` (Line 270-290)
**Added**: Audio recording trigger handler
```python
@socketio.on('trigger_audio_recording')
def handle_trigger_audio_recording(data):
    recording_command = {
        "command": "record_and_classify",
        "duration_sec": data.get('duration', 60),
        "timestamp": int(time.time())
    }
    mqtt_client.publish(config.TOPIC_AUDIO_CONTROL, json.dumps(recording_command), qos=1)
```

### 3. `dashboard/templates/index.html` (Line 85-100)
**Added**: Audio recording button and status display

### 4. `dashboard/static/app.js`
**Added**: Socket.IO event handlers for audio recording

---

## 🎉 Success Criteria

System is working when:
- [x] Audio service starts without errors
- [x] Audio service connects to mosquitto (port 1883)
- [x] Dashboard button triggers recording command
- [x] Audio service receives MQTT command
- [x] Audio service records 60 seconds from microphone
- [x] Audio service extracts features (MFCCs, mel spectrogram)
- [x] Audio service runs ML classification
- [x] Audio service publishes results to MQTT
- [x] Dashboard receives and displays classification
- [x] Browser shows: "Queen Present" (or "Queen Absent") with confidence

---

## 📞 Next Steps

After running the deployment commands, report:
1. **Audio service logs** (last 20 lines)
2. **Does "Record 1 Minute & Analyze" button work?**
3. **Any errors in browser console (F12)?**
4. **Does classification appear after 60 seconds?**

Let's get that audio recording working! 🎤🐝
