# Testing Checklist - Smart Hive AI
## Before Final Deployment

---

## ✅ PRE-DEPLOYMENT TESTING (Laptop - Mock Mode)

### Phase 1: Basic Functionality
- [ ] **Containers Build Successfully**
  ```powershell
  docker-compose up --build
  # Should complete without errors
  ```

- [ ] **Dashboard Accessible**
  - Open: http://localhost:5000
  - All 5 cards visible (Temp, Humidity, Vibration, Sound, AI Vision)
  - No console errors in browser (F12)

- [ ] **Video Feed Working**
  - AI Vision card shows live feed (generated bee frames)
  - No blank/gray screen
  - Frames update smoothly

- [ ] **Sensor Data Updating**
  - "Last Updated" timestamp changes every 5 seconds
  - Temperature value changes
  - Humidity value changes
  - Vibration value changes
  - Sound dB value changes
  - Sound frequency value changes (NEW)

### Phase 2: Toggle Functionality
- [ ] **Temperature Toggle**
  - Click toggle button
  - Button text changes to "Toggle: OFF"
  - Docker logs show: "Paused sensor: temperature"
  - Temperature value stops updating on dashboard
  - Click again → "Toggle: ON" → resumes

- [ ] **Humidity Toggle**
  - Same test as temperature
  - Verify independent control

- [ ] **Vibration Toggle**
  - Same test as temperature
  - Verify independent control

- [ ] **Sound Toggle**
  - Same test as temperature
  - Both dB AND frequency should stop

- [ ] **Vision Toggle**
  - Click AI Vision toggle
  - Queen detection logs should stop appearing
  - Video feed continues (but no detection processing)

### Phase 3: Frequency Analysis & Alerts
- [ ] **Normal Hum (200-350 Hz)**
  - Wait for frequency in this range
  - Status should show: "✓ Healthy Hum"
  - Action: "None required"

- [ ] **Queenless Roar (350-450 Hz)**
  - Wait for frequency in this range
  - Status: "👑 QUEEN STATUS ALERT"
  - Action: "Check for queen presence..."

- [ ] **Swarming Signal (450-600 Hz)**
  - Wait for frequency in this range
  - Status: "🏃 SWARM PREDICTION ALERT"
  - Action: "Schedule colony split..."

### Phase 4: Abnormal Conditions
Edit `mock_components.py` to force conditions:

- [ ] **Too Hot (>37°C)**
  ```python
  # In MockBME280.get_temp_humidity():
  temp = 38.5
  ```
  - Status: "Too Hot"
  - Action: "HIGH TEMP ALERT: Consider ventilation..."
  - Bar shows in red zone

- [ ] **Too Cold (<32°C)**
  ```python
  temp = 29.0
  ```
  - Status: "Too Cold"
  - Action: "LOW TEMP ALERT: Investigate colony..."

- [ ] **Too Wet (>75%)**
  ```python
  hum = 80.0
  ```
  - Status: "Too Wet"
  - Action: "HIGH HUMIDITY ALERT: Check for moisture..."

- [ ] **Too Dry (<45%)**
  ```python
  hum = 40.0
  ```
  - Status: "Too Dry"
  - Action: "LOW HUMIDITY ALERT: Consider supplemental water..."

- [ ] **High Vibration (>0.15)**
  ```python
  # In MockLIS3DH.get_rms_acceleration():
  return 0.20
  ```
  - Status: "Agitation Alert"
  - Action: "Hive disturbed or under attack"

- [ ] **Low Vibration (<0.02)**
  ```python
  return 0.01
  ```
  - Status: "Low Activity Alert"
  - Action: "Possible cluster immobilization..."

### Phase 5: Queen Detection
- [ ] **Detection Events**
  - Docker logs show: "Mock Detection: Queen found with confidence X.XX"
  - Dashboard AI status changes to: "QUEEN DETECTED (XX%)"
  - Confidence percentage displays correctly

- [ ] **S3 Upload Logs**
  - Mock mode logs: "[S3 MOCK] Queen detected! Would upload 'detection_...jpg'"
  - Filename includes timestamp and confidence

- [ ] **Detection Persistence**
  - Status returns to "Actively Scanning" after 5 seconds

---

## ✅ AWS INTEGRATION TESTING

### Phase 6: AWS IoT Core
- [ ] **MQTT Connection**
  - Docker logs show: "Successfully connected to AWS IoT Core"
  - No connection errors

- [ ] **Telemetry Publishing**
  - AWS IoT Console → Test → Subscribe to: `hive/telemetry`
  - Messages arrive every 5 seconds
  - Payload includes: timestamp, temperature, humidity, vibration_rms, sound_db, sound_freq

- [ ] **Vision Publishing**
  - Subscribe to: `hive/vision`
  - Messages arrive when queen detected
  - Payload includes: timestamp, queen_detected, confidence, box

- [ ] **Control Messages**
  - Subscribe to: `hive/control`
  - Click toggle on dashboard
  - Message appears with: sensor name, state (on/off)

### Phase 7: AWS S3
- [ ] **S3 Bucket Exists**
  - AWS S3 Console → Bucket created
  - Bucket name matches config

- [ ] **Detection Uploads** (Only in Real mode, not mock)
  - Images appear with format: `detection_<timestamp>_conf_<XX>.jpg`
  - Images contain bounding boxes
  - Confidence in filename matches image

- [ ] **General Snapshots** (Only in Real mode, not mock)
  - Images appear with format: `snapshot_<timestamp>.jpg`
  - Upload every 5 minutes (300 seconds)

---

## ✅ RASPBERRY PI DEPLOYMENT

### Phase 8: Hardware Setup
- [ ] **I2C Sensors Connected**
  ```bash
  sudo i2cdetect -y 1
  # Should show 0x77 (BME280) and 0x18 (LIS3DH)
  ```

- [ ] **Sensor Addresses Configured**
  - Update `config.py` if addresses differ
  - Match output of `i2cdetect`

- [ ] **Camera Connected**
  ```bash
  ls /dev/video*
  # Should show /dev/video0 (or similar)
  ```

- [ ] **Microphone Connected**
  ```bash
  arecord -l
  # Should list USB microphone
  ```

### Phase 9: Real Sensor Testing
- [ ] **Change to Real Mode**
  ```python
  # In config.py:
  IS_MOCK_ENVIRONMENT = False
  ```

- [ ] **BME280 Working**
  - Logs: "Successfully initialized Real BME280 Sensor at address 0x77"
  - Temperature reads actual room temp (not random)
  - Humidity reads actual humidity

- [ ] **LIS3DH Working**
  - Logs: "Successfully initialized Real LIS3DH Sensor at address 0x18"
  - Vibration changes when you tap the sensor
  - RMS values realistic (0.02-0.08 range when still)

- [ ] **Camera Working**
  - Logs: "Successfully initialized Real Vision Processor with USB camera"
  - Video feed shows actual camera view
  - Can see yourself/objects in frame

- [ ] **Microphone Working**
  - Logs: "Successfully initialized Real INMP441 (Microphone) at 44100 Hz"
  - dB level changes when you make noise
  - Frequency analysis runs without errors

### Phase 10: Real AI Inference
- [ ] **YOLOv5 Model Loaded**
  - No errors loading `queen_bee.tflite`
  - Model input size detected (check logs)

- [ ] **Inference Speed**
  - Check time between detections
  - Should be ~1-2 seconds per frame
  - No lag or freezing

- [ ] **Real Detection Test**
  - Show image of bees to camera
  - Should detect patterns (even if untrained)
  - Bounding boxes drawn on detected objects

### Phase 11: Real S3 Uploads
- [ ] **Credentials Configured**
  - `.env` file has correct AWS keys
  - S3 bucket exists and is accessible

- [ ] **Detection Uploads**
  - When queen detected, image uploads to S3
  - Logs: "QUEEN DETECTED! Successfully uploaded detection_...jpg"
  - Image appears in S3 bucket

- [ ] **General Snapshots**
  - Every 5 minutes, snapshot uploads
  - Logs: "Successfully uploaded snapshot_...jpg"
  - Images accumulate in bucket

---

## ✅ PERFORMANCE & STABILITY

### Phase 12: Stress Testing
- [ ] **24-Hour Continuous Run**
  - Start containers
  - Let run for 24 hours
  - Check for memory leaks
  - Verify no crashes

- [ ] **Network Interruption**
  - Disconnect internet
  - System should log errors but not crash
  - Reconnect → should auto-reconnect to AWS

- [ ] **Rapid Toggle Test**
  - Toggle all sensors ON/OFF rapidly
  - No crashes or deadlocks
  - System responds smoothly

- [ ] **CPU Usage Acceptable**
  ```bash
  docker stats
  # Check CPU % for both containers
  # Should be <50% average
  ```

### Phase 13: Data Validation
- [ ] **Sensor Ranges Realistic**
  - Temperature: 20-40°C range
  - Humidity: 30-90% range
  - Vibration: 0.01-0.3 RMS
  - Sound: 40-70 dB
  - Frequency: 100-1000 Hz

- [ ] **No NaN or Null Values**
  - Check dashboard for "--" or "NaN"
  - All values should be numbers

- [ ] **Timestamps Correct**
  - "Last Updated" shows current time
  - Not stuck in past
  - Updates every 5 seconds

---

## ✅ FINAL PRODUCTION CHECKLIST

### Phase 14: Optimization
- [ ] **Increase Intervals for Production**
  ```python
  TELEMETRY_INTERVAL_SECONDS = 30  # From 5
  S3_SNAPSHOT_INTERVAL_SECONDS = 1800  # From 300
  ```

- [ ] **Remove Debug Logs**
  - Comment out excessive print statements
  - Keep only error/warning logs

- [ ] **Security Hardening**
  - `.env` file not committed to Git
  - AWS credentials secured
  - Certificate files protected (chmod 600)

### Phase 15: Documentation
- [ ] **Update README.md**
  - Installation steps
  - Configuration guide
  - Troubleshooting section

- [ ] **Create User Guide**
  - How to read dashboard
  - What each alert means
  - When to take action

- [ ] **Document Calibration**
  - Baseline values for YOUR hive
  - Seasonal variations
  - Normal vs. abnormal patterns

---

## 🎓 THESIS DOCUMENTATION CHECKLIST

- [ ] **Screenshots Collected**
  - Dashboard in normal state
  - Dashboard showing each alert type
  - AWS IoT Console with messages
  - S3 bucket with images

- [ ] **Data Collected**
  - At least 1 week of continuous data
  - Examples of all alert types
  - Queen detection events

- [ ] **Performance Metrics**
  - Detection accuracy
  - False positive rate
  - System uptime
  - AWS costs

- [ ] **Code Repository**
  - GitHub repo created
  - All code committed
  - README.md complete
  - License added

---

## 🐛 KNOWN ISSUES & WORKAROUNDS

### Issue: Video feed blank in Docker
**Status:** ✅ FIXED (changed to edge-app:5001)

### Issue: Toggles don't stop sensors
**Status:** ✅ FIXED (added wait loops)

### Issue: No frequency data
**Status:** ✅ FIXED (added FFT analysis)

### Issue: Mock detection continuous
**Status:** ⚠️ Expected behavior (not analyzing frames)

### Issue: Real model needs training
**Status:** ⚠️ User action required (train on bee images)

---

## 📊 SUCCESS CRITERIA

Your system is ready for deployment when:

✅ All containers build without errors
✅ Dashboard displays all 5 sensor cards
✅ Video feed shows live camera/mock frames
✅ Toggles control sensor loops
✅ Frequency analysis shows intelligent alerts
✅ Abnormal conditions trigger correct warnings
✅ AWS IoT Core receives telemetry
✅ S3 stores detection images
✅ Real sensors work on Raspberry Pi
✅ System runs 24+ hours without crash

---

## 🚀 DEPLOYMENT SIGN-OFF

Before final deployment, confirm:

- [ ] All tests passed
- [ ] AWS costs estimated
- [ ] Backup configuration saved
- [ ] Emergency shutdown procedure documented
- [ ] Contact for technical support identified

**Deployment Date:** _____________

**Signed:** _____________

---

Good luck with your Smart Hive AI system! 🐝🎓
