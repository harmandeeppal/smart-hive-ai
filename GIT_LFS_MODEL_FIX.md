# 🎯 URGENT: Git LFS Model File Solution

## The Root Cause

The `models/vision_model.pt` file is tracked with Git LFS, but Git LFS on the Pi either:
1. Wasn't pulled correctly
2. Exists as a text stub (100 bytes) instead of the real model (100MB+)
3. Needs to be force-checked out

When Docker mounts `./models:/app/models:ro` to the container, it mounts the stub instead of the real file.

---

## SOLUTION: Verify & Force Git LFS on Pi

Run these commands **on the Raspberry Pi** in order:

```bash
cd ~/smart-hive-ai

# 1. Check the current status of the model file
echo "=== Model File Status ===" 
file models/vision_model.pt
ls -lh models/vision_model.pt
head -c 200 models/vision_model.pt | cat -v

# Output should show:
# If REAL model: "data" or "PyTorch" → should be 100MB+
# If STUB: "ASCII text" → should be ~100 bytes

# 2. If it's still a stub, force Git LFS to get the real file
if [ $(wc -c < models/vision_model.pt) -lt 1000 ]; then
    echo "❌ File is still a Git LFS stub, downloading real file..."
    git lfs pull --force
    git lfs checkout --force
    ls -lh models/vision_model.pt
    echo "✅ Should now be 100MB+"
else
    echo "✅ File is already real ($(du -h models/vision_model.pt | cut -f1))"
fi

# 3. Verify file is correct
md5sum models/vision_model.pt
# Note this hash for verification
```

---

## Then Rebuild Docker

Once the model file is confirmed REAL on Pi (not a stub):

```bash
# Fresh rebuild with the real model file
docker compose build --no-cache smart-hive-vision

# Restart service
docker compose restart smart-hive-vision
sleep 5

# Check if model loaded
docker logs smart-hive-vision | grep -i "model\|yolo\|loaded"
# Should show: "✅ YOLO model loaded successfully"
```

---

## If Git LFS Still Fails (Workaround Options)

### Option A: Copy Model Directly (If You Have SSH Access)

On your Windows machine, copy the model to the Pi via SCP:

```bash
# From Windows (PowerShell):
scp C:\Users\harma\OneDrive\ -\ AUT\ University\IDE_Workspace\aut_projects\smart-hive-ai\models\vision_model.pt pi@raspberrypi:~/smart-hive-ai/models/
```

### Option B: Download from Hugging Face/Release (If Published)

If the model is published online, download directly on Pi:

```bash
cd ~/smart-hive-ai/models
# Example (replace with actual URL):
# curl -L "https://github.com/harmandeeppal/smart-hive-ai/releases/download/v1.0/vision_model.pt" -o vision_model.pt
```

### Option C: Temporarily Disable Model Requirement (Test Option A Without Model)

The vision service **CAN run without the model** - it will still receive MQTT frames and process them (just without YOLO inference). This lets us verify the frame flow works:

```bash
# Vision service will log: "Vision model will be disabled"
# But MQTT communication will work
# This proves Option A architecture is sound

docker compose restart smart-hive-vision
sleep 5
docker logs smart-hive-vision | tail -5
```

---

## Verification: Model File Size Check

Run this to verify your model file status:

```bash
# On Pi:
ls -lh ~/smart-hive-ai/models/vision_model.pt

# Expected for REAL file: 100M+ 
# Examples:
# -rw-r--r-- 1 pi pi 123M Oct 18 12:34 vision_model.pt ✅ REAL
# -rw-r--r-- 1 pi pi 131 Oct 18 12:34 vision_model.pt ❌ STUB
```

---

## Quick Status Check

```bash
cd ~/smart-hive-ai && \
echo "=== Git LFS Status ===" && \
git lfs version && \
echo "=== Model File ===" && \
file models/vision_model.pt && \
ls -lh models/vision_model.pt && \
echo "=== First 100 bytes ===" && \
head -c 100 models/vision_model.pt && \
echo -e "\n=== File Type ===" && \
hexdump -C models/vision_model.pt | head -3
```

**Key indicator**: If output shows `version: 0.0.0` for git lfs version, Git LFS isn't installed. If model file is 131 bytes and contains "version https://git-lfs.github.com/spec", it's a stub.

---

## RECOMMENDED PATH FORWARD

1. **First**, run the model file status check
2. **If stub**, try `git lfs pull --force && git lfs checkout --force`
3. **If that fails**, use SCP to copy from Windows machine
4. **Once real file exists on Pi**, rebuild Docker
5. **Vision service should then load YOLO successfully**

This **is not** a blocker for testing Option A architecture - the MQTT frame flow works without YOLO. The model loading is just the final optimization.

---

## What Gets Fixed

Once model file is real:
- ✅ Vision service starts
- ✅ YOLO model loads (5-10 seconds)  
- ✅ Frame inference runs
- ✅ Detection results published to MQTT
- ✅ Option A fully complete!

Current status without model fix:
- ✅ Edge-app publishing frames to MQTT
- ✅ Vision service receiving frames (no errors)
- ✅ MQTT communication working
- ❌ YOLO inference disabled (but could enable in future)
