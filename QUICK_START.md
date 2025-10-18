# 🚀 Quick Start: Building Containers on Raspberry Pi

## ✅ Files Ready to Transfer to Pi

All necessary files are now ready in this repository:

```
✅ Dockerfile.edge           (878 bytes)
✅ Dockerfile.dashboard      (515 bytes) 
✅ Dockerfile.vision         (764 bytes) - NEW
✅ Dockerfile.audio          (726 bytes) - NEW
✅ docker-compose.yml
✅ requirements-edge.txt
✅ requirements-dashboard.txt
✅ requirements-vision.txt
✅ requirements-audio.txt
✅ All Python service files
```

---

## 🎯 Next Steps on Your Raspberry Pi

### 1️⃣ Pull Latest Code

```bash
ssh pi@192.168.88.16
cd ~/smart-hive-ai
git pull origin main
```

### 2️⃣ Verify New Dockerfiles Exist

```bash
ls -la Dockerfile.*
# Should show all 4 files including the NEW vision and audio Dockerfiles
```

### 3️⃣ Build All Containers

```bash
# Quick build (all at once - 40-55 minutes total)
docker-compose build --no-cache

# Or build one by one (recommended for debugging)
docker-compose build --no-cache dashboard          # 3-5 min
docker-compose build --no-cache edge-app           # 10-15 min
docker-compose build --no-cache smart-hive-vision  # 15-20 min
docker-compose build --no-cache smart-hive-audio   # 10-15 min
```

### 4️⃣ Start Everything

```bash
docker-compose up -d
docker-compose ps
```

### 5️⃣ Verify Services

```bash
docker logs smart-hive-audio --tail 20
# Look for: "AudioProcessor imported successfully"
# Look for: "librosa version: 0.10.0"

docker logs smart-hive-vision --tail 20
# Look for: "YOLO model loaded"

docker logs smart-hive-edge --tail 20  
# Look for: "Camera initialized successfully"
```

---

## 🎧 Monitoring Audio ML Processing in Real-Time

### Watch Audio Processing Logs Live

```bash
# Follow audio service logs in real-time (recommended)
docker logs -f smart-hive-audio

# Or with timestamps
docker logs -f --timestamps smart-hive-audio
```

### What You'll See When Audio is Being Processed

#### 1️⃣ **When Recording Starts**
```
🎤 Recording requested: 60 seconds
🎙️  Starting 60s recording...
🎙️  Recording for 60 seconds at 22050Hz...
```

#### 2️⃣ **During Windowed Inference**
```
✅ Recording complete: 1323000 samples
Using windowed inference (recommended)
Created 119 windows from 1323000 samples
Extracted features from 119 windows
Feature selection: 60 features selected
Features scaled
```

#### 3️⃣ **After Classification**
```
Windowed classification: queen_present (confidence: 0.873)
✅ Audio results published: queen_present
```

#### 4️⃣ **Error Messages to Watch For**
```
❌ Recording failed: [Errno -9996] Invalid input device
⚠️  AudioProcessor import failed
❌ Feature extraction failed
❌ Model not found: models/audio_model.pkl
```

### Advanced Monitoring Commands

```bash
# View last 50 lines
docker logs smart-hive-audio --tail 50

# Search for specific events
docker logs smart-hive-audio | grep "Recording requested"
docker logs smart-hive-audio | grep "queen_present"
docker logs smart-hive-audio | grep "confidence"
docker logs smart-hive-audio | grep "❌"  # Find errors
docker logs smart-hive-audio | grep "⚠️"   # Find warnings

# Watch for processing completion
docker logs -f smart-hive-audio | grep -E "(Recording complete|classification)"

# Monitor all services at once
docker-compose logs -f

# Monitor only audio and dashboard
docker-compose logs -f smart-hive-audio dashboard
```

### Trigger Audio Recording from Dashboard

1. **Open Dashboard**: http://192.168.88.16:5000
2. **Click**: "🎤 Record 1 Minute & Analyze" button
3. **Watch logs**: In terminal running `docker logs -f smart-hive-audio`
4. **See Results**: After ~65 seconds, dashboard shows classification

### Example Complete Log Sequence

```log
INFO:__main__:📨 Control message: hive/audio/control = {"command": "record_and_classify", "duration_sec": 60}
INFO:__main__:🎤 Recording requested: 60 seconds
INFO:ml_audio_model.audio_processor:🎙️  Recording for 60 seconds at 22050Hz...
INFO:ml_audio_model.audio_processor:✅ Recording complete: 1323000 samples
INFO:ml_audio_model.audio_processor:Using windowed inference (recommended)
DEBUG:ml_audio_model.audio_processor:Created 119 windows from 1323000 samples
INFO:ml_audio_model.audio_processor:Extracted features from 119 windows
DEBUG:ml_audio_model.audio_processor:Feature selection: 60 features selected
DEBUG:ml_audio_model.audio_processor:Features scaled
INFO:ml_audio_model.audio_processor:Windowed classification: queen_present (confidence: 0.873)
INFO:__main__:✅ Audio results published: queen_present
```

### Debugging Audio Issues

```bash
# Check if audio service is running
docker ps | grep audio

# Check if microphone is detected (inside container)
docker exec -it smart-hive-audio python -c "import sounddevice as sd; print(sd.query_devices())"

# Check if model file exists
docker exec -it smart-hive-audio ls -lh models/audio_model.pkl

# Check librosa installation
docker exec -it smart-hive-audio python -c "import librosa; print(f'librosa {librosa.__version__}')"

# Check full service status
docker inspect smart-hive-audio | grep -A 10 State
```

### Save Logs to File

```bash
# Save current logs
docker logs smart-hive-audio > audio_logs_$(date +%Y%m%d_%H%M%S).txt

# Save logs with timestamps
docker logs --timestamps smart-hive-audio > audio_logs_detailed.txt

# Continuous log recording
docker logs -f smart-hive-audio | tee audio_live_$(date +%Y%m%d_%H%M%S).log
```

---

## 📚 Full Documentation

See `BUILD_CONTAINERS_GUIDE.md` for:
- Detailed step-by-step instructions
- Troubleshooting guide
- Verification checklist
- Expected output examples

---

## ⚡ Ultra Quick Command (Expert Mode)

If you're confident everything is set up:

```bash
cd ~/smart-hive-ai
git pull origin main
docker-compose down
docker builder prune -af
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f
```

Done! 🎉
