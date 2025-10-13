# Quick Configuration Guide - Smart Hive AI

## 🎯 Configurable Parameters

All timing, thresholds, and hardware settings are now centralized in `config.py`. Here's what you can control:

---

## ⏱️ TIMING CONFIGURATION

### Sensor Update Intervals
```python
# How often sensors publish data (in seconds)
TELEMETRY_INTERVAL_SECONDS = 5  
# Recommendation: 5-10 seconds for real-time monitoring
# Lower = More data, higher AWS costs
# Higher = Less responsive, lower costs

# How often AI vision runs (in seconds)
VISION_LOOP_INTERVAL_SECONDS = 1
# Recommendation: 1-2 seconds
# Note: Only publishes when queen detected

# How often to upload general snapshots to S3 (in seconds)
S3_SNAPSHOT_INTERVAL_SECONDS = 300  # 5 minutes
# Recommendation: 300-600 seconds (5-10 minutes)
# Lower = More storage costs
```

### AWS Data Flow
```
Edge Device → AWS IoT Core (MQTT) → Dashboard
     ↓
  AWS S3 (Images)

Telemetry: Every 5 seconds
Vision Events: When queen detected (+ image upload)
General Snapshots: Every 5 minutes
```

---

## 🔧 HARDWARE CONFIGURATION

### I2C Sensors (SunFounder Kit)
```python
# I2C Bus (default on Raspberry Pi)
I2C_BUS = 1  # GPIO pins: SCL=Pin 5, SDA=Pin 3

# BME280 Temperature & Humidity
BME280_ADDRESS = 0x77  # Or 0x76 (check with i2cdetect)

# LIS3DH Accelerometer/Vibration
LIS3DH_ADDRESS = 0x18  # Or 0x19 (check with i2cdetect)
```

**To find your sensor addresses:**
```bash
# On Raspberry Pi:
sudo i2cdetect -y 1
```

### Camera Settings
```python
# Camera Type
CAMERA_TYPE = "USB"  # Options: "USB" or "PICAMERA"

# USB Camera (Logitech)
CAMERA_DEVICE_INDEX = 0  # Usually 0 for first camera
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# If multiple cameras, check with:
# ls /dev/video*
```

### Microphone Settings
```python
# Samson USB Microphone
MICROPHONE_SAMPLE_RATE = 44100  # Hz (CD quality)
MICROPHONE_DURATION_MS = 100    # For dB sampling
MICROPHONE_FREQ_DURATION_SEC = 1.0  # For frequency analysis
```

---

## 📊 THRESHOLD CONFIGURATION

### Temperature (°C)
**Location:** `dashboard/static/app.js` Line 41-55

```javascript
// Current thresholds:
if (temp <= 32) {
    status = 'Too Cold';
    action = 'LOW TEMP ALERT: Investigate colony strength...';
} else if (temp >= 37) {
    status = 'Too Hot';
    action = 'HIGH TEMP ALERT: Consider ventilation...';
} else {
    status = 'Optimal';
    action = 'None required.';
}
```

**To customize:**
```javascript
// For different climate zones:
if (temp <= 30) { // Colder threshold
if (temp >= 39) { // Hotter threshold
```

### Humidity (%)
**Location:** `dashboard/static/app.js` Line 57-72

```javascript
// Current thresholds:
if (hum <= 45) {
    status = 'Too Dry';
} else if (hum >= 75) {
    status = 'Too Wet';
} else {
    status = 'Optimal';
}
```

### Vibration (RMS)
**Location:** `dashboard/static/app.js` Line 74-89

```javascript
// Current thresholds:
if (rms > 0.15) {  // Agitated
    status = 'Agitation Alert';
} else if (rms < 0.02) {  // Low activity
    status = 'Low Activity Alert';
} else {
    status = 'Normal Activity';
}
```

**Calibration needed:**
- Run system for 1 week
- Note baseline RMS values
- Adjust thresholds based on YOUR hive's normal activity

### Sound Frequency (Hz)
**Location:** `dashboard/static/app.js` Line 117-141

```javascript
// Current thresholds (research-based):
if (freq >= 450 && freq <= 600) {
    // Swarming signals (piping/quacking)
} else if (freq >= 350 && freq < 450) {
    // Queenless roar
} else if (freq < 150 && db < 42) {
    // Sudden silence
} else if (freq >= 200 && freq < 350) {
    // Normal healthy hum
}
```

---

## 🧪 TESTING MODE CONFIGURATION

### Mock Environment (Laptop Testing)
```python
# In config.py:
IS_MOCK_ENVIRONMENT = True
```

**What this does:**
- Uses `mock_components.py` (no real sensors needed)
- Generates random data within realistic ranges
- Simulates queen detection (20% chance per frame)
- Logs S3 uploads instead of actually uploading

### Real Environment (Raspberry Pi)
```python
# In config.py:
IS_MOCK_ENVIRONMENT = False
```

**What this does:**
- Uses `real_components.py` (requires sensors)
- Reads actual sensor data
- Runs real AI inference
- Actually uploads to S3

---

## 🎨 DASHBOARD CUSTOMIZATION

### Visual Appearance
**Location:** `dashboard/static/styles.css`

```css
/* Card colors */
.card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }

/* Alert colors */
.action-text { color: #ffd700; }  /* Gold for warnings */

/* Gauge bar colors */
.gauge-bar::before { background: linear-gradient(...); }
```

### Alert Emojis
**Location:** `dashboard/static/app.js`

```javascript
// Temperature
elements.temp.status.textContent = '☀️ Too Hot';
elements.temp.status.textContent = '❄️ Too Cold';

// Sound
elements.sound.status.textContent = '🏃 SWARM PREDICTION ALERT';
elements.sound.status.textContent = '👑 QUEEN STATUS ALERT';
elements.sound.status.textContent = '💀 DISTRESS/MORTALITY ALERT';
```

---

## 🔐 AWS CONFIGURATION

### Environment Variables (.env file)
```bash
# Create .env file in project root:
AWS_ENDPOINT=your-endpoint.iot.region.amazonaws.com
CERT_FILE_NAME=your-certificate.pem.crt
KEY_FILE_NAME=your-private.pem.key
S3_BUCKET_NAME=smart-hive-snapshots-your-name
SECRET_KEY=your-flask-secret-key
```

### MQTT Topics
```python
# In config.py:
TOPIC_TELEMETRY = "hive/telemetry"  # Sensor data
TOPIC_VISION = "hive/vision"        # Queen detections
TOPIC_CONTROL = "hive/control"      # Toggle commands
```

**To customize:**
```python
# For multiple hives:
TOPIC_TELEMETRY = "hive/hive1/telemetry"
TOPIC_TELEMETRY = "hive/hive2/telemetry"
```

---

## 📈 PERFORMANCE TUNING

### Reduce AWS Costs
```python
# Lower frequency of updates:
TELEMETRY_INTERVAL_SECONDS = 10  # Instead of 5
S3_SNAPSHOT_INTERVAL_SECONDS = 600  # Instead of 300

# Upload only high-confidence detections:
# In app.py, line 238:
if box is not None and confidence is not None and confidence > 0.90:
    # Only upload if >90% confident
```

### Improve AI Performance
```python
# Increase vision loop interval (less CPU):
VISION_LOOP_INTERVAL_SECONDS = 2  # Instead of 1

# Lower camera resolution (faster processing):
CAMERA_WIDTH = 320  # Instead of 640
CAMERA_HEIGHT = 240  # Instead of 480
```

### Better Frequency Analysis
```python
# Higher resolution (slower but more accurate):
MICROPHONE_FREQ_DURATION_SEC = 2.0  # Instead of 1.0

# Higher sample rate (better quality):
MICROPHONE_SAMPLE_RATE = 48000  # Instead of 44100
```

---

## 🔄 MULTI-HIVE SETUP

To monitor multiple hives with one dashboard:

### 1. Edge Devices (Multiple Raspberry Pis)
```python
# Hive 1 - config.py:
THING_NAME = "SmartHive_Pi_Hive1"
TOPIC_TELEMETRY = "hive/hive1/telemetry"
TOPIC_VISION = "hive/hive1/vision"
TOPIC_CONTROL = "hive/hive1/control"

# Hive 2 - config.py:
THING_NAME = "SmartHive_Pi_Hive2"
TOPIC_TELEMETRY = "hive/hive2/telemetry"
# ... etc
```

### 2. Dashboard (Single Instance)
```python
# Subscribe to all hives:
client.subscribe("hive/+/telemetry")  # + is wildcard
client.subscribe("hive/+/vision")
```

---

## 🚨 TROUBLESHOOTING CONFIGURATION

### Sensors Not Detected?
```bash
# Check I2C bus:
sudo i2cdetect -y 1

# Enable I2C if needed:
sudo raspi-config
# → Interface Options → I2C → Enable
```

### Camera Not Working?
```bash
# Check camera devices:
ls /dev/video*

# Test camera:
raspistill -o test.jpg  # For Pi Camera
fswebcam test.jpg       # For USB Camera
```

### Microphone Silent?
```bash
# List audio devices:
arecord -l

# Test recording:
arecord -d 5 test.wav
aplay test.wav
```

### AWS Connection Failed?
```bash
# Verify certificates exist:
ls certs/

# Check permissions:
chmod 644 certs/*.pem.crt
chmod 600 certs/*.pem.key

# Test MQTT connection:
# Use AWS IoT Console → Test → Subscribe to hive/#
```

---

## 📝 QUICK REFERENCE

### Restart Containers
```powershell
docker-compose down
docker-compose up --build
```

### View Logs
```powershell
docker logs smart-hive-edge -f
docker logs smart-hive-dashboard -f
```

### Access Dashboard
```
http://localhost:5000
```

### Direct Video Feed
```
http://localhost:5001/video_feed
```

### Force Mock Environment
```python
# Temporarily override in app.py:
import config
config.IS_MOCK_ENVIRONMENT = True
```

---

## 🎓 RECOMMENDED CONFIGURATIONS

### For Development (Laptop):
```python
IS_MOCK_ENVIRONMENT = True
TELEMETRY_INTERVAL_SECONDS = 5
VISION_LOOP_INTERVAL_SECONDS = 1
```

### For Testing (Raspberry Pi):
```python
IS_MOCK_ENVIRONMENT = False
TELEMETRY_INTERVAL_SECONDS = 10
VISION_LOOP_INTERVAL_SECONDS = 2
S3_SNAPSHOT_INTERVAL_SECONDS = 600
```

### For Production (Deployed):
```python
IS_MOCK_ENVIRONMENT = False
TELEMETRY_INTERVAL_SECONDS = 30
VISION_LOOP_INTERVAL_SECONDS = 5
S3_SNAPSHOT_INTERVAL_SECONDS = 1800  # 30 minutes
```

### For Research/Data Collection:
```python
IS_MOCK_ENVIRONMENT = False
TELEMETRY_INTERVAL_SECONDS = 1  # High frequency
VISION_LOOP_INTERVAL_SECONDS = 1
S3_SNAPSHOT_INTERVAL_SECONDS = 60  # Every minute
# ⚠️ Warning: Generates LOTS of data!
```

---

## 💡 PRO TIPS

1. **Start with longer intervals**, then decrease as needed
2. **Monitor AWS costs** for first week
3. **Calibrate thresholds** after collecting baseline data
4. **Use mock mode** for UI development
5. **Test real mode** before full deployment
6. **Keep backup** of working `config.py`
7. **Document changes** to thresholds in your thesis

---

Need to change something? All key parameters are in these 3 files:
- `config.py` - Hardware and timing
- `dashboard/static/app.js` - Thresholds and alerts
- `.env` - AWS credentials

Happy beekeeping! 🐝
