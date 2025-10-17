"""
Smart Hive AI - ML Models Quick Reference
2-Day Implementation Checklist & Configuration Reference
"""

# ═══════════════════════════════════════════════════════════════
# QUICK START: 2-DAY SPRINT CHECKLIST
# ═══════════════════════════════════════════════════════════════

## DAY 1: MORNING (2 hours) - Create Wrappers
─────────────────────────────────────────────
Objective: Create reusable ML processor wrappers

Tasks:
  ☐ Create ml_vision_model/vision_processor.py
    └─ Copy from ML_MODELS_IMPLEMENTATION_GUIDE.md
    └─ Test: python -m py_compile ml_vision_model/vision_processor.py
  
  ☐ Create ml_audio_model/audio_processor.py
    └─ Copy from ML_MODELS_IMPLEMENTATION_GUIDE.md
    └─ Test: python -m py_compile ml_audio_model/audio_processor.py
  
  ☐ Create scripts/test_vision_model.py
  
  ☐ Create scripts/test_audio_model.py
  
Time: 2 hours
Commits: 1 (WrapperCreation)


## DAY 1: AFTERNOON (3 hours) - Configuration & Integration
────────────────────────────────────────────────────────────
Objective: Configure models and integrate into main app

Tasks:
  ☐ Update config.py: Add ML parameters section
    └─ Copy config block from ML_INTEGRATION_PLAN.md Section 5
  
  ☐ Update app.py: Add ML initialization
    └─ Import VisionProcessor, AudioProcessor
    └─ Initialize in __init__
    └─ Start vision thread in start()
  
  ☐ Update app.py: Add vision loop (_vision_loop method)
    └─ Continuous frame capture
    └─ Process every N frames
    └─ Publish to MQTT
  
  ☐ Update app.py: Add audio recording method (record_audio)
    └─ Trigger from dashboard
    └─ Publish results
  
  ☐ Update requirements.txt: Add ML dependencies
    └─ ultralytics, librosa, scikit-learn, sounddevice
  
Time: 3 hours
Commits: 3
  - ConfigurationUpdate
  - MLIntegration_AppPy
  - DependenciesUpdate


## DAY 1: EVENING (1.5 hours) - Dashboard Integration
───────────────────────────────────────────────────────
Objective: Add ML controls to dashboard UI

Tasks:
  ☐ Update dashboard/dashboard_app.py
    └─ Add /api/vision/status endpoint
    └─ Add /api/audio/record endpoint
    └─ Add /api/ml/toggle endpoint
  
  ☐ Update dashboard/templates/index.html
    └─ Add ML section with status + buttons
  
  ☐ Update dashboard/static/app.js
    └─ Add toggleVisionModel() function
    └─ Add startAudioRecording() function
    └─ Add progress bar display
  
  ☐ Update dashboard/static/styles.css
    └─ Style ML section
    └─ Style recording progress bar
  
Time: 1.5 hours
Commits: 1 (DashboardMLIntegration)


## DAY 2: MORNING (2 hours) - Testing
──────────────────────────────────────
Objective: Verify all components work

Tasks:
  ☐ Test vision processor
    └─ python scripts/test_vision_model.py
  
  ☐ Test audio processor (feature extraction)
    └─ python scripts/test_audio_model.py
  
  ☐ Test app startup
    └─ python app.py
    └─ Check console for errors
  
  ☐ Test dashboard endpoints
    └─ curl http://localhost:5000/api/vision/status
    └─ curl -X POST http://localhost:5000/api/ml/toggle -H "Content-Type: application/json" -d '{"type":"vision"}'
  
  ☐ Test MQTT publishing
    └─ Subscribe to hive/vision/detection
    └─ Verify messages arrive

Time: 2 hours
Commits: 1 (TestingComplete)


## DAY 2: AFTERNOON (2 hours) - Docker & Deployment
──────────────────────────────────────────────────
Objective: Deploy to containers

Tasks:
  ☐ Update Dockerfile.edge
    └─ Add: RUN pip install ultralytics librosa scikit-learn sounddevice
    └─ Add: COPY ml_vision_model/ /app/ml_vision_model/
    └─ Add: COPY ml_audio_model/ /app/ml_audio_model/
    └─ Add: COPY models/ /app/models/
    └─ Add: RUN mkdir -p /app/audio_recordings
  
  ☐ Build Docker image
    └─ docker-compose build edge
  
  ☐ Run containers
    └─ docker-compose up -d edge
    └─ docker-compose logs edge -f
  
  ☐ Verify on Raspberry Pi
    └─ Open http://pi-ip:5000
    └─ Check Vision + Audio controls
    └─ Try recording
  
  ☐ Verify data in DynamoDB
    └─ Check hive/vision/detection messages
    └─ Check hive/audio/classification messages

Time: 2 hours
Commits: 2
  - DockerSupport
  - DeploymentComplete


## DAY 2: EVENING (1 hour) - Documentation & Final
─────────────────────────────────────────────────
Objective: Document and commit everything

Tasks:
  ☐ Update README.md with ML usage
    └─ Add "AI Models" section
    └─ Configuration examples
  
  ☐ Create FINAL git commit
    └─ git add -A
    └─ git commit -m "Complete ML models integration"
    └─ git push
  
  ☐ Update docs/ML_IMPLEMENTATION_CHECKLIST.md
    └─ Mark all items complete
  
  ☐ Final verification
    └─ All tests pass
    └─ Dashboard responsive
    └─ No console errors

Time: 1 hour
Commits: 1 (FinalDocumentation)


# ═══════════════════════════════════════════════════════════════
# CONFIGURATION REFERENCE
# ═══════════════════════════════════════════════════════════════

## Copy to config.py (Section: ML Models Configuration)

```python
# =====================================================
# MACHINE LEARNING MODELS CONFIGURATION
# =====================================================

# ─────────────────────────────────────────────────────
# VISION MODEL (YOLO Queen Bee Detection)
# ─────────────────────────────────────────────────────

# Enable/Disable vision model entirely
ENABLE_VISION_MODEL = True

# Path to YOLO model file (PyTorch format)
VISION_MODEL_PATH = "models/best.pt"

# Minimum confidence threshold for detection (0.0-1.0)
# Higher = more conservative, fewer false positives
# Recommended: 0.6-0.8
VISION_CONFIDENCE_THRESHOLD = 0.7

# Process every N frames (balance accuracy vs CPU)
# 1 = every frame (most accurate, ~20 FPS)
# 3 = every 3rd frame (balanced, ~7 FPS)
# 5 = every 5th frame (fastest, ~4 FPS)
VISION_PROCESS_EVERY_N_FRAMES = 3

# Inference timeout (seconds) - kill if takes longer
VISION_FRAME_TIMEOUT_SEC = 5

# MQTT topic for vision results
TOPIC_VISION_RESULTS = "hive/vision/detection"

# ─────────────────────────────────────────────────────
# AUDIO MODEL (ML-based Sound Classification)
# ─────────────────────────────────────────────────────

# Enable/Disable audio model entirely
ENABLE_AUDIO_MODEL = True

# Path to pre-trained audio classification model
AUDIO_MODEL_PATH = "ml_audio_model/queen_bee_model.pkl"

# Audio sample rate (Hz) - MUST match model training
AUDIO_SAMPLE_RATE = 22050

# Default recording duration (seconds)
# Can be overridden per recording
AUDIO_RECORD_DURATION_SEC = 30

# Minimum confidence for classification (0.0-1.0)
# Higher = more confident predictions
AUDIO_CONFIDENCE_THRESHOLD = 0.6

# Save audio recordings to disk
AUDIO_SAVE_RECORDINGS = False

# Where to save audio files if enabled
AUDIO_RECORDINGS_DIR = "audio_recordings"

# MQTT topic for audio results
TOPIC_AUDIO_RESULTS = "hive/audio/classification"
```


# ═══════════════════════════════════════════════════════════════
# DEPENDENCY INSTALLATION
# ═══════════════════════════════════════════════════════════════

## Quick Install
```bash
pip install ultralytics librosa scikit-learn sounddevice
```

## Add to requirements.txt
```
ultralytics==8.0.0
librosa==0.10.0
scikit-learn==1.3.0
sounddevice==0.4.6
```


# ═══════════════════════════════════════════════════════════════
# MQTT TOPICS & MESSAGE FORMAT
# ═══════════════════════════════════════════════════════════════

## Vision Detection Results
Topic: hive/vision/detection
Publish: Whenever queen is detected

Message Format:
```json
{
  "detected": true,
  "confidence": 0.87,
  "boxes": [[100, 50, 200, 150]],
  "timestamp": 1697500000.123,
  "inference_time_ms": 45.2
}
```

## Audio Classification Results
Topic: hive/audio/classification
Publish: After recording completes

Message Format:
```json
{
  "classification": "queen_present",
  "confidence": 0.92,
  "duration": 30,
  "timestamp": 1697500060.456
}
```


# ═══════════════════════════════════════════════════════════════
# DASHBOARD API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

## GET /api/vision/status
Returns current vision detection status

Response:
```json
{
  "enabled": true,
  "last_detection": {
    "detected": true,
    "confidence": 0.87,
    "boxes": [[100, 50, 200, 150]],
    "timestamp": 1697500000.123
  }
}
```

## POST /api/ml/toggle
Toggle model enable/disable

Request:
```json
{"type": "vision"}  # or "audio"
```

Response:
```json
{"vision_enabled": false}
```

## POST /api/audio/record
Start audio recording and classification

Request:
```json
{"duration": 30}  # seconds
```

Response:
```json
{
  "classification": "queen_present",
  "confidence": 0.92,
  "duration": 30,
  "timestamp": 1697500060.456
}
```

## GET /api/ml/config
Get current ML configuration (read-only)

Response:
```json
{
  "ENABLE_VISION_MODEL": true,
  "VISION_MODEL_PATH": "models/best.pt",
  "VISION_CONFIDENCE_THRESHOLD": 0.7,
  "VISION_PROCESS_EVERY_N_FRAMES": 3,
  "ENABLE_AUDIO_MODEL": true,
  "AUDIO_MODEL_PATH": "ml_audio_model/queen_bee_model.pkl",
  "AUDIO_SAMPLE_RATE": 22050,
  "AUDIO_RECORD_DURATION_SEC": 30
}
```


# ═══════════════════════════════════════════════════════════════
# TROUBLESHOOTING QUICK REFERENCE
# ═══════════════════════════════════════════════════════════════

## Problem: "Model file not found"
Solution:
  1. Check file path: ls -la models/best.pt
  2. Check VISION_MODEL_PATH in config.py
  3. Verify file is copied to Docker image

## Problem: Vision processing very slow
Solution:
  1. Increase VISION_PROCESS_EVERY_N_FRAMES (from 3 to 5)
  2. Reduce VISION_CONFIDENCE_THRESHOLD (more permissive)
  3. Monitor CPU: top command on Pi
  4. Check if other processes running

## Problem: "Microphone not found"
Solution:
  1. List audio devices: python -c "import sounddevice; print(sounddevice.query_devices())"
  2. Plug in USB microphone
  3. Check permissions: groups $USER (should include audio group)
  4. Try: sudo usermod -a -G audio $USER

## Problem: Dashboard buttons not responsive
Solution:
  1. Check browser console for JavaScript errors
  2. Verify endpoints exist: curl http://localhost:5000/api/vision/status
  3. Check Docker logs: docker-compose logs dashboard
  4. Restart containers: docker-compose restart

## Problem: MQTT messages not appearing
Solution:
  1. Check MQTT connection: mosquitto_sub -h localhost -t "hive/#"
  2. Verify app.py connects to AWS IoT
  3. Check app logs: docker-compose logs app
  4. Verify MQTT topics match config.py


# ═══════════════════════════════════════════════════════════════
# TESTING COMMANDS
# ═══════════════════════════════════════════════════════════════

## Test Vision Model
```bash
python scripts/test_vision_model.py
```
Expected: ✅ ALL VISION TESTS PASSED

## Test Audio Model
```bash
python scripts/test_audio_model.py
```
Expected: ✅ ALL AUDIO TESTS PASSED

## Test Main App
```bash
python app.py
```
Expected: No errors, shows "SmartHive System started"

## Test Dashboard Endpoints
```bash
# Check vision status
curl http://localhost:5000/api/vision/status

# Toggle vision
curl -X POST http://localhost:5000/api/ml/toggle \
  -H "Content-Type: application/json" \
  -d '{"type":"vision"}'

# Get config
curl http://localhost:5000/api/ml/config
```

## Test MQTT (from another terminal)
```bash
# Subscribe to all ML results
mosquitto_sub -h localhost -t "hive/vision/#"
mosquitto_sub -h localhost -t "hive/audio/#"
```


# ═══════════════════════════════════════════════════════════════
# GIT COMMITS SUMMARY
# ═══════════════════════════════════════════════════════════════

Day 1 Commits (4):
  1. "Add ML model integration wrappers" 
     - ml_vision_model/vision_processor.py
     - ml_audio_model/audio_processor.py

  2. "Add ML configuration parameters"
     - config.py (new ML section)
     - models/ directory created

  3. "Integrate ML models into main application"
     - app.py (vision thread, audio methods, MQTT publishing)

  4. "Add ML model controls to dashboard"
     - dashboard_app.py (new endpoints)
     - dashboard/templates/index.html (new section)
     - dashboard/static/app.js (new functions)
     - dashboard/static/styles.css (new styles)

Day 2 Commits (3):
  5. "Add ML model testing and Docker support"
     - scripts/test_vision_model.py
     - scripts/test_audio_model.py
     - Dockerfile.edge (ML dependencies + model files)
     - requirements.txt (updated)

  6. "Update documentation for ML integration"
     - README.md (ML section)
     - docs/ML_IMPLEMENTATION_CHECKLIST.md (this file)

  7. "Finalize ML integration deployment"
     - All tests passing
     - Docker builds successfully
     - Dashboard functional


# ═══════════════════════════════════════════════════════════════
# SUCCESS VERIFICATION CHECKLIST
# ═══════════════════════════════════════════════════════════════

✅ Completion Signs:

Code Ready:
  ☐ All 2 processor classes created (vision + audio)
  ☐ config.py has ML parameters section
  ☐ app.py integrates both processors
  ☐ dashboard_app.py has 3+ new endpoints
  ☐ Dashboard UI shows ML controls

Tested:
  ☐ test_vision_model.py passes
  ☐ test_audio_model.py passes
  ☐ app.py starts without errors
  ☐ Dashboard endpoints respond (curl tests)
  ☐ MQTT topics receive messages

Deployed:
  ☐ Docker image builds: docker build works
  ☐ Containers run: docker-compose up succeeds
  ☐ Dashboard accessible: http://localhost:5000
  ☐ ML controls visible and clickable
  ☐ All data flows to DynamoDB

Documented:
  ☐ config.py has ML settings comments
  ☐ Processor classes have docstrings
  ☐ API endpoints documented
  ☐ This checklist completed
  ☐ Git history shows all commits

Performance:
  ☐ Pi CPU stays below 50% under load
  ☐ Dashboard responsive (<2s response time)
  ☐ Vision detection runs continuously
  ☐ Audio recording completes in ~30s
  ☐ No memory leaks over 1 hour runtime


# ═══════════════════════════════════════════════════════════════
# FILE REFERENCES
# ═══════════════════════════════════════════════════════════════

Main Implementation Documents:
  → docs/ML_INTEGRATION_PLAN.md (Strategic plan, architecture)
  → docs/ML_MODELS_IMPLEMENTATION_GUIDE.md (Code templates, examples)
  → docs/ML_IMPLEMENTATION_CHECKLIST.md (THIS FILE - Quick reference)

Code Templates Location:
  → ml_vision_model/vision_processor.py (Template in implementation guide)
  → ml_audio_model/audio_processor.py (Template in implementation guide)

Configuration:
  → config.py (Add ML section from this document)

Testing:
  → scripts/test_vision_model.py (From implementation guide)
  → scripts/test_audio_model.py (From implementation guide)

Dashboard:
  → dashboard/templates/index.html (Add ML section)
  → dashboard/static/app.js (Add ML functions)
  → dashboard/static/styles.css (Add ML styles)


---
**End of Quick Reference - Ready to implement!**
"""
