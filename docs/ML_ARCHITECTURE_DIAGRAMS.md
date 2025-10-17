"""
Smart Hive AI - ML Models Architecture & Flow Diagrams
Visual Reference for Integration
"""

# ═══════════════════════════════════════════════════════════════════════════
# 1. SYSTEM ARCHITECTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SMART HIVE AI SYSTEM ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      RASPBERRY PI 4 (Edge Device)                    │    │
│  │                                                                      │    │
│  │  ┌──────────────────────────────────────────────────────────────┐   │    │
│  │  │  SmartHiveSystem (app.py) - Main Orchestrator               │   │    │
│  │  │                                                              │   │    │
│  │  │  ┌─────────────┐  ┌──────────┐  ┌─────────────────────────┐ │   │    │
│  │  │  │ Hardware    │  │ Telemetry│  │ ML MODELS (NEW)         │ │   │    │
│  │  │  │ Sensors     │  │ Thread   │  │                         │ │   │    │
│  │  │  │             │  │          │  │ ┌──────────────────────┐│ │   │    │
│  │  │  │ • BME280    │  │ 60s      │  │ │ Vision Pipeline      ││ │   │    │
│  │  │  │ • LIS3DH    │  │ Collect  │  │ │ ┌────────────────┐  ││ │   │    │
│  │  │  │ • INMP441   │  │ & Pub    │  │ │ │ USB/PiCamera   │  ││ │   │    │
│  │  │  │             │  │          │  │ │ │ Frame Capture  │  ││ │   │    │
│  │  │  │ DynamoDB    │  │          │  │ │ └────────────────┘  ││ │   │    │
│  │  │  │ Storage     │  │          │  │ │         ↓            ││ │   │    │
│  │  │  └─────────────┘  └──────────┘  │ │ ┌────────────────┐  ││ │   │    │
│  │  │                                  │ │ │ YOLO Detection │  ││ │   │    │
│  │  │  ┌─────────────┐                 │ │ │ (best.pt)      │  ││ │   │    │
│  │  │  │   MQTT      │                 │ │ │ Confidence>0.7 │  ││ │   │    │
│  │  │  │   Client    │                 │ │ └────────────────┘  ││ │   │    │
│  │  │  │             │                 │ │         ↓            ││ │   │    │
│  │  │  │ • AWS IoT   │                 │ │ ┌────────────────┐  ││ │   │    │
│  │  │  │   Core      │                 │ │ │ Draw Boxes     │  ││ │   │    │
│  │  │  │ • Publish   │                 │ │ │ Pub to MQTT    │  ││ │   │    │
│  │  │  │ • Subscribe │                 │ │ └────────────────┘  ││ │   │    │
│  │  │  └─────────────┘                 │ │                     ││ │   │    │
│  │  │                                  │ │ ┌──────────────────┐│ │   │    │
│  │  │                                  │ │ │ Audio Pipeline   ││ │   │    │
│  │  │                                  │ │ │ ┌──────────────┐ ││ │   │    │
│  │  │  Flask Video Stream              │ │ │ │ Record (30s) │ ││ │   │    │
│  │  │  (Port 5001)                     │ │ │ │ Microphone   │ ││ │   │    │
│  │  │  ↓                               │ │ │ └──────────────┘ ││ │   │    │
│  │  │  Draw detections on frames       │ │ │       ↓          ││ │   │    │
│  │  │                                  │ │ │ ┌──────────────┐ ││ │   │    │
│  │  │                                  │ │ │ │ MFCC Extract │ ││ │   │    │
│  │  │  Video Feed Available            │ │ │ │ 13 + delta.. │ ││ │   │    │
│  │  │  http://pi:5001/video_feed       │ │ │ └──────────────┘ ││ │   │    │
│  │  │                                  │ │ │       ↓          ││ │   │    │
│  │  │                                  │ │ │ ┌──────────────┐ ││ │   │    │
│  │  │                                  │ │ │ │ ML Classify  │ ││ │   │    │
│  │  │                                  │ │ │ │ (.pkl model) │ ││ │   │    │
│  │  │                                  │ │ │ └──────────────┘ ││ │   │    │
│  │  │                                  │ │ │       ↓          ││ │   │    │
│  │  │                                  │ │ │ ┌──────────────┐ ││ │   │    │
│  │  │                                  │ │ │ │ Pub Result   │ ││ │   │    │
│  │  │                                  │ │ │ │ to MQTT      │ ││ │   │    │
│  │  │                                  │ │ │ └──────────────┘ ││ │   │    │
│  │  │                                  │ │ └──────────────────┘│ │   │    │
│  │  │                                  │ └─────────────────────┘ │   │    │
│  │  └──────────────────────────────────────────────────────────────┘   │    │
│  │                                                                      │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                               │
│  EXTERNAL CONNECTIONS:                                                      │
│                                                                               │
│         ↓ MQTT (hive/telemetry, hive/vision, hive/audio)                   │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  AWS IoT Core MQTT Broker                                       │        │
│  │  (Ingests telemetry, vision, audio results)                    │        │
│  └────────┬────────────────────────────────────────────────────────┘        │
│           ↓                                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  AWS DynamoDB                                                   │        │
│  │  (Stores time-series data with NZ timezone)                    │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                               │
│         ↓ HTTP (REST API)                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  Flask Dashboard (Port 5000)                                    │        │
│  │  • Vision status display                                        │        │
│  │  • Audio recording controls                                     │        │
│  │  • Video stream preview                                         │        │
│  │  • Real-time telemetry                                          │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```


# ═══════════════════════════════════════════════════════════════════════════
# 2. VISION PROCESSING PIPELINE (DETAILED FLOW)
# ═══════════════════════════════════════════════════════════════════════════

```
VISION PIPELINE - CONTINUOUS OPERATION
═════════════════════════════════════════════════════════════════════════════

Start Vision Thread
        ↓
    [Loop: Every 0.05s]
        ↓
    ┌───────────────────────────────────────────────┐
    │ Read Frame from Camera                        │
    │ (USB or Raspberry Pi Camera Module)           │
    ├───────────────────────────────────────────────┤
    │ frame_count = 0 → 1 → 2 → 3 → 0              │
    └──────────────────┬──────────────────────────────┘
                       ↓
            Is frame_count % 3 == 0?
            (Process every 3rd frame)
                      /        \
                    YES         NO
                    ↓            ↓
              ┌─────────────┐   Skip
              │ Resize to   │   This
              │ 640x480     │   Frame
              └──────┬──────┘     ↓
                     ↓          Loop
              ┌─────────────────────────────────┐
              │ YOLO Inference                  │
              │ • Input: 640x480 RGB frame      │
              │ • Model: best.pt (YOLOv8)       │
              │ • Output: boxes + confidence    │
              │ • Timeout: 5 seconds            │
              └──────┬────────────────────────────┘
                     ↓
              Boxes found with conf > 0.7?
                    /         \
                  YES          NO
                   ↓            ↓
              ┌──────────────┐  │
              │ Queen        │  │
              │ Detected!    │  Store
              │              │  Last
              │ Store Result │  Result
              │ {detected:   │  ↓
              │  true,       │  Sleep
              │  conf:0.87   │  100ms
              │  boxes:[...]}│  ↓
              └──────┬───────┘  Loop
                     ↓
              Publish to MQTT
              Topic: hive/vision/detection
              Payload: {detected:true, conf:0.87, ...}
                     ↓
              Store for Dashboard
              last_vision_result = {...}
                     ↓
              Draw Boxes on Frame
              (if displayed)
                     ↓
                  Loop

FRAME RATE: ~6-7 FPS (20 FPS capture, process 1 of 3)
CPU USAGE: 15-25% (one core)
LATENCY: ~100-150ms detection to display


# ═══════════════════════════════════════════════════════════════════════════
# 3. AUDIO PROCESSING PIPELINE (DETAILED FLOW)
# ═══════════════════════════════════════════════════════════════════════════

```
AUDIO PIPELINE - ON-DEMAND OPERATION
═════════════════════════════════════════════════════════════════════════════

Wait for Trigger
(Dashboard button or MQTT command)
        ↓
    ┌─────────────────────────────────────────┐
    │ Dashboard Click "Record 30s"             │
    │ (POST /api/audio/record)                 │
    └─────────┬───────────────────────────────┘
              ↓
    ┌─────────────────────────────────────────┐
    │ Initialize Microphone                   │
    │ Sample Rate: 22050 Hz                    │
    │ Channels: 1 (Mono)                       │
    │ Duration: 30 seconds                     │
    └─────────┬───────────────────────────────┘
              ↓
    ┌─────────────────────────────────────────┐
    │ Record Audio from Microphone             │
    │ [████████████████████████████████] 30s  │
    │ Collecting: 660,150 samples             │
    │ (22050 Hz × 30 sec)                     │
    └─────────┬───────────────────────────────┘
              ↓
    Recording Complete
    Audio Buffer = 30s of raw audio
              ↓
    ┌─────────────────────────────────────────────────┐
    │ Feature Extraction (MFCC)                       │
    │                                                  │
    │ 1. Compute MFCC Coefficients                    │
    │    └─ 13 coefficients per frame                 │
    │                                                  │
    │ 2. Compute Delta (velocity)                     │
    │    └─ First derivative of MFCCs                 │
    │                                                  │
    │ 3. Compute Delta-Delta (acceleration)           │
    │    └─ Second derivative of MFCCs                │
    │                                                  │
    │ Statistics Computed for Each:                   │
    │    • Mean across all frames                     │
    │    • Standard Deviation across all frames       │
    │                                                  │
    │ Final Feature Vector: 78 values                 │
    │ (13 MFCC × 2 (mean+std) +                       │
    │  13 Delta × 2 (mean+std) +                      │
    │  13 Delta-Delta × 2 (mean+std))                 │
    └─────────┬───────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────────────────┐
    │ ML Classification                               │
    │                                                  │
    │ Input: Feature vector (78 values)               │
    │ Model: queen_bee_model.pkl                      │
    │        (RandomForest / SVM / LogisticRegression)│
    │                                                  │
    │ Processing:                                     │
    │ Model.predict(features) → [0 or 1]             │
    │ Model.predict_proba(features) → [p, 1-p]       │
    │                                                  │
    │ Decision:                                       │
    │ IF predict == 1:                                │
    │   classification = "queen_present"              │
    │   confidence = max_probability                  │
    │ ELSE:                                           │
    │   classification = "queen_absent"               │
    │   confidence = max_probability                  │
    └─────────┬───────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────────────────┐
    │ Result: {                                        │
    │   "classification": "queen_present",            │
    │   "confidence": 0.92,                           │
    │   "duration": 30,                               │
    │   "timestamp": 1697500060.456                   │
    │ }                                               │
    └─────────┬───────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────────────────┐
    │ Publish to MQTT                                 │
    │ Topic: hive/audio/classification                │
    │ Payload: {classification, confidence, ...}      │
    └─────────┬───────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────────────────┐
    │ Store in Dashboard Memory                       │
    │ last_audio_result = {...}                       │
    │                                                  │
    │ (Optional) Save to Disk                         │
    │ audio_recordings/audio_20251016_143022.npy      │
    └─────────┬───────────────────────────────────────┘
              ↓
    ┌─────────────────────────────────────────────────┐
    │ Update Dashboard                                │
    │ Display: "Queen Present (92% confidence)"       │
    │ or: "Queen Not Detected (88% confidence)"       │
    └─────────────────────────────────────────────────┘

TOTAL TIME: ~30 seconds (recording) + 0.5 seconds (processing)
CPU USAGE: Spike to 40% during processing, then idle
STORAGE: 1.3 MB per 30-second recording (if saved)


# ═══════════════════════════════════════════════════════════════════════════
# 4. CONFIGURATION PARAMETER INFLUENCE
# ═══════════════════════════════════════════════════════════════════════════

```
VISION CONFIGURATION IMPACT
════════════════════════════════════════════════════════════════════════════

VISION_CONFIDENCE_THRESHOLD
├─ Range: 0.5 (permissive) → 0.9 (strict)
├─ Default: 0.7 (balanced)
├─ Effect on Results:
│  0.5 ──→ Detects more (including partial bees, false positives)
│  0.7 ──→ Balanced (catches most real queens)
│  0.9 ──→ Only very confident detections (may miss some queens)
└─ Performance: No impact (same processing time)

VISION_PROCESS_EVERY_N_FRAMES
├─ Range: 1 (process every frame) → 5 (process every 5th frame)
├─ Default: 3 (balanced)
├─ Frame Rate Output:
│  1 ──→ ~20 FPS detection (real-time, high CPU)
│  3 ──→ ~6-7 FPS detection (balanced)
│  5 ──→ ~4 FPS detection (low CPU)
├─ CPU Impact: Direct correlation
└─ Latency: Higher N = longer delay to detection

CPU USAGE ESTIMATES
├─ Process Every Frame (N=1): 25-40% CPU
├─ Process Every 3rd (N=3): 15-25% CPU (DEFAULT)
├─ Process Every 5th (N=5): 10-15% CPU
└─ No Vision Model: 5-10% CPU

RECOMMENDATION FOR RASPBERRY PI 4
├─ Use: N=3 (default)
├─ Confidence: 0.7 (default)
└─ This gives 6-7 FPS with balanced detection accuracy


AUDIO CONFIGURATION IMPACT
════════════════════════════════════════════════════════════════════════════

AUDIO_RECORD_DURATION_SEC
├─ Range: 10 seconds (minimum) → 120 seconds (maximum)
├─ Default: 30 seconds (optimal)
├─ Model Input:
│  10s ──→ ~220k samples (minimal features, may lose patterns)
│  30s ──→ ~660k samples (standard, good pattern detection)
│  60s ──→ ~1.3M samples (maximum patterns, slower processing)
└─ Processing Time: Linear increase with duration

AUDIO_CONFIDENCE_THRESHOLD
├─ Range: 0.5 (permissive) → 0.9 (strict)
├─ Default: 0.6 (practical)
├─ Decision Logic:
│  0.5 ──→ Report predictions with <50% confidence (loose)
│  0.6 ──→ Report predictions with <60% confidence (default)
│  0.8 ──→ Report only high-confidence predictions (strict)
└─ Filters weak predictions

AUDIO_SAMPLE_RATE
├─ Value: 22050 Hz (FIXED - matches model training)
├─ DO NOT CHANGE without retraining model
└─ Standard sampling rate for speech/animal sounds

RECOMMENDED SETTINGS
├─ Recording Duration: 30-45 seconds (good for detection)
├─ Confidence Threshold: 0.6-0.7 (balanced)
├─ Save Recordings: FALSE (default, saves storage)
└─ Dashboard shows last result only


# ═══════════════════════════════════════════════════════════════════════════
# 5. THREADING & TIMING MODEL
# ═══════════════════════════════════════════════════════════════════════════

```
THREAD EXECUTION TIMELINE
════════════════════════════════════════════════════════════════════════════

MAIN THREAD (app.py - SmartHiveSystem)
├─ Startup: Initialize all components
├─ Start Vision Thread
├─ Start Telemetry Thread
└─ Block on: keyboard interrupt or stop signal
   │
   ├─ Status: Running


VISION THREAD (New)
├─ Initialization:
│  └─ Load YOLO model (200-300 MB memory)
├─ Loop (until stopped):
│  ├─ Read frame (5-10ms)
│  ├─ Check: process_count % 3 == 0?
│  ├─ If YES:
│  │  ├─ Resize frame (5-10ms)
│  │  ├─ YOLO inference (50-100ms)
│  │  └─ Parse results, publish MQTT (10ms)
│  ├─ If NO:
│  │  └─ Skip to next
│  └─ Repeat every frame (~50ms per frame)
├─ Total Loop Time: 50-100ms per iteration
├─ Effective Rate: 6-7 FPS
└─ CPU Core: 1 (dedicated)


AUDIO THREAD (On-Demand - Dashboard Trigger)
├─ Wait for trigger (POST /api/audio/record)
├─ When triggered:
│  ├─ Initialize microphone (100ms)
│  ├─ Record audio (30,000ms for 30s)
│  ├─ Extract MFCC features (300-500ms)
│  ├─ ML inference (100-200ms)
│  ├─ Publish MQTT result (10ms)
│  └─ Return to dashboard
├─ Total Time: 30.5 seconds
├─ CPU Core: 1 (shared with other tasks)
└─ CPU Usage: 40% spike during processing, then idle


TELEMETRY THREAD (Existing)
├─ Loop every 60 seconds:
│  ├─ Read sensors (BME280, LIS3DH, INMP441)
│  ├─ Package into JSON
│  ├─ Publish to MQTT (hive/telemetry)
│  ├─ Write to DynamoDB
│  └─ Total time: 2-3 seconds
└─ CPU Usage: Minimal (<5%) for 3 seconds, then idle


CONCURRENT EXECUTION
└─ Vision Thread + Telemetry Thread can run simultaneously
   ├─ Vision: ~20% CPU
   ├─ Telemetry: ~5% CPU (for 3s every 60s)
   └─ Total: ~25% CPU (sustainable on Pi)


# ═══════════════════════════════════════════════════════════════════════════
# 6. DATA FLOW TO CLOUD
# ═══════════════════════════════════════════════════════════════════════════

```
DATA FLOW DIAGRAM
════════════════════════════════════════════════════════════════════════════

RASPBERRY PI ─→ MQTT PUBLISHER (AWS IoT Core) ─→ AWS DYNAMODB
                        ↓
                   DynamoDB Rules Engine
                        ↓
                   Store Time-Series Data
                        ↓
                  Query + Analytics


VISION RESULTS
═════════════
Raspberry Pi: {detected: true, confidence: 0.87, boxes: [...]}
      ↓
MQTT Topic: hive/vision/detection
      ↓
AWS IoT Core (receives message)
      ↓
DynamoDB Table: SmartHiveData
      ├─ Partition Key: device_id (SmartHive_Pi)
      ├─ Sort Key: timestamp (ISO-8601 with NZ timezone)
      ├─ Attributes:
      │  ├─ event_type: "vision"
      │  ├─ detected: true
      │  ├─ confidence: 0.87
      │  └─ boxes: "[[[100,50,200,150]]]"
      └─ TTL: None (keep forever)


AUDIO RESULTS
═════════════
Raspberry Pi: {classification: "queen_present", confidence: 0.92, ...}
      ↓
MQTT Topic: hive/audio/classification
      ↓
AWS IoT Core (receives message)
      ↓
DynamoDB Table: SmartHiveData
      ├─ Partition Key: device_id (SmartHive_Pi)
      ├─ Sort Key: timestamp (ISO-8601 with NZ timezone)
      ├─ Attributes:
      │  ├─ event_type: "audio"
      │  ├─ classification: "queen_present"
      │  ├─ confidence: 0.92
      │  └─ duration: 30
      └─ TTL: None (keep forever)


TELEMETRY RESULTS
═════════════════
Raspberry Pi: {temp: 25.3, humidity: 60.2, vibration: 0.15, ...}
      ↓
MQTT Topic: hive/telemetry
      ↓
AWS IoT Core (receives message)
      ↓
DynamoDB Table: SmartHiveData
      ├─ Partition Key: device_id (SmartHive_Pi)
      ├─ Sort Key: timestamp (ISO-8601 with NZ timezone)
      ├─ Attributes:
      │  ├─ event_type: "telemetry"
      │  ├─ temperature: 25.3
      │  ├─ humidity: 60.2
      │  ├─ vibration: 0.15
      │  └─ ... other sensors
      └─ TTL: None (keep forever)


QUERY EXAMPLE
═════════════
Get all queen detections in last 24 hours:

Query DynamoDB:
  ├─ KeyConditionExpression: device_id = 'SmartHive_Pi'
  ├─ FilterExpression: event_type = 'vision' AND detected = true
  ├─ TimeRange: timestamp >= NOW - 86400 seconds
  └─ Returns: [Queen detection events with timestamps and confidence]


# ═══════════════════════════════════════════════════════════════════════════
# 7. ERROR RECOVERY FLOWCHART
# ═══════════════════════════════════════════════════════════════════════════

```
ERROR HANDLING & RECOVERY
════════════════════════════════════════════════════════════════════════════

VISION MODEL ERRORS
────────────────────

Model File Not Found
  ↓ (On App Startup)
  └─→ Log Error: "Model file not found at models/best.pt"
      └─→ Set ENABLE_VISION_MODEL = False
          └─→ Continue app (vision disabled)
              └─→ Dashboard shows "Vision: Unavailable"

Camera Not Found
  ↓ (During Vision Thread)
  └─→ Log Warning: "Camera read returned None"
      └─→ Retry frame capture
          └─→ If fails 5 times: Disable vision temporarily
              └─→ Retry every 10 seconds
                  └─→ Resume when camera available

Inference Timeout (>5 seconds)
  ↓ (During YOLO processing)
  └─→ Log Warning: "Frame processing took >5s"
      └─→ Skip this frame
          └─→ Continue next frame
              └─→ If happens >3 times: Increase PROCESS_EVERY_N_FRAMES
                  └─→ Reduce processing frequency


AUDIO MODEL ERRORS
────────────────────

Model File Not Found
  ↓ (On App Startup)
  └─→ Log Error: "Model file not found"
      └─→ Set ENABLE_AUDIO_MODEL = False
          └─→ Continue app (audio disabled)
              └─→ Dashboard shows "Audio: Unavailable"

Microphone Not Found
  ↓ (When recording triggered)
  └─→ Log Error: "Microphone not found"
      └─→ Return error to dashboard: {error: "Microphone not found"}
          └─→ User sees error message
              └─→ User must plug in microphone
                  └─→ Retry recording

Recording Timeout
  ↓ (If recording >duration+10 seconds)
  └─→ Force stop recording
      └─→ Process partial audio
          └─→ Return result with warning
              └─→ Log event for debugging

Feature Extraction Failed
  ↓ (librosa or scipy error)
  └─→ Log Error: "MFCC extraction failed"
      └─→ Return error to dashboard
          └─→ User can retry


RECOVERY STRATEGIES
─────────────────────

1. Graceful Degradation
   ├─ Vision unavailable → System continues with audio + telemetry
   ├─ Audio unavailable → System continues with vision + telemetry
   └─ Telemetry failed → System continues with vision + audio

2. Automatic Retry
   ├─ Vision: Retry every frame (automatic retry built-in)
   ├─ Audio: User-triggered (no automatic retry)
   └─ Both: Exponential backoff for cloud connectivity

3. User Notification
   ├─ Dashboard shows component status
   ├─ Error logs available in Docker console
   └─ MQTT can publish error events

4. System Restart
   ├─ If all components fail: Restart Docker container
   ├─ Kubernetes auto-restart (if deployed)
   └─ Systemd auto-restart (if on bare metal)


# ═══════════════════════════════════════════════════════════════════════════
# 8. PERFORMANCE MONITORING
# ═══════════════════════════════════════════════════════════════════════════

```
KEY METRICS TO MONITOR
═══════════════════════════════════════════════════════════════════════════

VISION PERFORMANCE
──────────────────
Metric                      | Healthy Range     | Action If Exceeded
─────────────────────────────────────────────────────────────────
Inference Time              | 50-150ms          | Increase PROCESS_EVERY_N_FRAMES
CPU Usage (Vision Thread)   | 15-30%            | Reduce frame rate
Detections per Hour         | 0-10              | Normal (depends on activity)
False Positive Rate         | <10%              | Increase confidence threshold
Frame Drops                 | 0                 | Check camera connection


AUDIO PERFORMANCE
─────────────────
Metric                      | Healthy Range     | Action If Exceeded
─────────────────────────────────────────────────────────────────
Recording Duration          | 30±2s             | Check microphone
Feature Extraction Time     | 300-500ms         | Normal (depends on duration)
Classification Time         | 100-200ms         | Check Pi CPU
Storage per Recording       | ~1.3 MB (30s)     | Disable AUDIO_SAVE_RECORDINGS
Confidence Scores           | 0.5-0.95          | Review model performance


SYSTEM PERFORMANCE
──────────────────
Metric                      | Healthy Range     | Action If Exceeded
─────────────────────────────────────────────────────────────────
Total CPU Usage             | <50%              | Reduce vision frame rate
Memory Usage                | <70% of 4GB       | Check for memory leaks
Dashboard Response Time     | <2 seconds        | Restart dashboard
MQTT Publish Latency        | <500ms            | Check AWS IoT connection
DynamoDB Write Latency      | <2 seconds        | Check AWS connectivity


LOGGING & DEBUGGING
───────────────────
Enable detailed logging:

In app.py:
  logging.basicConfig(level=logging.DEBUG)

Monitor logs:
  docker-compose logs app -f

MQTT Message Verification:
  mosquitto_sub -h localhost -t "hive/#"

DynamoDB Query:
  aws dynamodb query --table-name SmartHiveData \
    --key-condition-expression "device_id = :id" \
    --expression-attribute-values '{":id":{"S":"SmartHive_Pi"}}'


# ═══════════════════════════════════════════════════════════════════════════
# END OF ARCHITECTURE DIAGRAMS
# ═══════════════════════════════════════════════════════════════════════════
```

---

**Use these diagrams as reference during implementation**

Key Takeaways:
1. Vision runs continuously, processes every 3rd frame (≈6-7 FPS)
2. Audio runs on-demand, takes 30-31 seconds per recording
3. Both publish to MQTT → DynamoDB automatically
4. Dashboard UI provides essential controls only
5. Configuration via config.py, dashboard for runtime toggles
6. Graceful degradation if any component fails
7. Target CPU: 20-30% under normal load (safe for Pi 4)

"""
