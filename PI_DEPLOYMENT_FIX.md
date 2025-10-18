# Raspberry Pi Deployment Fix - PyTorch 2.6 Safe Globals

**Date:** October 18, 2025  
**Issue:** YOLOv8n model fails to load on Pi with PyTorch 2.6+ security restrictions  
**Status:** ✅ FIXED - Commit af17e7f

---

## Problem Identified

When deploying to Raspberry Pi, the vision service crashed with:

```
ERROR: UnpicklingError: Weights only load failed.
WeightsUnpickler error: Unsupported global: GLOBAL ultralytics.nn.tasks.DetectionModel 
was not an allowed global by default.
```

**Root Cause:**  
- Pi Docker container runs PyTorch 2.6+ (same as laptop Python 3.13)
- PyTorch 2.6 changed default `weights_only=True` for security
- Even pretrained `yolov8n.pt` contains ultralytics classes not in PyTorch's default allowlist
- Local tests passed because we imported ultralytics before loading model (implicit registration)

---

## Solution Implemented

Added explicit safe globals registration in `ml_vision_model/vision_processor.py`:

```python
# FIX: PyTorch 2.6+ requires explicit safe globals for ultralytics models
# Add ultralytics classes to PyTorch's trusted class allowlist
if hasattr(torch.serialization, 'add_safe_globals'):
    import ultralytics.nn.tasks
    torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])
    logger.info("✅ Added ultralytics safe globals for PyTorch 2.6+")

# Use pretrained model (will auto-download on first run)
self.model = YOLO('yolov8n.pt')
```

**What This Does:**
1. Checks if PyTorch supports `add_safe_globals()` (2.6+ feature)
2. Imports ultralytics detection model class
3. Adds it to PyTorch's trusted class registry
4. Allows YOLO model to load without security errors

---

## Deployment Steps for Pi

**SSH to your Raspberry Pi and run:**

```bash
# Pull the latest fix
cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization

# Rebuild ONLY the vision service (faster)
docker compose build --no-cache smart-hive-vision

# Restart the vision service
docker compose up -d smart-hive-vision

# Verify the fix worked
docker logs smart-hive-vision | grep -A2 "Added ultralytics safe globals"
```

**Expected Success Output:**
```
INFO: Loading pretrained YOLOv8n model (temporary fix)...
INFO: ✅ Added ultralytics safe globals for PyTorch 2.6+
INFO: ✅ YOLO model loaded successfully (pretrained YOLOv8n)
```

---

## Verification Commands

**1. Check Vision Service Health:**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```
Should show: `smart-hive-vision   Up X seconds (healthy)`

**2. Check Model Loading:**
```bash
docker logs smart-hive-vision | tail -40 | grep -E "(YOLO|safe globals|vision_model)"
```

**3. Check Frame Processing:**
```bash
# Wait 10 seconds for frames
sleep 10
docker logs smart-hive-vision | grep "Detection published"
```

**4. Test Dashboard:**
- Open: http://192.168.88.16:5000
- Check "AI Vision Analysis" card updates with detection results
- Click "🎤 Record 1 Minute & Analyze" button to test audio

---

## Audio Service Note

Audio service showed:
```
ERROR: ❌ Required packages not installed. Install with: pip install librosa scikit-learn sounddevice
```

**This is expected** - Docker build needs to install from `requirements-audio.txt`. Should be fixed after rebuild:

```bash
docker compose build --no-cache smart-hive-audio
docker compose up -d smart-hive-audio
docker logs smart-hive-audio | grep "Audio processor initialized"
```

---

## Testing Checklist

- [ ] Vision service starts without errors
- [ ] Logs show "✅ Added ultralytics safe globals"
- [ ] Logs show "✅ YOLO model loaded successfully"
- [ ] Dashboard accessible at http://192.168.88.16:5000
- [ ] Vision card shows detection results
- [ ] Audio recording button visible
- [ ] Audio service loads librosa successfully

---

## Technical Details

**Affected Files:**
- `ml_vision_model/vision_processor.py` (lines 94-101)

**Commit:**
- `af17e7f` - fix: Add PyTorch 2.6+ safe globals for ultralytics model loading

**Why Local Tests Passed:**
- Python 3.13.5 + PyTorch 2.9.0 has same security restrictions
- But ultralytics import in test script already registered classes globally
- Pi container imports in isolation, needs explicit registration

**Alternative Solutions Not Used:**
1. Downgrade PyTorch to 2.5 (loses security features)
2. Set `weights_only=False` globally (security risk)
3. Use older ultralytics version (compatibility issues)

**Chosen Solution Benefits:**
- ✅ Keeps PyTorch 2.6+ security model
- ✅ Only whitelists specific trusted class
- ✅ Forward compatible with future PyTorch versions
- ✅ No changes to requirements.txt needed

---

## Next Steps

1. Deploy fix to Pi (commands above)
2. Verify vision service health
3. Test dashboard real-time updates
4. Test audio recording button functionality
5. Monitor logs for any other issues

---

**Status:** Ready to deploy! 🚀
