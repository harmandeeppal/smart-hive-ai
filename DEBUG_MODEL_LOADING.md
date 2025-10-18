# 🔍 Deep Dive: Why Can't Vision Processor Load the Model?

**The file IS there (6.0MB, real PyTorch ZIP), but vision_processor can't load it.**

This diagnostic will show us exactly why.

## Run This on Pi

```bash
cd ~/smart-hive-ai

# 1. Pull the latest code with improved error logging
git pull origin feature/project-cleanup-and-ml-reorganization

# 2. Rebuild vision service with new error messages
docker compose build --no-cache smart-hive-vision

# 3. Restart and see detailed error messages
docker compose restart smart-hive-vision
sleep 10

# 4. Get the FULL vision service logs with error details
echo "=== DETAILED VISION SERVICE LOGS ===" && \
docker logs smart-hive-vision | grep -A 20 "Loading YOLO model\|Failed to load\|Model file\|Working directory\|CWD\|Absolute" && \
echo "" && \
echo "=== ALL ERRORS AND WARNINGS ===" && \
docker logs smart-hive-vision | grep -i "error\|warning\|failed" | tail -20
```

## What This Will Show

If the file IS accessible but YOLO can't load it, we'll see:
- Actual working directory in Docker
- Absolute path being used
- Specific error from ultralytics YOLO loader
- Whether it's a permissions issue, file corruption, or YOLO compatibility

## Alternative: Test YOLO Loading Directly

Test if YOLO can load the model file at all:

```bash
docker exec smart-hive-vision python3 << 'EOF'
import os
import sys

print("=== PYTHON ENVIRONMENT ===")
print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")

model_path = "models/vision_model.pt"
print(f"\nChecking model file: {model_path}")
print(f"  Exists: {os.path.exists(model_path)}")
print(f"  Absolute: {os.path.abspath(model_path)}")
print(f"  Size: {os.path.getsize(model_path) if os.path.exists(model_path) else 'N/A'} bytes")
print(f"  Readable: {os.access(model_path, os.R_OK)}")

print("\n=== TRYING TO LOAD YOLO ===")
try:
    from ultralytics import YOLO
    print("✅ ultralytics imported")
    print(f"YOLO version: {YOLO.__module__}")
    
    print(f"\nLoading model from: {model_path}")
    model = YOLO(model_path)
    print("✅ MODEL LOADED SUCCESSFULLY!")
    print(f"Model info: {model}")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
EOF
```

This will tell us **exactly** why YOLO can't load the model (or if it can!).

## Expected Results

### ✅ If model loads successfully:
```
✅ ultralytics imported
Loading model from: models/vision_model.pt
✅ MODEL LOADED SUCCESSFULLY!
Model info: <ultralyticsResults>
```

### ❌ If YOLO fails to load:
```
❌ FAILED: <ExceptionType>
Error: <detailed error message>
Traceback: ...
```

Common issues and their fixes:
- **"Module not installed"** → Missing ultralytics in Dockerfile
- **"File not found"** → Path issue (but we know it's there)
- **"Corrupt file"** → Download issue
- **"Permission denied"** → File permissions (but test showed readable)
- **"Model format error"** → Incompatible YOLO version

---

Please run the diagnostic and share the output. This will show us **exactly** what's preventing the model from loading!
