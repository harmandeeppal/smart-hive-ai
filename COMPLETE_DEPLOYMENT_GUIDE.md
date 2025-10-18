# Complete Smart Hive Deployment Guide

## 🎯 What's New in This Update

### 1. ✅ **Audio ML Classification** (READY - Just needs rebuild)
- Fixed missing packages issue (librosa, scikit-learn, sounddevice)
- Complete recording → ML classification → dashboard display flow
- Real-time waveform visualization and sound level bars
- Color-coded results (GREEN for queen_present, RED for queen_absent)

### 2. ✅ **Video & AI Vision Toggle Controls** (NEW)
- **📹 Video Toggle**: Turn camera stream ON/OFF independently
- **🤖 AI Vision Toggle**: Enable/disable AI detection on demand
- **Graceful Fallback**: No more broken images - shows helpful error messages
- **Save Resources**: Disable video/AI when not needed to reduce CPU load

---

## 📋 Deployment Steps (Run on Raspberry Pi)

### **Step 1: Pull Latest Code**

```bash
ssh pi@192.168.88.16
cd ~/smart-hive-ai

# Pull all the new features
git pull origin feature/project-cleanup-and-ml-reorganization
```

**Expected Output:**
```
Updating c84cc77..fad0d42
Fast-forward
 app.py                           | 120 ++++++++++++--
 dashboard/templates/index.html   |  28 ++-
 dashboard/static/styles.css      |  65 +++++++
 dashboard/static/app.js          | 106 +++++++++++
 dashboard/dashboard_app.py       |  12 ++
 5 files changed, 300 insertions(+), 31 deletions(-)
```

---

### **Step 2: Rebuild Audio Service** ⏳ **CRITICAL - Takes 8-12 Minutes**

```bash
# This is THE FIX for "Waiting for analysis..." issue
docker compose build --no-cache smart-hive-audio
```

**What You'll See:**
```
[+] Building 520.3s (12/12) FINISHED
 => [6/12] RUN pip install --no-cache-dir -r requirements-audio.txt
 => Collecting librosa==0.10.0
 => Collecting scikit-learn==1.3.0
 => Collecting sounddevice==0.4.6
 => Building wheels for librosa (takes 5-8 minutes on Pi)
 => Successfully installed librosa-0.10.0 scikit-learn-1.3.0 sounddevice-0.4.6
```

**Start the rebuilt service:**
```bash
docker compose up -d smart-hive-audio

# Wait for startup
sleep 10

# Verify packages installed ✅
docker logs smart-hive-audio 2>&1 | head -30
```

**SUCCESS Indicators:**
```
✅ Audio model loaded successfully  ← This line MUST appear!
Model expects 13 MFCC features
🎤 Audio service ready (on-demand recording mode)
```

**FAILURE Indicators (rebuild didn't work):**
```
❌ Required packages not installed  ← BAD! Run build again
```

---

### **Step 3: Rebuild Edge-App** (For Video/AI Toggles)

```bash
docker compose build --no-cache smart-hive-edge-app
docker compose up -d smart-hive-edge-app
```

**Expected:**
```
[+] Building 45.2s (10/10) FINISHED
✔ Container smart-hive-edge-app Started
```

---

### **Step 4: Rebuild Dashboard** (For Toggle UI)

```bash
docker compose build --no-cache dashboard
docker compose up -d dashboard
```

**Expected:**
```
[+] Building 20.1s (9/9) FINISHED
✔ Container smart-hive-dashboard Started
```

---

### **Step 5: Verify All Containers Running**

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**Expected:**
```
NAMES                    STATUS         PORTS
smart-hive-edge-app      Up 30 seconds  0.0.0.0:5001->5001/tcp
smart-hive-dashboard     Up 25 seconds  0.0.0.0:5000->5000/tcp
smart-hive-audio         Up 2 minutes   
mosquitto                Up 10 hours    0.0.0.0:1883->1883/tcp
```

---

## 🧪 Testing

### **Test 1: Audio ML Classification**

```bash
# Quick 5-second test
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'

# Watch logs (wait 6 seconds)
docker logs smart-hive-audio --tail 15
```

**✅ Expected (SUCCESS):**
```
🎙️ Starting 5s recording...
Recording from Samson Meteorite Mic...
✅ Audio recorded: 5.0 seconds
✅ Audio features extracted: (5.0s, 13 MFCCs)  ← Package working!
✅ Classification: queen_present (confidence: 0.87)  ← ML working!
✅ Audio results published to: hive/audio/results
```

**❌ If you still see "unknown":**
```
# Packages still missing - rebuild failed
# Try again with:
docker compose stop smart-hive-audio
docker compose rm -f smart-hive-audio
docker rmi smart-hive-audio:latest
docker compose build --no-cache smart-hive-audio
docker compose up -d smart-hive-audio
```

---

### **Test 2: Dashboard Audio Recording**

1. Open dashboard: **http://192.168.88.16:5000**
2. **Hard refresh:** `Ctrl + Shift + R` (clears cache)
3. Click **"🎤 Record 1 Minute & Analyze"** button
4. Wait 60 seconds (progress bar fills)

**✅ Expected After 60 Seconds:**
- Classification: **"Queen Present"** or **"Queen Absent"** (GREEN/RED)
- Confidence: **"87.5%"** (example)
- Status: **"✅ Completed"**
- Waveform animates smoothly
- Sound level bars update in real-time

---

### **Test 3: Video Toggle Controls**

1. Open dashboard: **http://192.168.88.16:5000**
2. Hard refresh: `Ctrl + Shift + R`

**You should now see TWO buttons on video card:**
- **"📹 Video: ON"** (green button)
- **"🤖 AI Vision: OFF"** (grey button)

**Test Video Toggle:**
1. Click **"📹 Video: ON"** → Button turns grey, video feed goes dark
2. Video shows message: "Video Feed Disabled"
3. Click again → Button turns green, video resumes

**Test AI Vision Toggle:**
1. Click **"🤖 AI Vision: OFF"** → Button turns blue "AI Vision: ON"
2. If camera working: Bounding boxes appear on video
3. Check edge-app logs: `docker logs smart-hive-edge-app --tail 20`
4. Should see AI detection messages
5. Click again → Bounding boxes disappear, only raw video

**Test Combined:**
- **Video ON + AI ON**: Live video with bounding boxes
- **Video ON + AI OFF**: Raw video only (saves CPU)
- **Video OFF + AI ON**: No video (AI disabled)
- **Video OFF + AI OFF**: No video, no processing

---

### **Test 4: Camera Fallback**

**If camera not available:**
- Should see: **"Camera Not Available"** (red text)
- Should NOT see: Broken image icon ✅
- Toggles still work (but video won't show until camera fixed)

**Check camera:**
```bash
# Test if camera accessible in edge-app container
docker exec smart-hive-edge-app python3 -c "
import cv2
camera = cv2.VideoCapture(0)
if camera.isOpened():
    ret, frame = camera.read()
    print(f'✅ Camera working: {frame.shape if ret else \"Failed to read\"}')
    camera.release()
else:
    print('❌ Camera not available')
"
```

---

## 📊 Dashboard Features Summary

### **Before This Update:**
- ❌ Video showed broken image icon
- ❌ Audio recording stuck at "Waiting for analysis..."
- ❌ No control over video/AI processing
- ❌ CPU always running AI even when not needed

### **After This Update:**
- ✅ **Video Feed**: Shows helpful error if camera unavailable
- ✅ **Audio ML**: Complete classification with confidence scores
- ✅ **Video Toggle**: Turn camera stream ON/OFF
- ✅ **AI Toggle**: Enable/disable detection on demand
- ✅ **Resource Control**: Save CPU by disabling unnecessary processing
- ✅ **Professional UI**: Waveform visualization, gradient buttons, smooth animations

---

## 🎨 UI Enhancements Visible in Dashboard

### **Audio ML Card:**
- 🌊 Animated green waveform (60 FPS)
- 📊 10-bar sound level indicator (gradient colors)
- 🎨 Dark theme visualizer (#1a1a2e background)
- 📈 Live dB updates from telemetry
- 🟢/🔴 Color-coded classifications
- ⏱️ Enhanced recording progress bar

### **Video Feed Card:**
- 📹 Video toggle button (green when ON, grey when OFF)
- 🤖 AI vision toggle button (blue when ON, grey when OFF)
- 📊 Live status indicators for both toggles
- 🎥 Graceful error messages if camera unavailable
- 🔄 Smooth opacity/filter transitions

---

## 🐛 Troubleshooting

### **Issue: Audio Still Returns "unknown"**

**Symptom:**
```
✅ Audio results published: unknown
```

**Cause:** Audio service still using old cached image

**Solution:**
```bash
# Force complete rebuild
docker compose stop smart-hive-audio
docker compose rm -f smart-hive-audio
docker rmi smart-hive-audio:latest

# Clean Docker cache
docker system prune -f

# Rebuild from scratch
docker compose build --no-cache smart-hive-audio
docker compose up -d smart-hive-audio

# Verify logs
docker logs smart-hive-audio 2>&1 | grep -E "Audio model|packages|librosa"
```

**Expected in logs:**
```
✅ Audio model loaded successfully  ← MUST see this!
```

---

### **Issue: Toggle Buttons Not Showing**

**Symptom:** Still see single "Toggle: ON" button on video card

**Cause:** Browser cache or dashboard not rebuilt

**Solution:**
```bash
# On Pi:
docker compose build --no-cache dashboard
docker compose up -d dashboard

# In browser:
# 1. Hard refresh: Ctrl + Shift + R
# 2. If still old, clear browser cache completely
# 3. Refresh again
```

---

### **Issue: "Camera Not Available" Showing**

**Possible Causes:**

1. **Camera already in use:**
   ```bash
   # Check what's using camera
   lsof /dev/video0
   
   # If needed, kill process
   sudo kill <PID>
   ```

2. **Camera not mounted in Docker:**
   ```bash
   # Check docker-compose.yml has:
   grep -A 5 "smart-hive-edge-app" docker-compose.yml | grep devices
   
   # Should show:
   # devices:
   #   - /dev/video0:/dev/video0
   ```

3. **OpenCV can't access camera:**
   ```bash
   # Test camera access
   docker exec smart-hive-edge-app python3 -c "
   import cv2
   cam = cv2.VideoCapture(0)
   print('Camera opened:', cam.isOpened())
   if cam.isOpened():
       ret, frame = cam.read()
       print('Frame shape:', frame.shape if ret else 'Failed')
   cam.release()
   "
   ```

---

### **Issue: Waveform Not Animating**

**Cause:** JavaScript error or telemetry not publishing sound_db

**Solution:**
```bash
# 1. Check browser console (F12)
# Look for errors related to "audio-waveform" or "animateWaveform"

# 2. Verify telemetry includes sound_db
docker exec mosquitto mosquitto_sub -t 'hive/telemetry' -C 1

# Should see:
{
  "temperature": 24.5,
  "sound_db": 42.3,  ← This field must be present
  ...
}

# 3. If missing, check edge-app logs
docker logs smart-hive-edge-app --tail 30
```

---

## 📝 Configuration Reference

### **Default States After Deployment:**
- Video Stream: **ON** (shows live camera feed)
- AI Vision: **OFF** (no bounding boxes, save CPU)
- Audio Service: **ON** (ready for on-demand recording)
- All Sensor Toggles: **ON**

### **MQTT Topics Added:**
- `hive/control/video` - Video stream control
- `hive/control/ai_vision` - AI detection control
- `hive/status/video` - Video status updates
- `hive/status/ai_vision` - AI status updates

### **Files Modified:**
1. `app.py` - Video/AI toggle logic, camera fallback
2. `dashboard/templates/index.html` - Two toggle buttons
3. `dashboard/static/styles.css` - Button gradients, video container
4. `dashboard/static/app.js` - Toggle handlers, Socket.IO listeners
5. `dashboard/dashboard_app.py` - Status topic subscriptions

---

## ⏱️ Deployment Timeline

| Step | Duration | Description |
|------|----------|-------------|
| git pull | 10 seconds | Download latest code |
| Audio build | **8-12 minutes** | ⏳ Longest step - package compilation |
| Edge-app build | 2-3 minutes | Video/AI toggle implementation |
| Dashboard build | 1-2 minutes | UI updates |
| Testing | 2-3 minutes | Verify all features working |
| **TOTAL** | **~15-20 minutes** | Complete deployment |

---

## ✅ Success Criteria

### **System Fully Operational When:**

1. **Audio ML Works:**
   ```bash
   docker logs smart-hive-audio | grep "Audio model loaded successfully"
   # Returns: ✅ Audio model loaded successfully
   ```

2. **Recording Classifies:**
   ```bash
   # Test command returns classification (not "unknown")
   docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'
   docker logs smart-hive-audio --tail 5
   # Shows: ✅ Classification: queen_present (confidence: 0.87)
   ```

3. **Dashboard Shows:**
   - ✅ Two toggle buttons on video card
   - ✅ Waveform animating smoothly
   - ✅ Sound level bars updating
   - ✅ Video feed showing (or helpful error message)
   - ✅ Audio classification completes after recording

4. **Toggles Work:**
   - ✅ Video button turns video ON/OFF
   - ✅ AI button turns detection ON/OFF
   - ✅ Status text updates in real-time

---

## 🚀 Quick Deployment Commands

**Copy-paste this entire block on Raspberry Pi:**

```bash
# Navigate to project
cd ~/smart-hive-ai

# Pull latest code
git pull origin feature/project-cleanup-and-ml-reorganization

# Rebuild all services (takes ~12 minutes total)
echo "⏳ Rebuilding audio service (8-12 min)..."
docker compose build --no-cache smart-hive-audio

echo "⏳ Rebuilding edge-app (2-3 min)..."
docker compose build --no-cache smart-hive-edge-app

echo "⏳ Rebuilding dashboard (1-2 min)..."
docker compose build --no-cache dashboard

# Restart all services
docker compose up -d smart-hive-audio smart-hive-edge-app dashboard

# Wait for startup
sleep 15

# Show status
echo "📊 Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}"

# Verify audio ML
echo ""
echo "🎤 Audio Service Logs:"
docker logs smart-hive-audio 2>&1 | grep -E "Audio model|packages|ready"

# Test audio classification
echo ""
echo "🧪 Testing audio classification (5 seconds)..."
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'
sleep 6
docker logs smart-hive-audio --tail 10

echo ""
echo "✅ Deployment complete!"
echo "🌐 Open dashboard: http://192.168.88.16:5000"
echo "🔄 Remember to hard refresh (Ctrl+Shift+R) in browser!"
```

---

## 📚 Summary

**What Was Fixed:**
1. ✅ Audio ML classification (librosa/scikit-learn packages installed)
2. ✅ Video/AI toggle controls (independent ON/OFF)
3. ✅ Camera availability fallback (no more broken images)
4. ✅ Resource management (disable video/AI to save CPU)

**What You'll See:**
- Professional waveform visualization
- Color-coded ML classifications  
- Two separate toggle buttons for video and AI
- Graceful error messages if hardware unavailable

**Time Required:** 15-20 minutes total deployment

**Next Steps:** Open http://192.168.88.16:5000 and test all features!
