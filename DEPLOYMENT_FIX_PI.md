# Raspberry Pi Deployment - Two Critical Fixes

## Summary of Issues Fixed

### Issue 1: YOLO Model Loading Failure ❌ → ✅
**Root Cause**: YOLO calls `git` during model initialization for version info, but git wasn't installed in Docker
**Fix**: Added `git` to apt-get in both Dockerfile.ml and Dockerfile.vision
**Commit**: `fc2ba89`

### Issue 2: Dashboard Port 5000 Inaccessible ❌ → ✅
**Root Cause**: Dashboard was trying to connect to AWS IoT Core instead of local Mosquitto broker, causing crashes
**Fix**: Changed MQTT connection to use local Mosquitto broker (mosquitto:1883) with proper error handling
**Commit**: `1a13e4f`

---

## Steps to Deploy on Raspberry Pi

### Step 1: Pull Latest Changes
```bash
cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization
```

**Expected Output**:
```
From https://github.com/harmandeeppal/smart-hive-ai
   1a13e4f..HEAD   feature/project-cleanup-and-ml-reorganization -> origin/feature/project-cleanup-and-ml-reorganization
Updating 1a13e4f..XXXXX
```

---

### Step 2: Stop and Remove Old Containers
```bash
docker compose down
```

---

### Step 3: Rebuild ALL Containers (Fresh Build)
```bash
docker compose build --no-cache
```

**This will rebuild**:
- ✅ mosquitto (MQTT broker)
- ✅ smart-hive-edge (camera frame publishing)
- ✅ smart-hive-vision (with git installed ✅)
- ✅ smart-hive-audio
- ✅ smart-hive-dashboard (with local Mosquitto connection ✅)

**Expected**: Each image builds successfully with "Successfully tagged..."

---

### Step 4: Start All Containers
```bash
docker compose up -d
```

**Expected Output**:
```
Creating smart-hive-mosquitto ... done
Creating smart-hive-edge ... done
Creating smart-hive-vision ... done
Creating smart-hive-audio ... done
Creating smart-hive-dashboard ... done
```

---

### Step 5: Verify Containers Are Running
```bash
docker ps
```

**Expected Output** (all should show "Up"):
```
CONTAINER ID   IMAGE                        STATUS
...            eclipse-mosquitto:latest     Up ...
...            smart-hive-edge:latest       Up ...
...            smart-hive-vision:latest     Up ... (was Restarting before)
...            smart-hive-audio:latest      Up ...
...            smart-hive-dashboard:latest  Up ... (was Restarting before)
```

---

## Verification Checks

### Check 1: YOLO Model Loading
```bash
docker logs smart-hive-vision | grep -i "yolo\|model\|error" -A 2
```

**Expected Output** (should see SUCCESS, not the old "No such file or directory: git" error):
```
INFO:ml_vision_model.vision_processor:Loading YOLO model from models/vision_model.pt
✅ Model loaded successfully
```

**If still fails**, run:
```bash
docker logs smart-hive-vision | tail -50
```

---

### Check 2: Dashboard Running
```bash
docker logs smart-hive-dashboard | grep -i "mqtt\|connecting\|error" -A 2
```

**Expected Output** (should see Mosquitto connection, NOT AWS_ENDPOINT error):
```
Setting up MQTT client...
Connecting to MQTT broker at mosquitto:1883
✅ MQTT client started successfully
INFO:__main__:Starting Flask-SocketIO server...
```

**If still fails**, run:
```bash
docker logs smart-hive-dashboard | tail -50
```

---

### Check 3: Dashboard Accessibility (from your computer)
```
Open browser: http://192.168.88.16:5000
```

**Expected**: Dashboard web page loads (you should see the dashboard interface)

---

## If Containers Still Fail

### Nuclear Option: Deep Rebuild
```bash
# Stop everything
docker compose down

# Remove dangling images
docker image prune -f

# Full rebuild with verbose output
docker compose build --no-cache --progress=plain

# Start and watch logs
docker compose up -d
sleep 10
docker compose logs -f
```

---

### Troubleshooting

**Vision service keeps restarting?**
```bash
docker logs smart-hive-vision | tail -100
```
Look for any error related to YOLO or model loading.

**Dashboard keeps restarting?**
```bash
docker logs smart-hive-dashboard | tail -100
```
Should NOT see "Invalid host" or AWS_ENDPOINT errors anymore.

**MQTT connection failing?**
```bash
# Check if Mosquitto is running
docker logs mosquitto | tail -20

# Should see:
# 1633027600: mosquitto version 2.x.x starting
# 1633027600: Using default config
# 1633027600: Listener on 0.0.0.0:1883
```

---

## Success Criteria ✅

All of these should be true:

1. ✅ `docker ps` shows all containers with status "Up"
2. ✅ `docker logs smart-hive-vision` shows "Model loaded successfully" (or at least no git error)
3. ✅ `docker logs smart-hive-dashboard` shows "MQTT client started successfully"
4. ✅ http://192.168.88.16:5000 is accessible from your computer
5. ✅ No containers in "Restarting" state

---

## Next Steps After Deployment

Once all containers are running:

1. Monitor frame publishing:
   ```bash
   docker logs smart-hive-edge | grep -i "publishing\|frame\|mqtt"
   ```

2. Monitor frame reception:
   ```bash
   docker logs smart-hive-vision | grep -i "frame\|received\|inference"
   ```

3. Monitor dashboard data:
   ```bash
   docker logs smart-hive-dashboard | grep -i "received\|update\|telemetry"
   ```

---

## Commits Applied

| Commit | Description |
|--------|-------------|
| fc2ba89 | fix: Add git to Docker containers for YOLO model loading |
| 1a13e4f | fix: Dashboard MQTT connection to local Mosquitto broker |

---

Generated: October 18, 2025
