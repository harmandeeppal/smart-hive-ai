# Fix Audio ML Processing - Stuck on "Waiting for analysis..."

## Issue
Recording completes successfully (1 minute, 40.6 dB detected), but classification never happens. Dashboard shows:
- ✅ Waveform animating
- ✅ Sound level bars working (40.6 dB)
- ❌ Classification: "Waiting for analysis..." (stuck forever)
- ❌ Confidence: "--"
- ❌ Status: "Processing..." (never completes)

## Root Cause
Audio ML service is missing required Python packages:
- `librosa` - Audio feature extraction
- `scikit-learn` - ML model loading
- `sounddevice` - Audio recording

The service receives the recording command, records audio, but **cannot extract features or run classification** because these packages aren't installed.

---

## Fix Steps (Run on Raspberry Pi)

### Step 1: SSH to Raspberry Pi
```bash
ssh pi@192.168.88.16
cd ~/smart-hive-ai
```

### Step 2: Check Current Audio Service Status
```bash
# Find audio container name
docker ps -a | grep audio

# Check logs (replace container name if different)
docker logs smart-hive-audio 2>&1 | tail -30
```

**Expected Error:**
```
ERROR:ml_audio_model.audio_processor:❌ Required packages not installed. Install with: pip install librosa scikit-learn sounddevice
WARNING:ml_audio_model.audio_processor:Audio model will be disabled. System will continue without audio analysis.
```

### Step 3: Stop Audio Service
```bash
docker compose stop smart-hive-audio
```

### Step 4: Remove Old Container and Image
```bash
# Remove container
docker compose rm -f smart-hive-audio

# Remove old image to force fresh build
docker rmi smart-hive-audio:latest
```

### Step 5: Rebuild with No Cache (CRITICAL!)
```bash
# This will take 5-10 minutes - packages need to compile
docker compose build --no-cache smart-hive-audio
```

**What to Watch For:**
```
Step 6/12 : RUN pip install --no-cache-dir -r requirements-audio.txt
 ---> Running in abc123...
Collecting librosa==0.10.0       ← Should see this
Collecting scikit-learn==1.3.0   ← And this
Collecting sounddevice==0.4.6    ← And this
Building wheels for librosa...   ← May take several minutes
Successfully installed librosa-0.10.0 scikit-learn-1.3.0 sounddevice-0.4.6
```

**If Build Fails:**
Check if `requirements-audio.txt` has these packages:
```bash
cat requirements-audio.txt | grep -E "librosa|scikit-learn|sounddevice"
```

Should show:
```
librosa==0.10.0
scikit-learn==1.3.0
sounddevice==0.4.6
```

### Step 6: Start Audio Service
```bash
docker compose up -d smart-hive-audio
```

### Step 7: Verify Packages Installed
```bash
docker logs smart-hive-audio 2>&1 | head -30
```

**Expected SUCCESS Output:**
```
INFO:__main__:✅ AudioProcessor imported successfully
INFO:ml_audio_model.audio_processor:Loading audio model from models/audio_model.pkl
INFO:ml_audio_model.audio_processor:✅ Audio model loaded successfully
INFO:ml_audio_model.audio_processor:Model expects 13 MFCC features
INFO:__main__:✅ Audio processor initialized
INFO:__main__:Connecting to local MQTT broker: mosquitto:1883
INFO:__main__:✅ MQTT connected to mosquitto:1883
INFO:__main__:🎤 Audio service ready (on-demand recording mode)
```

**Key Success Indicators:**
- ✅ "Audio model loaded successfully" (NOT "packages not installed")
- ✅ "Model expects 13 MFCC features" (model initialized)
- ✅ No ERROR or WARNING messages

### Step 8: Test Recording and Classification
```bash
# Trigger a quick 5-second test
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'

# Watch logs in real-time
docker logs -f smart-hive-audio
```

**Expected Output (WORKING!):**
```
📨 Control message: hive/audio/control = {"command": "record_and_classify", "duration_sec": 5}
🎤 Recording requested: 5 seconds
🎙️  Starting 5s recording...
Recording from Samson Meteorite Mic (card 1, device 0)
✅ Audio recorded: 5.0 seconds
✅ Audio features extracted: (5.0s, 13 MFCCs)           ← NEW! Feature extraction working
✅ Classification: queen_present (confidence: 0.87)     ← NEW! ML model working!
✅ Audio results published to: hive/audio/results       ← NEW! Results sent to dashboard
```

Press `Ctrl+C` to stop following logs.

---

## Dashboard Test

### Test 1: Click Recording Button
1. Open dashboard: http://192.168.88.16:5000
2. Click "🎤 Record 1 Minute & Analyze"
3. Wait 60 seconds (watch progress bar)
4. **After 60 seconds, you should see:**
   - Classification: "Queen Present" or "Queen Absent" (GREEN or RED text)
   - Confidence: "87.5%" (example)
   - Status: "✅ Completed"

### Test 2: Verify MQTT Message
```bash
# Subscribe to results topic
docker exec mosquitto mosquitto_sub -t 'hive/audio/results' -C 1
```

**Expected:**
```json
{
  "classification": "queen_present",
  "confidence": 0.873,
  "timestamp": "2025-10-19T10:30:45.123456"
}
```

---

## Troubleshooting

### Issue 1: Build Fails with "No space left on device"

**Solution:**
```bash
# Clean up old images
docker system prune -a --volumes

# Try build again
docker compose build --no-cache smart-hive-audio
```

### Issue 2: Build Fails with "unable to prepare context"

**Solution:**
```bash
# Check if .dockerignore is blocking requirements file
cat .dockerignore | grep requirements

# If it shows "requirements-audio.txt", remove that line:
nano .dockerignore
# Remove or comment out: requirements-audio.txt

# Try build again
docker compose build --no-cache smart-hive-audio
```

### Issue 3: Packages Install But Model Fails to Load

**Solution:**
```bash
# Verify model file exists and is readable
ls -lh models/audio_model.pkl

# Should show: -rw-rw-r-- 1 pi pi 16M Oct 18 01:49 models/audio_model.pkl

# If file is missing or corrupted, you'll need to retrain or restore the model
```

### Issue 4: Recording Works But Classification Returns "unknown"

**Check:**
```bash
# Verify model actually loaded
docker logs smart-hive-audio 2>&1 | grep "Audio model loaded"

# If it says "Audio model will be disabled", packages still not installed
# Go back to Step 5 and rebuild with --no-cache
```

### Issue 5: Dashboard Still Shows "Waiting for analysis..."

**Possible Causes:**

1. **Audio service not publishing results**
   ```bash
   # Check MQTT traffic
   docker exec mosquitto mosquitto_sub -t 'hive/audio/#' -v
   
   # Trigger recording
   docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'
   
   # You should see:
   # hive/audio/control {"command":"record_and_classify","duration_sec":5}
   # hive/audio/results {"classification":"queen_present","confidence":0.87,...}
   ```

2. **Dashboard not subscribed to results topic**
   ```bash
   # Check dashboard logs
   docker logs smart-hive-dashboard --tail 20
   
   # Should see: "Subscribed to: hive/audio/results"
   ```

3. **JavaScript error in dashboard**
   - Open browser console (F12)
   - Look for errors related to "audio" or "classification"
   - Share error message for debugging

---

## Expected Timeline

| Step | Duration | Description |
|------|----------|-------------|
| Stop/Remove containers | 30 seconds | Clean old containers |
| Build --no-cache | 8-12 minutes | Install packages (librosa takes time) |
| Start container | 10 seconds | Launch audio service |
| Verify logs | 10 seconds | Check successful startup |
| Test recording | 5-10 seconds | Quick classification test |
| **Total** | **10-15 minutes** | Full fix deployment |

---

## Success Criteria

✅ **Audio ML service fully working when:**

1. **Logs show:**
   ```
   ✅ Audio model loaded successfully
   Model expects 13 MFCC features
   ```

2. **Test recording shows:**
   ```
   ✅ Audio features extracted: (5.0s, 13 MFCCs)
   ✅ Classification: queen_present (confidence: 0.87)
   ```

3. **Dashboard displays:**
   - Classification: "Queen Present" or "Queen Absent"
   - Confidence: Percentage (e.g., "87.5%")
   - Status: "✅ Completed"
   - Text color: GREEN or RED based on classification

4. **MQTT topic shows:**
   ```bash
   docker exec mosquitto mosquitto_sub -t 'hive/audio/results' -C 1
   # Returns JSON with classification and confidence
   ```

---

## Quick Fix Commands (Copy-Paste Ready)

```bash
# Run all steps in sequence
cd ~/smart-hive-ai

# Stop and remove old audio service
docker compose stop smart-hive-audio
docker compose rm -f smart-hive-audio
docker rmi smart-hive-audio:latest

# Rebuild with no cache (takes 8-12 minutes)
echo "⏳ Building audio service (this will take 8-12 minutes)..."
docker compose build --no-cache smart-hive-audio

# Start service
docker compose up -d smart-hive-audio

# Wait 10 seconds for startup
sleep 10

# Check logs for success
echo "📋 Checking logs..."
docker logs smart-hive-audio 2>&1 | head -30

# Test classification
echo "🧪 Testing classification..."
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'

# Wait 6 seconds for recording + processing
sleep 6

# Show results
docker logs smart-hive-audio --tail 10
```

---

## After Fix - Dashboard Behavior

### What You'll See:

1. **Click "🎤 Record 1 Minute & Analyze"**
   - Button shows progress bar (fills over 60 seconds)
   - Status changes to "Recording..."

2. **After 60 seconds:**
   - Status briefly shows "Processing..."
   - Classification appears: "Queen Present" or "Queen Absent"
   - Confidence shows: "87.5%" (example)
   - Status shows: "✅ Completed"
   - Text is GREEN for queen_present, RED for queen_absent

3. **Waveform continues:**
   - Green waveform keeps animating
   - Sound level bars update with live telemetry
   - dB value shows current sound level

---

## Summary

**Problem:** Recording completes but ML classification never happens because librosa, scikit-learn, and sounddevice packages are missing.

**Solution:** Rebuild audio service container with `--no-cache` flag to force fresh package installation.

**Critical Command:**
```bash
docker compose build --no-cache smart-hive-audio
```

**Verification:**
```bash
docker logs smart-hive-audio 2>&1 | grep "Audio model loaded successfully"
# Should return: ✅ Audio model loaded successfully
```

**Test:**
```bash
docker exec mosquitto mosquitto_pub -t 'hive/audio/control' -m '{"command":"record_and_classify","duration_sec":5}'
docker logs smart-hive-audio --tail 10
# Should show: ✅ Classification: queen_present (confidence: 0.87)
```

**Time Required:** 10-15 minutes (mostly waiting for package compilation).
