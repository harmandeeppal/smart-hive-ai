"""
Smart Hive AI - ML Models Integration Plan
Master's Level Project (2-Day Implementation)
==============================================

Date: October 2025
Scope: Queen Bee Vision & Audio Detection Integration
Timeline: 2 Days
Complexity: Master Level
Approach: Simple, Essential Features Only
"""

# TABLE OF CONTENTS
1. Executive Summary
2. Current State Analysis
3. Architecture Design
4. Implementation Roadmap
5. Configuration Strategy
6. Dashboard Integration (Essential Only)
7. Deployment & Verification
8. Git Commit Strategy

---

# 1. EXECUTIVE SUMMARY

## Objectives
✅ Integrate YOLO-based vision model for real-time queen bee detection
✅ Integrate audio ML model for queen bee presence detection
✅ Deployment on Raspberry Pi with minimal complexity
✅ Dashboard control for essential features only
✅ Configuration via config.py + Dashboard toggles

## Key Principles
- **Simple**: Only essential features; no unnecessary complexity
- **Fast**: 2-day implementation using AI agent
- **Modular**: Vision and Audio can run independently
- **Resource-Aware**: Optimize for Raspberry Pi 4 constraints
- **Master-Level**: Professional documentation, error handling, logging

## Current State
✅ Vision Model: YOLO (best.pt) - Ready, uses Picamera2/USB
✅ Audio Model: scikit-learn + librosa - Ready, uses microphone
✅ Core App: SmartHiveSystem - Skeleton ready for integration
✅ Dashboard: Flask + Socket.IO - Ready for new endpoints
✅ Config: Centralized management - Ready for ML parameters

---

# 2. CURRENT STATE ANALYSIS

## Vision Model (ml_vision_model/)
```
Status: READY FOR INTEGRATION
File: camera_yolo_noir.py (YOLOv8 implementation)

Current Implementation:
- Uses Picamera2 for Raspberry Pi Camera Module
- Loads best.pt (YOLOv8 model)
- Detects "Queen" class with confidence threshold
- Outputs bounding boxes to cv2 windows
- Saves input/output images

Issues to Address:
❌ Hardcoded file I/O (inputs/, outputs/)
❌ OpenCV window display (not suitable for headless Pi)
❌ No integration with main app
❌ No USB camera support yet
❌ No error handling for camera initialization failure
```

**Model Details:**
- Format: PyTorch (.pt) - YOLOv8
- Input: 640x480 RGB frames
- Output: Bounding boxes + class + confidence
- Target Classes: ["queen", "background"]
- Confidence Threshold: Currently 0.1 (should be configurable 0.5-0.9)

## Audio Model (ml_audio_model/)
```
Status: READY FOR INTEGRATION
File: enhanced_queen_bee_detection.py

Current Implementation:
- Uses librosa + MFCC feature extraction
- Multiple classifiers (RandomForest, SVM, LogisticRegression)
- Windowed audio analysis (1.0s windows)
- Training pipeline included

Issues to Address:
❌ No real-time inference API
❌ No microphone input integration
❌ No integration with main app
❌ Model loading logic needed (uses .pkl files)
❌ No error handling for microphone failures
```

**Model Details:**
- Feature Extraction: MFCC (13 coefficients) + Delta + Delta-Delta
- Window Size: 1.0 seconds
- Sample Rate: 22050 Hz
- Output: Binary classification (queen_present / queen_absent)
- Model Storage: Pickle files (.pkl) - Already in ml_audio_model/

## Main Application State
```
File: app.py (SmartHiveSystem class)
- ✅ Sensor initialization infrastructure
- ✅ MQTT client setup
- ✅ DynamoDB write logic
- ✅ Threading infrastructure
- ❌ Vision processor not yet integrated
- ❌ Audio processor not yet integrated
- ❌ Real-time inference pipelines missing
```

---

# 3. ARCHITECTURE DESIGN

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│               RASPBERRY PI 4 (Edge Device)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              SmartHiveSystem (Main App)              │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │                                                       │    │
│  │  ┌──────────────────┐    ┌──────────────────────┐   │    │
│  │  │ Vision Pipeline  │    │  Audio Pipeline      │   │    │
│  │  ├──────────────────┤    ├──────────────────────┤   │    │
│  │  │ • USB/PiCamera   │    │ • Microphone Input   │   │    │
│  │  │ • YOLO Detection │    │ • Audio Recording    │   │    │
│  │  │ • Inference Loop │    │ • MFCC Extraction    │   │    │
│  │  │ • Result Storage │    │ • ML Classification  │   │    │
│  │  └──────────────────┘    └──────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │     Sensor Data Collection (Existing)        │   │    │
│  │  │  • BME280 (Temperature/Humidity)             │   │    │
│  │  │  • LIS3DH (Vibration)                        │   │    │
│  │  │  • INMP441 (Basic Audio Levels)              │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │   Communication & Storage (Existing)         │   │    │
│  │  │  • MQTT → AWS IoT Core                       │   │    │
│  │  │  • DynamoDB Persistence                      │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
              ↓                           ↓
    ┌─────────────────────┐    ┌─────────────────────┐
    │    AWS IoT Core     │    │  Flask Dashboard    │
    │   (MQTT Broker)     │    │   (Web Interface)   │
    └─────────────────────┘    └─────────────────────┘
              ↓                           ↓
    ┌─────────────────────┐    ┌─────────────────────┐
    │    DynamoDB DB      │    │    Video Stream     │
    │  (Time-series)      │    │    ML Results       │
    └─────────────────────┘    └─────────────────────┘
```

## Component Integration Plan

### 3.1 Vision Processing Pipeline

**File Structure:**
```
ml_vision_model/
├── best.pt                      (YOLOv8 model)
├── camera_yolo_noir.py          (Original - reference only)
└── vision_processor.py (NEW)    (Integration wrapper)
```

**Integration Steps:**
1. Create `ml_vision_model/vision_processor.py` wrapper
   - Initialize YOLO model once (on app startup)
   - Provide `detect_frame(frame)` method
   - Return: `{"detected": bool, "confidence": float, "boxes": [[x1,y1,x2,y2], ...]}`
   - Handle errors gracefully (model load failure, inference timeout)

2. Modify app.py SmartHiveSystem
   - Add `vision_thread` for continuous frame processing
   - Process every N frames (configurable: 1, 3, 5)
   - Store results: `self.last_detection = {...}`
   - Publish to MQTT topic: `hive/vision`

3. Integration with existing video stream
   - Draw detection boxes on video frames
   - Display confidence scores
   - Toggle enable/disable via config

**Threading Model:**
```
Main Thread:
  └─ Telemetry Publishing (60s interval)
  
Vision Thread (NEW):
  └─ Continuous video frame capture
  └─ YOLO inference (every N frames)
  └─ Store results
  └─ Publish to MQTT
  
Audio Thread (NEW):
  └─ On-demand recording (30-60s)
  └─ Feature extraction
  └─ ML classification
  └─ Publish results to MQTT
```

### 3.2 Audio Processing Pipeline

**File Structure:**
```
ml_audio_model/
├── enhanced_queen_bee_detection.py  (Original - reference)
├── queen_bee_model.pkl              (Pre-trained model)
└── audio_processor.py (NEW)         (Integration wrapper)
```

**Integration Steps:**
1. Create `ml_audio_model/audio_processor.py` wrapper
   - Load pre-trained model from .pkl file on startup
   - Provide `record_and_classify(duration_sec)` method
   - Return: `{"classification": "queen_present/absent", "confidence": float}`
   - Handle microphone failures gracefully

2. Modify app.py SmartHiveSystem
   - Add `record_audio_on_demand()` method
   - Triggered via MQTT control topic or Dashboard button
   - Record for configurable duration (30-60s)
   - Extract MFCC features + apply model
   - Publish results to MQTT: `hive/audio`
   - Optional: Save audio file to storage

3. Dashboard trigger
   - Add "Start Recording" button
   - Show recording progress (timer)
   - Display classification result
   - Optional: Download recorded audio

**Threading Model:**
```
Audio Recording Thread:
  └─ Wait for trigger (MQTT or Dashboard)
  └─ Record audio for N seconds
  └─ Extract MFCC features
  └─ Run inference
  └─ Publish results
  └─ Optional: Save audio file
```

---

# 4. IMPLEMENTATION ROADMAP

## Phase 1: Prepare Integration Wrappers (Day 1 Morning - 2 hours)

### Step 1.1: Create Vision Processor Wrapper
**File:** `ml_vision_model/vision_processor.py`

```python
# Pseudo-code structure
class VisionProcessor:
    def __init__(self, model_path, confidence_threshold=0.7):
        # Load YOLO model once
        # Set confidence threshold
        # Error handling for missing model
    
    def process_frame(self, frame):
        # Input: OpenCV frame (BGR)
        # Output: {"detected": bool, "confidence": float, "boxes": [...]}
        # Error handling for processing timeout
    
    def enable(self):
        # Set enabled flag
    
    def disable(self):
        # Set disabled flag
```

**Key Points:**
- Lazy model loading (load on first use)
- Frame resizing to 640x480 if needed
- Confidence filtering
- Exception handling for GPU memory issues
- Logging (detection count, inference time)

### Step 1.2: Create Audio Processor Wrapper
**File:** `ml_audio_model/audio_processor.py`

```python
# Pseudo-code structure
class AudioProcessor:
    def __init__(self, model_path, sample_rate=22050):
        # Load pre-trained model from .pkl
        # Configure audio parameters
        # Error handling for missing model
    
    def record_and_classify(self, duration_sec=30):
        # Record audio from microphone
        # Return: {"classification": str, "confidence": float}
        # Error handling for microphone failure
    
    def extract_features(self, audio_data):
        # Extract MFCC features (13 coefficients + delta + delta-delta)
        # Perform windowing if needed
    
    def enable(self):
        # Set enabled flag
    
    def disable(self):
        # Set disabled flag
```

**Key Points:**
- Use librosa for MFCC extraction
- Window-based feature aggregation
- Confidence scoring from model
- Microphone initialization error handling
- Optional: Audio file saving

---

## Phase 2: Integrate into Main App (Day 1 Afternoon - 3 hours)

### Step 2.1: Update config.py
**Add ML Configuration Section:**

```python
# =====================================================
# ML Models Configuration
# =====================================================

# Vision Model Settings
ENABLE_VISION_MODEL = True
VISION_MODEL_PATH = "models/best.pt"
VISION_CONFIDENCE_THRESHOLD = 0.7
VISION_PROCESS_EVERY_N_FRAMES = 3  # Process every 3rd frame
VISION_FRAME_TIMEOUT_SEC = 5  # Kill inference if takes >5s

# Audio Model Settings
ENABLE_AUDIO_MODEL = True
AUDIO_MODEL_PATH = "ml_audio_model/queen_bee_model.pkl"
AUDIO_SAMPLE_RATE = 22050
AUDIO_RECORD_DURATION_SEC = 30  # Default recording duration
AUDIO_CONFIDENCE_THRESHOLD = 0.6
AUDIO_SAVE_RECORDINGS = False  # Save recorded audio files
AUDIO_RECORDINGS_DIR = "audio_recordings"

# MQTT Topics for ML Results
TOPIC_VISION_RESULTS = "hive/vision/detection"
TOPIC_AUDIO_RESULTS = "hive/audio/classification"
```

### Step 2.2: Update SmartHiveSystem (app.py)
**Add vision & audio integration:**

```python
class SmartHiveSystem:
    def __init__(self):
        # ... existing init code ...
        
        # Add ML processors
        if config.ENABLE_VISION_MODEL:
            from ml_vision_model.vision_processor import VisionProcessor
            self.vision_processor = VisionProcessor(
                config.VISION_MODEL_PATH,
                config.VISION_CONFIDENCE_THRESHOLD
            )
        
        if config.ENABLE_AUDIO_MODEL:
            from ml_audio_model.audio_processor import AudioProcessor
            self.audio_processor = AudioProcessor(
                config.AUDIO_MODEL_PATH,
                config.AUDIO_SAMPLE_RATE
            )
        
        # Add threading events for control
        self.vision_enabled = True
        self.audio_enabled = False  # Off by default
        self.recording = False
    
    def start(self):
        # ... existing start code ...
        
        # Start vision thread if enabled
        if config.ENABLE_VISION_MODEL:
            vision_thread = threading.Thread(
                target=self._vision_loop,
                daemon=True
            )
            vision_thread.start()
    
    def _vision_loop(self):
        """Continuous vision processing loop"""
        frame_count = 0
        while self.is_running:
            if not self.vision_enabled:
                time.sleep(0.1)
                continue
            
            try:
                # Capture frame
                frame = self.camera.read()
                if frame is None:
                    continue
                
                frame_count += 1
                
                # Process every N frames
                if frame_count % config.VISION_PROCESS_EVERY_N_FRAMES == 0:
                    result = self.vision_processor.process_frame(frame)
                    
                    # Publish to MQTT
                    if result["detected"]:
                        self.publish_result("VISION", result)
                    
                    # Store for dashboard
                    self.last_vision_result = result
                
            except Exception as e:
                logging.error(f"Vision processing error: {e}")
    
    def record_audio(self, duration_sec=None):
        """Trigger audio recording and classification"""
        if not config.ENABLE_AUDIO_MODEL:
            return {"error": "Audio model disabled"}
        
        if self.recording:
            return {"error": "Already recording"}
        
        try:
            duration = duration_sec or config.AUDIO_RECORD_DURATION_SEC
            self.recording = True
            
            result = self.audio_processor.record_and_classify(duration)
            
            # Publish to MQTT
            self.publish_result("AUDIO", result)
            
            # Store for dashboard
            self.last_audio_result = result
            
            return result
            
        except Exception as e:
            logging.error(f"Audio processing error: {e}")
            return {"error": str(e)}
        finally:
            self.recording = False
```

### Step 2.3: Update Dashboard (dashboard_app.py)
**Add essential endpoints:**

```python
# Add new routes for ML models

@app.route('/api/vision/status')
def vision_status():
    """Get current vision detection status"""
    return {
        'enabled': system.vision_enabled,
        'last_detection': system.last_vision_result,
        'model_loaded': True
    }

@app.route('/api/audio/record', methods=['POST'])
def start_audio_recording():
    """Trigger audio recording"""
    duration = request.json.get('duration', config.AUDIO_RECORD_DURATION_SEC)
    result = system.record_audio(duration)
    return result

@app.route('/api/ml/toggle', methods=['POST'])
def toggle_ml_model():
    """Toggle vision or audio model"""
    model_type = request.json.get('type')  # 'vision' or 'audio'
    if model_type == 'vision':
        system.vision_enabled = not system.vision_enabled
        return {'vision_enabled': system.vision_enabled}
    elif model_type == 'audio':
        system.audio_enabled = not system.audio_enabled
        return {'audio_enabled': system.audio_enabled}
```

---

## Phase 3: Dashboard UI Updates (Day 1 Evening - 1.5 hours)

### Step 3.1: Update Dashboard HTML
**File:** `dashboard/templates/index.html`

**Add ML Controls Section:**
```html
<!-- ML Models Section -->
<div class="ml-section">
    <h3>AI Models Control</h3>
    
    <!-- Vision Model -->
    <div class="model-card">
        <h4>Vision Detection</h4>
        <button onclick="toggleVisionModel()">
            <span id="vision-status">●</span> Vision
        </button>
        <p id="vision-result">No detection</p>
    </div>
    
    <!-- Audio Model -->
    <div class="model-card">
        <h4>Audio Classification</h4>
        <button onclick="startAudioRecording()">
            <span id="audio-status">●</span> Record & Analyze
        </button>
        <div id="recording-progress" style="display:none;">
            <progress id="record-progress" max="30"></progress>
            <p id="record-timer">30s</p>
        </div>
        <p id="audio-result">Ready</p>
    </div>
</div>
```

### Step 3.2: Update Dashboard JavaScript
**File:** `dashboard/static/app.js`

```javascript
// Vision Model Control
function toggleVisionModel() {
    fetch('/api/ml/toggle', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({type: 'vision'})
    })
    .then(r => r.json())
    .then(data => {
        document.getElementById('vision-status').style.color = 
            data.vision_enabled ? 'green' : 'red';
    });
}

// Audio Recording Control
function startAudioRecording() {
    const duration = 30;  // Fixed: 30 seconds
    
    fetch('/api/audio/record', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({duration: duration})
    });
    
    // Show progress
    showRecordingProgress(duration);
}

function showRecordingProgress(duration) {
    const progressDiv = document.getElementById('recording-progress');
    progressDiv.style.display = 'block';
    
    let remaining = duration;
    const interval = setInterval(() => {
        document.getElementById('record-timer').textContent = remaining + 's';
        document.getElementById('record-progress').value = duration - remaining;
        remaining--;
        
        if (remaining < 0) {
            clearInterval(interval);
            progressDiv.style.display = 'none';
        }
    }, 1000);
}
```

### Step 3.3: Update Dashboard CSS
**File:** `dashboard/static/styles.css`

```css
.ml-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 10px;
    padding: 20px;
    margin: 20px 0;
    color: white;
}

.model-card {
    background: rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}

.model-card button {
    background: #fff;
    color: #667eea;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-weight: bold;
}

.model-card button:hover {
    background: #f0f0f0;
}

#recording-progress {
    margin: 10px 0;
}

progress {
    width: 100%;
    height: 20px;
    border-radius: 5px;
}
```

---

## Phase 4: Testing & Deployment (Day 2 - 6 hours)

### Step 4.1: Create Test Scripts (1 hour)
**File:** `scripts/test_vision_model.py`

```python
#!/usr/bin/env python3
"""Test vision model integration"""

import cv2
import config
from ml_vision_model.vision_processor import VisionProcessor

def test_vision():
    processor = VisionProcessor(config.VISION_MODEL_PATH)
    print("✅ Vision processor loaded")
    
    # Test with mock frame
    frame = cv2.zeros((480, 640, 3), dtype='uint8')
    result = processor.process_frame(frame)
    print(f"✅ Vision test result: {result}")

if __name__ == '__main__':
    test_vision()
```

**File:** `scripts/test_audio_model.py`

```python
#!/usr/bin/env python3
"""Test audio model integration"""

import config
from ml_audio_model.audio_processor import AudioProcessor

def test_audio():
    processor = AudioProcessor(config.AUDIO_MODEL_PATH)
    print("✅ Audio processor loaded")
    print("⏺ Recording for 3 seconds...")
    result = processor.record_and_classify(duration_sec=3)
    print(f"✅ Audio test result: {result}")

if __name__ == '__main__':
    test_audio()
```

### Step 4.2: Docker Updates (1 hour)
**Dockerfile.edge additions:**

```dockerfile
# ML Models Support
RUN pip install ultralytics librosa scikit-learn

# Copy ML models
COPY ml_vision_model/ /app/ml_vision_model/
COPY ml_audio_model/ /app/ml_audio_model/
COPY models/ /app/models/

# Create audio recordings directory
RUN mkdir -p /app/audio_recordings
```

### Step 4.3: Integration Testing (3 hours)
**Test Checklist:**

```
Vision Model:
  □ Model loads successfully
  □ Process frame without errors
  □ Bounding boxes drawn correctly
  □ Confidence filtering works
  □ MQTT publishing works
  □ Dashboard shows results

Audio Model:
  □ Model loads successfully
  □ Microphone initialization works
  □ Recording completes successfully
  □ MFCC extraction works
  □ Classification returns results
  □ MQTT publishing works
  □ Dashboard recording button works

Integration:
  □ Both models can run simultaneously
  □ No CPU overload (Pi stays responsive)
  □ Memory usage acceptable
  □ Dashboard accessible at all times
  □ Error handling works (graceful degradation)
  □ Config changes applied correctly
```

### Step 4.4: Deployment (1 hour)
```bash
# On Raspberry Pi:
docker-compose up -d
docker-compose logs app -f  # Monitor for errors
```

---

# 5. CONFIGURATION STRATEGY

## Configuration Hierarchy

```
Priority 1 (Highest): config.py (Machine-readable, persistent)
  ↓
Priority 2: Dashboard toggles (Runtime, session-level)
  ↓
Priority 3 (Lowest): MQTT commands (One-time, specific action)
```

## config.py ML Parameters

```python
# =====================================================
# MACHINE LEARNING MODELS CONFIGURATION
# =====================================================

# ─────────────────────────────────────────────────────
# VISION MODEL (YOLO Queen Bee Detection)
# ─────────────────────────────────────────────────────

# Enable/Disable vision model
ENABLE_VISION_MODEL = True

# Path to YOLO model file (PyTorch format)
VISION_MODEL_PATH = "models/best.pt"

# Confidence threshold (0.0-1.0): Only report detections above this confidence
VISION_CONFIDENCE_THRESHOLD = 0.7

# Process every N frames to balance CPU usage vs accuracy
# Values: 1 (every frame, most accurate), 3 (default), 5 (fastest)
VISION_PROCESS_EVERY_N_FRAMES = 3

# Inference timeout in seconds (kill if takes longer)
VISION_FRAME_TIMEOUT_SEC = 5

# MQTT topic for publishing vision detection results
TOPIC_VISION_RESULTS = "hive/vision/detection"

# ─────────────────────────────────────────────────────
# AUDIO MODEL (ML-based Queen Bee Sound Classification)
# ─────────────────────────────────────────────────────

# Enable/Disable audio model
ENABLE_AUDIO_MODEL = True

# Path to pre-trained audio model
AUDIO_MODEL_PATH = "ml_audio_model/queen_bee_model.pkl"

# Audio sampling rate in Hz (must match model training)
AUDIO_SAMPLE_RATE = 22050

# Default recording duration in seconds (can be overridden by dashboard)
AUDIO_RECORD_DURATION_SEC = 30

# Confidence threshold for classification (0.0-1.0)
AUDIO_CONFIDENCE_THRESHOLD = 0.6

# Save audio recordings to disk (True/False)
AUDIO_SAVE_RECORDINGS = False

# Directory to save audio recordings
AUDIO_RECORDINGS_DIR = "audio_recordings"

# MQTT topic for publishing audio classification results
TOPIC_AUDIO_RESULTS = "hive/audio/classification"
```

## Runtime Configuration Changes

### Dashboard Toggles (Session-level)
```
/api/ml/toggle (POST)
  - Temporarily enable/disable vision or audio
  - Resets on app restart
  - Does not modify config.py
```

### MQTT Commands (One-time actions)
```
hive/control/audio:
  payload: {"action": "record", "duration": 45}
  → Triggers audio recording for 45 seconds
  → Publishes result to hive/audio/classification
```

---

# 6. DASHBOARD INTEGRATION (ESSENTIAL ONLY)

## Dashboard Scope: Keep it SIMPLE

### What GOES on Dashboard ✅
```
1. Vision Model
   - ON/OFF toggle button
   - Last detection status (Yes/No)
   - Last confidence score
   - Timestamp of last detection

2. Audio Model
   - "Start Recording" button
   - Recording progress (timer + progress bar)
   - Last classification result (Queen Present/Absent)
   - Last confidence score

3. Status Indicators
   - Vision model: ● Green (detecting) / ○ Gray (disabled)
   - Audio model: ● Green (ready) / ⏺ Red (recording) / ⚠ Yellow (error)
```

### What STAYS OFF Dashboard ❌
```
❌ Audio playback controls
❌ Model re-training
❌ Threshold tuning (use config.py)
❌ Feature visualization
❌ Detailed metrics/charts
❌ Model version selection
```

### Essential API Endpoints

```
GET  /api/vision/status
     → {"enabled": bool, "last_detection": {...}, "timestamp": "..."}

POST /api/ml/toggle
     → {"type": "vision"|"audio"}
     → {"vision_enabled": bool} or {"audio_enabled": bool}

POST /api/audio/record
     → {"duration": 30}
     → {"classification": "queen_present", "confidence": 0.92}

GET  /api/ml/config
     → Returns current ML configuration (read-only)
```

### HTML Section (Single Card Design)

```html
<section class="ml-status">
    <h3>🤖 AI Models Status</h3>
    
    <div class="status-item">
        <span class="indicator" id="vision-indicator">●</span>
        <span>Vision Detection</span>
        <button onclick="toggleVision()">Toggle</button>
        <span class="result" id="vision-text">Last: Queen Detected (0.89)</span>
    </div>
    
    <div class="status-item">
        <span class="indicator" id="audio-indicator">●</span>
        <span>Audio Analysis</span>
        <button onclick="recordAudio()">Record 30s</button>
        <div id="audio-progress" style="display:none">
            <progress id="prog" max="30" value="0"></progress>
            <span id="timer">30s</span>
        </div>
        <span class="result" id="audio-text">Ready</span>
    </div>
</section>
```

---

# 7. DEPLOYMENT & VERIFICATION

## Pre-Deployment Checklist

```
Code Structure:
  ☐ ml_vision_model/vision_processor.py created
  ☐ ml_audio_model/audio_processor.py created
  ☐ config.py updated with ML parameters
  ☐ app.py updated with ML integration
  ☐ dashboard_app.py updated with new endpoints
  ☐ dashboard/templates/index.html updated
  ☐ dashboard/static/app.js updated

Models:
  ☐ best.pt in models/ directory
  ☐ queen_bee_model.pkl in ml_audio_model/
  ☐ Model files copied to Docker image

Dependencies:
  ☐ ultralytics (YOLO)
  ☐ librosa (Audio processing)
  ☐ scikit-learn (ML model loading)
  ☐ sounddevice (Microphone recording)
  ☐ All added to requirements.txt

Testing:
  ☐ Test scripts run successfully
  ☐ Vision model processes frames
  ☐ Audio model records and classifies
  ☐ Dashboard endpoints respond
  ☐ MQTT publishing works

Docker:
  ☐ Dockerfile.edge updated
  ☐ docker-compose.yml verified
  ☐ Volume mounts correct
  ☐ Build successful
```

## Deployment Steps

### Step 1: Verify Models Exist
```bash
ls -la models/best.pt
ls -la ml_audio_model/queen_bee_model.pkl
```

### Step 2: Update Dependencies
```bash
pip install ultralytics librosa scikit-learn sounddevice
```

### Step 3: Test on Local Machine
```bash
python scripts/test_vision_model.py
python scripts/test_audio_model.py
```

### Step 4: Deploy to Docker
```bash
docker-compose build edge
docker-compose up -d edge
docker-compose logs edge -f
```

### Step 5: Verify on Dashboard
```
1. Open http://localhost:5000
2. Check Vision Detection status
3. Click "Record 30s" for audio
4. Verify results appear
```

---

# 8. GIT COMMIT STRATEGY

## Commits (Organized by feature, not time)

### Commit 1: Create ML Integration Wrappers
```
commit: "Add ML model integration wrappers"
files:
  - ml_vision_model/vision_processor.py (NEW)
  - ml_audio_model/audio_processor.py (NEW)
description: "Wrapper classes for vision (YOLO) and audio (scikit-learn) models"
```

### Commit 2: Update Configuration
```
commit: "Add ML configuration parameters"
files:
  - config.py (MODIFIED)
  - models/ directory (CREATE)
description: "Add configurable ML model settings to config.py"
```

### Commit 3: Integrate ML into Main App
```
commit: "Integrate ML models into main application"
files:
  - app.py (MODIFIED)
description: "Add vision thread, audio recording, MQTT publishing for ML results"
```

### Commit 4: Update Dashboard
```
commit: "Add ML model controls to dashboard"
files:
  - dashboard/dashboard_app.py (MODIFIED)
  - dashboard/templates/index.html (MODIFIED)
  - dashboard/static/app.js (MODIFIED)
  - dashboard/static/styles.css (MODIFIED)
description: "Add API endpoints and UI for vision/audio model control"
```

### Commit 5: Add Testing & Deployment
```
commit: "Add ML model testing scripts and Docker support"
files:
  - scripts/test_vision_model.py (NEW)
  - scripts/test_audio_model.py (NEW)
  - Dockerfile.edge (MODIFIED)
  - requirements.txt (MODIFIED)
description: "Testing scripts and Docker configuration for ML models"
```

### Commit 6: Documentation
```
commit: "Add comprehensive ML integration documentation"
files:
  - docs/ML_INTEGRATION_PLAN.md (MODIFIED - THIS FILE)
  - docs/ML_MODELS_GUIDE.md (NEW)
description: "Complete documentation for ML model integration, architecture, and deployment"
```

---

# 9. RESOURCE OPTIMIZATION FOR RASPBERRY PI 4

## CPU Management
```
Vision Processing:
  - Frame: 640x480
  - Process 1 out of every 3 frames (≈6-7 FPS)
  - Inference time: ~50-100ms per frame
  - CPU usage: 15-25% (one core)

Audio Processing:
  - Recording: 22050 Hz sample rate
  - Duration: 30 seconds (on-demand)
  - Feature extraction: ~500ms per recording
  - CPU usage: Spike to 40%, then drops

Estimated Total Load:
  - Baseline (no ML): ~10-15%
  - With Vision: ~25-35%
  - With Audio Recording: ~40-50% (temporary, 30s only)
  - Safe operating range
```

## Memory Management
```
Vision Model (YOLO):
  - Model size: ~200-300 MB (loaded once)
  - Per-frame buffer: ~3-5 MB
  - Total: ~350 MB

Audio Model (scikit-learn):
  - Model size: ~20-50 MB
  - Recording buffer: ~10 MB max
  - Total: ~80 MB

Total ML Memory: ~450 MB (out of 4GB = 11%)
Safe margin: ✅ Plenty of headroom
```

## Disk I/O Optimization
```
Vision:
  - Write MQTT packets only (not images by default)
  - No disk I/O during detection

Audio:
  - Optional: Save recordings (disabled by default)
  - If enabled: 30s @ 22050 Hz ≈ 1.3 MB per recording
```

---

# 10. ERROR HANDLING STRATEGY

## Vision Model Failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Model file missing | On app startup | Log error, disable vision, continue |
| Frame timeout (>5s) | During processing | Skip frame, log warning, continue |
| GPU memory full | During inference | Reduce frame size, retry |
| Camera disconnect | Frame read returns None | Log warning, keep thread running |

## Audio Model Failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Model file missing | On initialization | Log error, disable audio, continue |
| Microphone not found | During record() | Return error to dashboard, allow retry |
| Recording timeout | If exceeds duration+5s | Force stop, process recorded data |
| Feature extraction fail | During MFCC extraction | Return "Error: Cannot process", log details |

## Graceful Degradation

```
Scenario 1: Vision model crashes
  Result: Vision disabled, system continues
  Impact: Audio + sensors still functional

Scenario 2: Audio recording fails
  Result: Return error to dashboard
  Impact: User can retry or disable audio

Scenario 3: Microphone disconnected
  Result: Audio disabled gracefully
  Impact: Vision + sensors still functional

Scenario 4: Insufficient CPU
  Result: Automatically throttle (process fewer frames)
  Impact: Accuracy reduced, but system stable
```

---

# APPENDIX A: REQUIRED DEPENDENCIES

```
# requirements.txt additions
ultralytics==8.0.0          # YOLO
librosa==0.10.0             # Audio feature extraction
scikit-learn==1.3.0         # ML model loading
sounddevice==0.4.6          # Microphone recording
numpy>=1.21.0               # Already installed
opencv-python>=4.5.0        # Already installed
scipy>=1.7.0                # For audio processing
```

---

# APPENDIX B: DIRECTORY STRUCTURE (FINAL)

```
smart-hive-ai/
├── app.py                              ✏️ MODIFIED (ML integration)
├── config.py                           ✏️ MODIFIED (ML parameters)
├── dashboard/
│   ├── dashboard_app.py               ✏️ MODIFIED (ML endpoints)
│   ├── templates/
│   │   └── index.html                 ✏️ MODIFIED (ML UI)
│   └── static/
│       ├── app.js                     ✏️ MODIFIED (ML controls)
│       └── styles.css                 ✏️ MODIFIED (ML styling)
├── models/
│   ├── best.pt                        📦 (YOLO model)
│   └── queen_bee.tflite                (existing TFLite model)
├── ml_vision_model/
│   ├── best.pt                        (YOLOv8 model)
│   ├── camera_yolo_noir.py            (reference only)
│   └── vision_processor.py            ✨ NEW (integration wrapper)
├── ml_audio_model/
│   ├── enhanced_queen_bee_detection.py (reference only)
│   ├── queen_bee_model.pkl            (pre-trained model)
│   └── audio_processor.py             ✨ NEW (integration wrapper)
├── scripts/
│   ├── test_vision_model.py           ✨ NEW (testing)
│   └── test_audio_model.py            ✨ NEW (testing)
├── docs/
│   ├── ML_INTEGRATION_PLAN.md         📝 THIS FILE
│   ├── ML_MODELS_GUIDE.md             ✨ NEW (detailed guide)
│   └── ... (existing docs)
├── Dockerfile.edge                     ✏️ MODIFIED (ML support)
├── requirements.txt                    ✏️ MODIFIED (ML dependencies)
└── docker-compose.yml                  (no changes needed)
```

---

# SUCCESS CRITERIA

✅ **Week 1 Complete When:**

1. **Code Ready**
   - [ ] ml_vision_model/vision_processor.py fully functional
   - [ ] ml_audio_model/audio_processor.py fully functional
   - [ ] app.py integrates both ML pipelines
   - [ ] dashboard_app.py has all ML endpoints
   - [ ] All code committed to git

2. **Tested**
   - [ ] Vision model detects in test frames
   - [ ] Audio model classifies test recordings
   - [ ] Dashboard shows ML controls
   - [ ] MQTT publishing works
   - [ ] No errors on Pi startup

3. **Documented**
   - [ ] ML_INTEGRATION_PLAN.md complete (this file)
   - [ ] Code has professional headers and docstrings
   - [ ] README updated with ML usage instructions
   - [ ] Configuration documented

4. **Deployed**
   - [ ] Docker containers build successfully
   - [ ] System runs on Raspberry Pi 4
   - [ ] All dashboards accessible
   - [ ] Historical data in DynamoDB

---

**END OF ML INTEGRATION PLAN**
