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
# Lower = More data, higher DynamoDB costs
# Higher = Less responsive, lower costs
```

### Data Flow
```
Edge Device → Local MQTT Broker → Dashboard
     ↓
  AWS DynamoDB (Optional)

Telemetry: Every 5 seconds
Audio ML Events: When audio patterns detected
Camera Stream: Continuous (no AI detection)
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
# Samson USB Microphone (INMP441)
MICROPHONE_SAMPLE_RATE = 44100  # Hz (CD quality)
MICROPHONE_DURATION_MS = 100    # For dB sampling
MICROPHONE_FREQ_DURATION_SEC = 1.0  # For frequency analysis
```

### Audio ML Settings
```python
# Audio ML Classifier (Random Forest)
AUDIO_CONFIDENCE_THRESHOLD = 0.6  # 60% confidence minimum
# Recommendation: 0.5-0.7
# Lower = More sensitive (more false positives)
# Higher = More selective (may miss events)

AUDIO_WINDOW_SECONDS = 1.0   # Analysis window duration
AUDIO_HOP_SECONDS = 0.5      # Sliding window step
# Recommendation: Keep defaults for balanced performance

AUDIO_AGGREGATION_METHOD = 'max_proba'  # How to combine predictions
# Options: 'max_proba', 'vote', 'average'
# max_proba = Use highest confidence prediction
```

**Audio ML Model:**
- Model file: `models/audio_model_pipeline.pkl`
- Features: 312 (13 MFCC × 3 types × 8 statistics)
- Classes: Normal, Swarming, Queenless, etc.
- Training: scikit-learn RandomForestClassifier

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
- Simulates audio ML predictions
- No actual hardware required

### Real Environment (Raspberry Pi)
```python
# In config.py:
IS_MOCK_ENVIRONMENT = False
```

**What this does:**
- Uses `real_components.py` (requires sensors)
- Reads actual sensor data
- Runs real Audio ML inference
- Streams live USB camera video

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

## 🔐 AWS CONFIGURATION (Optional)

### Environment Variables (.env file)
```bash
# Create .env file in project root:
# AWS IoT Core (Optional)
AWS_ENDPOINT=your-endpoint.iot.region.amazonaws.com
CERT_FILE_NAME=your-certificate.pem.crt
KEY_FILE_NAME=your-private.pem.key

# DynamoDB (Optional)
ENABLE_DYNAMODB=false  # Set to true to enable cloud storage

# Flask Secret
SECRET_KEY=your-flask-secret-key
```

### MQTT Topics
```python
# In config.py:
TOPIC_TELEMETRY = "hive/telemetry"  # Sensor data
TOPIC_AUDIO = "hive/audio"          # Audio ML predictions
TOPIC_CONTROL = "hive/control"      # Toggle commands
```

**To customize:**
```python
# For multiple hives:
TOPIC_TELEMETRY = "hive/hive1/telemetry"
TOPIC_AUDIO = "hive/hive1/audio"
# etc
```

**Note:** System works with local MQTT broker (mosquitto). AWS IoT Core is optional for remote access.

---

## 📈 PERFORMANCE TUNING

### Reduce CPU Usage
```python
# Lower frequency of sensor updates:
TELEMETRY_INTERVAL_SECONDS = 10  # Instead of 5

# Reduce camera resolution (less bandwidth):
CAMERA_WIDTH = 320  # Instead of 640
CAMERA_HEIGHT = 240  # Instead of 480
CAMERA_FPS = 15     # Instead of 20
```

### Improve Audio ML Performance
```python
# Increase confidence threshold (fewer false alarms):
AUDIO_CONFIDENCE_THRESHOLD = 0.7  # Instead of 0.6

# Adjust analysis window (balance accuracy vs speed):
AUDIO_WINDOW_SECONDS = 0.5  # Faster but less context
# or
AUDIO_WINDOW_SECONDS = 2.0  # Slower but more accurate
```

### Better Audio Quality
```python
# Higher sample rate (better quality, more CPU):
MICROPHONE_SAMPLE_RATE = 48000  # Instead of 44100

# Longer frequency analysis window:
MICROPHONE_FREQ_DURATION_SEC = 2.0  # Instead of 1.0
```

---

## 🔄 MULTI-HIVE SETUP

To monitor multiple hives with one dashboard:

### 1. Edge Devices (Multiple Raspberry Pis)
```python
# Hive 1 - config.py:
THING_NAME = "SmartHive_Pi_Hive1"
TOPIC_TELEMETRY = "hive/hive1/telemetry"
TOPIC_AUDIO = "hive/hive1/audio"
TOPIC_CONTROL = "hive/hive1/control"

# Hive 2 - config.py:
THING_NAME = "SmartHive_Pi_Hive2"
TOPIC_TELEMETRY = "hive/hive2/telemetry"
TOPIC_AUDIO = "hive/hive2/audio"
# ... etc
```

### 2. Dashboard (Single Instance)
```python
# Subscribe to all hives:
client.subscribe("hive/+/telemetry")  # + is wildcard
client.subscribe("hive/+/audio")
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

### MQTT Connection Failed?
```bash
# Check mosquitto broker:
docker ps | grep mosquitto

# Test local MQTT:
docker exec -it mosquitto mosquitto_sub -t "hive/#" -v

# If using AWS IoT Core:
# Verify certificates exist:
ls certs/

# Check permissions:
chmod 644 certs/*.pem.crt
chmod 600 certs/*.pem.key
```

### Audio ML Not Working?
```bash
# Check audio model exists:
ls models/audio_model_pipeline.pkl

# Verify audio ML container:
docker logs smart-hive-audio -f

# Check microphone:
docker exec smart-hive-edge arecord -l
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
AUDIO_CONFIDENCE_THRESHOLD = 0.5  # More sensitive for testing
```

### For Testing (Raspberry Pi):
```python
IS_MOCK_ENVIRONMENT = False
TELEMETRY_INTERVAL_SECONDS = 10
AUDIO_CONFIDENCE_THRESHOLD = 0.6
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
```

### For Production (Deployed):
```python
IS_MOCK_ENVIRONMENT = False
TELEMETRY_INTERVAL_SECONDS = 30
AUDIO_CONFIDENCE_THRESHOLD = 0.7  # Reduce false alarms
CAMERA_FPS = 15  # Lower bandwidth
```

### For Research/Data Collection:
```python
IS_MOCK_ENVIRONMENT = False
TELEMETRY_INTERVAL_SECONDS = 1  # High frequency
AUDIO_CONFIDENCE_THRESHOLD = 0.5
ENABLE_DYNAMODB = true  # Store all data
# ⚠️ Warning: Generates LOTS of data!
```

---

## 💡 PRO TIPS

1. **Start with longer intervals**, then decrease as needed
2. **Calibrate thresholds** after collecting baseline data (run for 1 week)
3. **Use mock mode** for UI development and testing
4. **Test Audio ML confidence** - start at 0.5, increase if too many false alarms
5. **Monitor CPU usage** on Raspberry Pi, adjust intervals if needed
6. **Keep backup** of working `config.py`
7. **Document changes** to thresholds in your thesis

---

Need to change something? All key parameters are in these files:
- `config.py` - Hardware, timing, and Audio ML settings
- `dashboard/static/app.js` - Thresholds and alerts
- `.env` - AWS credentials (optional)
- `models/audio_model_pipeline.pkl` - Audio ML model (retrain if needed)

For more details, see:
- **Audio ML Training:** `../AUDIO_ML_GUIDE.md`
- **Camera Setup:** `../USB_CAMERA_TROUBLESHOOTING.md`
- **Deployment:** `DEPLOYMENT.md`
- **Troubleshooting:** `../DOCUMENTATION_INDEX.md`

Happy beekeeping! 🐝
