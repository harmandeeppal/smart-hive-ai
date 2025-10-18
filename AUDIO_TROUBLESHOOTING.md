# 🔧 Audio ML Troubleshooting Guide

## Common Issues and Solutions

### ❌ Issue 1: Invalid Sample Rate Error

**Error Message**:
```
ERROR: ❌ Recording failed: Error opening InputStream: Invalid sample rate [PaErrorCode -9997]
```

**Problem**: Your microphone doesn't support 22050 Hz sample rate.

**Solution**: The updated code now automatically:
1. Detects supported sample rates (tries 22050, 44100, 48000, 16000 Hz)
2. Records at the highest supported rate
3. Automatically resamples to 22050 Hz for ML model

**What Changed**:
- `ml_audio_model/audio_processor.py` now includes automatic sample rate detection
- Uses `librosa.resample()` to convert to required 22050 Hz
- No manual intervention needed!

---

### ⚠️ Issue 2: scikit-learn Version Warning

**Warning Message**:
```
InconsistentVersionWarning: Trying to unpickle estimator from version 1.7.2 when using version 1.3.2
```

**Problem**: Model was trained with sklearn 1.7.2, but container has 1.3.2.

**Impact**: 
- ⚠️ **WARNING ONLY** - Not an error
- Model still works correctly
- Predictions are valid

**Solutions**:

#### Option A: Ignore (Recommended for now)
- Model works fine despite warning
- No action needed
- Test to verify accuracy

#### Option B: Upgrade scikit-learn (If issues arise)
```bash
# Edit requirements-audio.txt
scikit-learn==1.7.2  # Change from 1.3.2

# Rebuild container
docker-compose build --no-cache smart-hive-audio
docker-compose up -d smart-hive-audio
```

**Note**: sklearn 1.7.2 requires newer dependencies that may not be available on ARM yet.

---

### 🎤 Issue 3: Microphone Not Detected

**Error Message**:
```
ERROR: ❌ Recording failed: No input device found
```

**Diagnosis Commands**:
```bash
# Check if microphone is connected
lsusb | grep -i audio

# List audio devices
arecord -l

# Check from inside container
docker exec -it smart-hive-audio python -c "import sounddevice as sd; print(sd.query_devices())"
```

**Solutions**:

1. **Check USB Connection**:
   ```bash
   lsusb
   # Should show: Samson Technologies Corp. Meteorite Mic
   ```

2. **Check ALSA recognizes it**:
   ```bash
   arecord -l
   # Should show: card 1: Mic [Samson Meteorite Mic]
   ```

3. **Grant Docker Audio Access**:
   
   In `docker-compose.yml`:
   ```yaml
   smart-hive-audio:
     devices:
       - /dev/snd:/dev/snd  # ✅ Already configured
     group_add:
       - audio              # ✅ Already configured
   ```

4. **Test Recording Manually**:
   ```bash
   # Record 5-second test
   arecord -D hw:1,0 -f S16_LE -r 44100 -d 5 test.wav
   
   # Play it back
   aplay test.wav
   ```

---

### 📊 Issue 4: Low Audio Quality / Poor Classification

**Symptoms**:
- Audio recorded but classification wrong
- Low confidence scores
- Inconsistent results

**Diagnosis**:
```bash
# Check microphone volume/gain
alsamixer
# Press F6, select Samson Meteorite
# Adjust capture volume to 80-90%

# Test recording quality
docker exec -it smart-hive-audio python -c "
import sounddevice as sd
import numpy as np
rec = sd.rec(5*44100, samplerate=44100, channels=1)
sd.wait()
print(f'Audio level: {np.abs(rec).mean():.4f}')
print(f'Max amplitude: {np.abs(rec).max():.4f}')
"
```

**Expected Values**:
- Audio level: 0.01 - 0.3 (good)
- Max amplitude: 0.1 - 0.9 (good)
- If too low (<0.001): Increase microphone gain
- If clipping (>0.95): Reduce microphone gain

**Solutions**:

1. **Adjust Microphone Gain**:
   ```bash
   alsamixer
   # F6 → Select Samson Meteorite
   # Arrow keys to adjust capture volume
   # ESC to exit
   ```

2. **Position Microphone Correctly**:
   - 10-20 cm from hive entrance
   - Avoid wind/vibration
   - Point toward bee activity

3. **Check Ambient Noise**:
   - Record during quiet period
   - Check for electrical interference
   - Verify hive has active bees

---

### 🔌 Issue 5: MQTT Connection Failed

**Error Message**:
```
ERROR: ❌ MQTT connection failed: Connection refused
```

**Solutions**:

1. **Check Mosquitto is Running**:
   ```bash
   docker ps | grep mosquitto
   # Should show: mosquitto container running
   ```

2. **Restart Mosquitto**:
   ```bash
   docker-compose restart mosquitto
   docker logs mosquitto --tail 20
   ```

3. **Check Network**:
   ```bash
   docker network ls | grep smart-hive
   docker network inspect smart-hive-ai_default
   ```

---

### 💾 Issue 6: Model File Not Found

**Error Message**:
```
ERROR: ❌ Model not found: models/audio_model.pkl
```

**Solutions**:

1. **Check Model Exists**:
   ```bash
   ls -lh models/audio_model.pkl
   # Should show: ~15.8 MB file
   ```

2. **Check Inside Container**:
   ```bash
   docker exec -it smart-hive-audio ls -lh models/audio_model.pkl
   ```

3. **Rebuild Container**:
   ```bash
   docker-compose build --no-cache smart-hive-audio
   docker-compose up -d smart-hive-audio
   ```

---

## Testing Audio System

### Quick Test Script

```bash
# SSH to Raspberry Pi
ssh pi@192.168.88.16

# Run comprehensive test
docker exec -it smart-hive-audio python << 'EOF'
import sounddevice as sd
import numpy as np

print("=" * 60)
print("Audio System Test")
print("=" * 60)

# 1. List devices
print("\n1. Available Audio Devices:")
print(sd.query_devices())

# 2. Test recording
print("\n2. Testing 5-second recording...")
try:
    audio = sd.rec(5*44100, samplerate=44100, channels=1)
    sd.wait()
    print(f"   ✅ Recording successful")
    print(f"   Audio level: {np.abs(audio).mean():.4f}")
    print(f"   Max amplitude: {np.abs(audio).max():.4f}")
except Exception as e:
    print(f"   ❌ Recording failed: {e}")

# 3. Check librosa
print("\n3. Checking librosa...")
try:
    import librosa
    print(f"   ✅ librosa version: {librosa.__version__}")
except Exception as e:
    print(f"   ❌ librosa import failed: {e}")

# 4. Check model
print("\n4. Checking model file...")
import os
if os.path.exists('models/audio_model.pkl'):
    size = os.path.getsize('models/audio_model.pkl') / (1024*1024)
    print(f"   ✅ Model found: {size:.1f} MB")
else:
    print(f"   ❌ Model not found")

print("=" * 60)
EOF
```

### Expected Output

```
============================================================
Audio System Test
============================================================

1. Available Audio Devices:
  0 bcm2835 Headphones: - (hw:0,0), ALSA (0 in, 8 out)
> 1 Samson Meteorite Mic: USB Audio (hw:1,0), ALSA (1 in, 0 out)

2. Testing 5-second recording...
   ✅ Recording successful
   Audio level: 0.0234
   Max amplitude: 0.4521

3. Checking librosa...
   ✅ librosa version: 0.10.1

4. Checking model file...
   ✅ Model found: 15.8 MB
============================================================
```

---

## Real-Time Monitoring

### Monitor During Recording

```bash
# Terminal 1: Follow logs
docker logs -f smart-hive-audio

# Terminal 2: Watch resource usage
docker stats smart-hive-audio

# Terminal 3: Monitor audio levels (if needed)
alsamixer
```

### Logs to Watch For

**✅ Success Indicators**:
```
✅ AudioProcessor imported successfully
✅ Audio model pipeline loaded successfully
✅ Audio processor initialized with windowed inference
✅ MQTT connected successfully
📱 Using microphone: Samson Meteorite Mic
⏺ Recording for 60 seconds at 44100Hz...
✅ Recording complete (2646000 samples at 44100Hz)
🔄 Resampling from 44100Hz to 22050Hz...
✅ Resampled to 1323000 samples at 22050Hz
Using windowed inference (recommended)
Created 119 windows from 1323000 samples
Extracted features from 119 windows
Windowed classification: queen_present (confidence: 0.873)
✅ Audio results published: queen_present
```

**❌ Error Indicators**:
```
❌ Recording failed: Invalid sample rate
❌ Feature extraction failed
❌ Model not found
❌ MQTT connection failed
⚠️  AudioProcessor import failed
```

---

## Performance Expectations

| Metric | Expected Value | Notes |
|--------|---------------|-------|
| **Recording Time** | 60 seconds | User configurable |
| **Processing Time** | 3-8 seconds | Depends on Pi model |
| **Total Time** | ~65-68 seconds | Recording + processing |
| **Memory Usage** | 150-250 MB | Container peak |
| **CPU Usage** | 20-40% | During processing |
| **Confidence (Good)** | 0.7 - 0.95 | High confidence |
| **Confidence (Poor)** | 0.5 - 0.7 | Uncertain |
| **Sample Rate** | 22050 Hz | After resampling |
| **Windows Created** | 119 | From 60s recording |

---

## Getting Help

### Debug Information to Collect

When reporting issues, include:

1. **System Info**:
   ```bash
   uname -a
   cat /etc/os-release
   docker --version
   ```

2. **Container Logs**:
   ```bash
   docker logs smart-hive-audio > audio_logs.txt
   ```

3. **Audio Devices**:
   ```bash
   lsusb | grep -i audio
   arecord -l
   docker exec smart-hive-audio python -c "import sounddevice; print(sounddevice.query_devices())"
   ```

4. **Model Info**:
   ```bash
   ls -lh models/
   docker exec smart-hive-audio ls -lh models/
   ```

5. **Docker Compose Config**:
   ```bash
   cat docker-compose.yml | grep -A 20 smart-hive-audio
   ```

---

## Next Steps After Fix

1. **Pull Updated Code**:
   ```bash
   cd ~/smart-hive-ai
   git pull origin feature/audio-windowed-inference
   ```

2. **Rebuild Container**:
   ```bash
   docker-compose build --no-cache smart-hive-audio
   ```

3. **Restart Service**:
   ```bash
   docker-compose up -d smart-hive-audio
   ```

4. **Test Recording**:
   - Open dashboard: http://192.168.88.16:5000
   - Click "🎤 Record 1 Minute & Analyze"
   - Watch logs: `docker logs -f smart-hive-audio`

5. **Verify Results**:
   - Should see successful recording at 44100 Hz
   - Should see automatic resampling to 22050 Hz
   - Should see classification with confidence score

---

**Last Updated**: October 19, 2025  
**Branch**: feature/audio-windowed-inference  
**Status**: Ready for testing with auto-resampling
