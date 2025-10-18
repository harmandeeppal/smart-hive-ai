# MQTT Topic Architecture Analysis & Fix

**Date:** October 18, 2025  
**Issue:** Inconsistent MQTT control topics - dashboard can't control ML services  

---

## Current MQTT Topic Mapping

### **Telemetry & Data Flow** ✅ WORKING
| Topic | Publisher | Subscriber | Purpose | Status |
|-------|-----------|------------|---------|--------|
| `hive/telemetry` | Edge-app | Dashboard | Sensor data (temp, humidity, weight) | ✅ OK |
| `hive/telemetry/camera/frame` | Edge-app | Vision Service | JPEG frames (3 FPS) | ✅ OK |
| `hive/vision/detection` | Vision Service | Dashboard | YOLO detection results | ✅ FIXED |
| `hive/audio/classification` | Audio Service | Dashboard | Audio ML results | ✅ OK |
| `hive/audio/control` | Dashboard | Audio Service | Trigger audio recording | ✅ OK |

### **Control Topics** ❌ BROKEN
| Topic | Publisher | Subscriber | Purpose | Status |
|-------|-----------|------------|---------|--------|
| `hive/control` | Dashboard | Edge-app | Toggle sensors (temp, camera, etc.) | ✅ WORKS |
| `hive/control` | Dashboard | Vision Service | Toggle ML vision on/off | ❌ **NOT WORKING** |
| `hive/ml/control` | Nobody | Vision Service | Vision service listens here | ❌ **ORPHANED** |
| `hive/vision/enable` | Nobody | Vision Service | Vision service also listens here | ❌ **ORPHANED** |
| `hive/vision` | Nobody | Dashboard | Legacy topic, not used | ❌ **OUTDATED** |

---

## Problem Identified

**Dashboard publishes ML control to:** `hive/control`  
**Vision service listens to:** `hive/ml/control` + `hive/vision/enable`  

**Result:** Dashboard toggle buttons do NOTHING for ML services! 🔴

---

## Root Cause Analysis

**Vision Service Code** (`ml_vision_service.py` line 119-120):
```python
client.subscribe("hive/ml/control")      # ❌ Nobody publishes here!
client.subscribe("hive/vision/enable")   # ❌ Nobody publishes here!
```

**Dashboard Code** (`dashboard_app.py` line 206, 225):
```python
mqtt_client.publish("hive/control", control_payload, qos=1)  # ✅ Correct topic
```

**Edge-app listens to:** `hive/control` ✅  
**Vision service listens to:** `hive/ml/control` ❌  

---

## Solution Options

### **Option 1: Unified Control Topic** (RECOMMENDED ✅)
**Approach:** Use `hive/control` for ALL control commands (sensors + ML)

**Benefits:**
- Single control topic for entire system
- Dashboard already uses it
- Edge-app already listens to it
- Simpler architecture

**Changes Required:**
1. Vision service subscribes to `hive/control` instead of `hive/ml/control`
2. Audio service already uses `hive/audio/control` (separate, specific to audio)
3. Each service filters messages by `sensor` field

**Payload Format:**
```json
{
  "sensor": "ml_vision",    // or "temperature", "camera", etc.
  "state": "on"             // or "off"
}
```

**Updated Topic Map:**
| Topic | Publishers | Subscribers | Messages |
|-------|-----------|-------------|----------|
| `hive/control` | Dashboard | Edge-app, Vision Service | Sensor + ML toggles |
| `hive/audio/control` | Dashboard | Audio Service | Audio recording triggers |

---

### **Option 2: Separate ML Control Topic**
**Approach:** Use `hive/ml/control` for ML services only

**Benefits:**
- Clearer separation between sensors and ML
- Prevents cross-service message pollution

**Changes Required:**
1. Dashboard publishes ML toggles to `hive/ml/control`
2. Dashboard publishes sensor toggles to `hive/control`
3. Vision service keeps current subscription

**Problems:**
- Dashboard needs to know which topic to use per sensor type
- More complex routing logic

---

## Recommended Implementation (Option 1)

### **1. Update Vision Service** (`ml_vision_service.py`)

**Current Code** (lines 117-120):
```python
client.subscribe(config.TOPIC_CAMERA_FRAME)
logger.info(f"📨 Subscribed to: {config.TOPIC_CAMERA_FRAME}")
client.subscribe("hive/ml/control")
client.subscribe("hive/vision/enable")
```

**Fixed Code:**
```python
client.subscribe(config.TOPIC_CAMERA_FRAME)
logger.info(f"📨 Subscribed to: {config.TOPIC_CAMERA_FRAME}")
client.subscribe(config.TOPIC_CONTROL)
logger.info(f"📨 Subscribed to: {config.TOPIC_CONTROL}")
```

**Current Handler** (line 158):
```python
elif msg.topic in ["hive/ml/control", "hive/vision/enable"]:
```

**Fixed Handler:**
```python
elif msg.topic == config.TOPIC_CONTROL:
    # Parse JSON payload
    try:
        control_data = json.loads(msg.payload.decode())
        sensor = control_data.get("sensor")
        state = control_data.get("state")
        
        # Only handle ml_vision commands
        if sensor == "ml_vision":
            if state == "on":
                self.vision_enabled = True
                logger.info("🟢 ML Vision enabled via dashboard")
            elif state == "off":
                self.vision_enabled = False
                logger.info("🔴 ML Vision disabled via dashboard")
    except Exception as e:
        logger.debug(f"Control message parse error: {e}")
```

### **2. Update Config** (`config.py`)

**Remove outdated topic:**
```python
# REMOVE THIS (line 135):
TOPIC_VISION = "hive/vision"  # ❌ Not used anywhere
```

**Keep these:**
```python
TOPIC_CONTROL = "hive/control"              # ✅ Unified control
TOPIC_VISION_RESULTS = "hive/vision/detection"  # ✅ Detection output
TOPIC_AUDIO_RESULTS = "hive/audio/classification"  # ✅ Audio output
```

### **3. Verify Dashboard** (Already Correct ✅)

Dashboard already sends correct format:
```python
control_payload = json.dumps({
    "sensor": data['sensor'],  # "ml_vision" or "temperature", etc.
    "state": data['state']      # "on" or "off"
})
mqtt_client.publish("hive/control", control_payload, qos=1)
```

---

## Final MQTT Topic Architecture

### **Control Flow** (Dashboard → Services)
```
Dashboard
    │
    ├─→ hive/control ────────┬→ Edge-app (sensors: temp, camera, weight)
    │                        └→ Vision Service (sensor: ml_vision)
    │
    └─→ hive/audio/control ──→ Audio Service (recording triggers)
```

### **Data Flow** (Services → Dashboard)
```
Edge-app ──→ hive/telemetry ──────────────→ Dashboard
         └─→ hive/telemetry/camera/frame ─→ Vision Service
                                             │
                                             └→ hive/vision/detection → Dashboard

Audio Service ──→ hive/audio/classification → Dashboard
```

### **Complete Topic List**
| Topic | Direction | Purpose |
|-------|-----------|---------|
| `hive/telemetry` | Edge → Dashboard | Sensor readings |
| `hive/telemetry/camera/frame` | Edge → Vision | JPEG frames |
| `hive/vision/detection` | Vision → Dashboard | YOLO results |
| `hive/audio/classification` | Audio → Dashboard | Audio ML results |
| `hive/control` | Dashboard → Edge/Vision | Unified control |
| `hive/audio/control` | Dashboard → Audio | Audio-specific control |

---

## Testing Plan

**1. Deploy Vision Service Fix:**
```bash
cd ~/smart-hive-ai
git pull
docker compose build --no-cache smart-hive-vision
docker compose up -d smart-hive-vision
```

**2. Test Vision Toggle:**
```bash
# Publish test message
docker exec -it mosquitto mosquitto_pub -t "hive/control" \
  -m '{"sensor":"ml_vision","state":"off"}'

# Check vision service logs
docker logs smart-hive-vision | tail -20
# Expected: "🔴 ML Vision disabled via dashboard"

# Enable it
docker exec -it mosquitto mosquitto_pub -t "hive/control" \
  -m '{"sensor":"ml_vision","state":"on"}'

# Check logs again
# Expected: "🟢 ML Vision enabled via dashboard"
```

**3. Test from Dashboard:**
- Open http://192.168.88.16:5000
- Find ML Vision toggle switch
- Click ON → Check vision service logs for "🟢 ML Vision enabled"
- Click OFF → Check logs for "🔴 ML Vision disabled"

**4. Verify Sensor Toggles Still Work:**
```bash
# Test temperature sensor toggle
docker exec -it mosquitto mosquitto_pub -t "hive/control" \
  -m '{"sensor":"temperature","state":"off"}'

# Check edge-app logs
docker logs smart-hive-edge | grep "temperature"
# Expected: "Paused sensor: temperature"
```

---

## Impact Analysis

### **Files to Modify**
1. ✅ `ml_vision_service.py` - Update subscription + handler
2. ✅ `config.py` - Remove TOPIC_VISION
3. ⚠️ `dashboard_app.py` - Already correct (no changes needed)
4. ⚠️ `app.py` - Already correct (no changes needed)

### **Breaking Changes**
- ❌ None - dashboard already uses correct format

### **Backward Compatibility**
- ✅ Old topics (`hive/ml/control`, `hive/vision/enable`) removed, were never used
- ✅ No external systems affected

---

**Status:** Ready to implement ✅  
**Estimated Time:** 10 minutes (single file change + test)
