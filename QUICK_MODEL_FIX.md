# 🔧 Quick Model File Fix for Raspberry Pi

## The Problem
The vision model file (`models/vision_model.pt`) is being tracked with Git LFS, but Git LFS hasn't been pulled on the Pi. When Docker tries to build the image, the file either doesn't exist or is just a text stub, so `COPY models/vision_model.pt ./models/` fails.

## The Solution (2 Steps)

### Step 1: Pull Model File with Git LFS on Pi
```bash
cd ~/smart-hive-ai

# Install Git LFS
sudo apt-get install -y git-lfs

# Initialize Git LFS
git lfs install

# Pull the actual model files
git lfs pull

# Verify the file is now real (not a stub)
ls -lh models/vision_model.pt
# Should show: 100M or similar (large file)
# NOT: 100 bytes (text stub)

# Make sure file is checked out
git lfs checkout
```

### Step 2: Rebuild Docker Image
```bash
# Rebuild the vision service image to copy the model
docker compose build --no-cache smart-hive-vision

# This will now successfully copy models/vision_model.pt into the image
```

### Step 3: Restart Vision Service
```bash
docker compose restart smart-hive-vision

# Wait 30 seconds and check logs
sleep 5
docker logs smart-hive-vision | tail -20
# Should now show: "✅ Model loaded successfully"
# NOT: "❌ Model file not found"
```

## Verify It Worked

```bash
# Check vision service is healthy
docker compose ps smart-hive-vision
# Should show: "Up (healthy)" after ~30 seconds

# Check model loaded in logs
docker logs smart-hive-vision | grep -i "model loaded\|yolo"
# Should show YOLO model loading successfully
```

## What This Will Enable

Once the model is in place:

✅ Vision service can process frames received from MQTT  
✅ YOLO inference will run on each frame  
✅ Detection results will be published to `hive/vision/results`  
✅ Frame flow: Edge-App → MQTT → Vision Service → Results  

## Quick Command Bundle

Copy-paste this entire block to run all steps:

```bash
cd ~/smart-hive-ai && \
sudo apt-get install -y git-lfs && \
git lfs install && \
git lfs pull && \
git lfs checkout && \
ls -lh models/vision_model.pt && \
docker compose build --no-cache smart-hive-vision && \
docker compose restart smart-hive-vision && \
sleep 5 && \
echo "=== Vision Service Logs ===" && \
docker logs smart-hive-vision | tail -20
```

---

## Alternative: If Git LFS Still Doesn't Work

If Git LFS pulls but still shows stubs, try this:

```bash
# Force fresh checkout
cd ~/smart-hive-ai
git lfs uninstall
git lfs install
rm -rf .git/lfs
git lfs pull --force
git lfs checkout --force
```

Then rebuild Docker:
```bash
docker compose build --no-cache smart-hive-vision
```

---

## Troubleshooting

**Q: Still seeing "Model file not found" after rebuild?**

A: Verify the model is really in the image:
```bash
docker exec smart-hive-vision ls -lh /app/models/
# Should show: vision_model.pt (not a text stub)
```

**Q: Model loads but vision service says "Unhealthy"?**

A: The health check is running YOLO import. Wait 30 seconds, then:
```bash
docker logs smart-hive-vision
# Look for "Model loaded successfully" message
```

**Q: Model file is 100 bytes (Git LFS stub)?**

A: Git LFS didn't pull it. Run this:
```bash
cd ~/smart-hive-ai
git lfs pull --force
git lfs checkout --force
file models/vision_model.pt
# Should show: "PyTorch model file" or "data"
# NOT: "ASCII text"
```

---

## Status Tracking

After this fix, you should see:

```
Edge-App Logs:
✅ 📹 Camera frame publisher started
✅ 📤 Published 45873 bytes to hive/telemetry/camera/frame (every 3 FPS)

Vision Service Logs:
✅ ✅ MQTT connected successfully
✅ 📨 Subscribed to: hive/telemetry/camera/frame
✅ 🎥 Starting vision inference loop (MQTT frames)
✅ Model loaded successfully from models/vision_model.pt

Frame Flow Test:
✅ docker exec mosquitto mosquitto_sub -t "hive/telemetry/camera/frame" -C 1 | wc -c
✅ Returns: ~45000 (actual frame bytes)
```

---

**Once this is fixed, Option A deployment is COMPLETE!** 🎉
