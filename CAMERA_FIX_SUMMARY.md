# USB Camera Fix Summary
**Date:** October 19, 2025  
**Issue:** Dashboard showing "Camera Not Available" error  
**Status:** ✅ FIXED (needs deployment to Raspberry Pi)

---

## What Was Fixed

### 1. Enhanced Camera Initialization (`real_components.py`)
**Before:**
- Simple `VideoCapture(0)` call
- No retry logic
- Minimal error messages
- No warmup time for USB cameras

**After:**
- Multi-backend support (V4L2, CAP_ANY)
- 2-second camera warmup delay
- 5 retry attempts for frame capture
- Reduced buffer size for lower latency
- Detailed diagnostic logging
- Comprehensive error messages with troubleshooting hints

### 2. Improved Camera Status Reporting (`app.py`)
**Before:**
- Basic camera availability check
- Limited logging

**After:**
- Detailed status reporting to MQTT
- Resolution and backend information
- Helpful error messages
- Links to troubleshooting documentation

---

## New Documentation

### 📄 CAMERA_DEBUGGING_COMMANDS.md
Quick reference for diagnostic commands:
- Check camera hardware detection
- Test camera outside Docker
- Verify container access
- Test video feed endpoint
- Common issues and fixes

### 📄 USB_CAMERA_TROUBLESHOOTING.md
Comprehensive troubleshooting guide:
- Architecture overview
- Step-by-step diagnostics
- 6 common issues with solutions
- Configuration recommendations
- Quick fix workflow
- Testing procedures
- Summary checklist

---

## Code Changes Summary

### `real_components.py` - RealVisionProcessor class
```python
def _initialize_camera_with_retry(self, camera_index):
    """Try multiple camera backends and strategies"""
    backends = [
        (cv2.CAP_V4L2, "V4L2 (Video4Linux)"),  # Best for Linux/Raspberry Pi
        (cv2.CAP_ANY, "ANY (auto-detect)"),
    ]
    
    for backend, backend_name in backends:
        cap = cv2.VideoCapture(camera_index, backend)
        
        # Configure settings
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Low latency
        
        # Wait for warmup (USB cameras need this!)
        time.sleep(2)
        
        # Try multiple frame captures
        for attempt in range(5):
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                return cap  # Success!
```

### `app.py` - Enhanced camera status reporting
```python
def _check_camera_availability(self):
    """Check camera with detailed diagnostics"""
    if camera_works:
        print(f"✅ Camera fully operational")
        print(f"   Resolution: {width}x{height}")
        print(f"   Backend: {backend}")
        print(f"   Video feed available at: http://localhost:5001/video_feed")
        
        # Publish status to MQTT for dashboard
        self.mqtt_client.publish('hive/status/video', ...)
```

---

## How to Deploy

### On Your Raspberry Pi:

1. **Pull latest code:**
   ```bash
   cd ~/smart-hive-ai
   git pull origin feature/audio-windowed-inference
   ```

2. **Rebuild edge-app container:**
   ```bash
   docker-compose build --no-cache edge-app
   docker-compose up -d edge-app
   ```

3. **Watch logs to verify camera initialization:**
   ```bash
   docker logs -f smart-hive-edge
   ```

4. **Look for success messages:**
   ```
   📷 Attempting camera initialization (index 0)...
      Trying backend: V4L2 (Video4Linux)
      ⏳ Waiting for camera warmup (2 seconds)...
      ✅ Camera initialized successfully!
         Backend: V4L2 (Video4Linux)
         Resolution: 640x480
         Frame shape: (480, 640, 3)
   
   ✅ Camera fully operational
      Resolution: 640x480
      Backend: V4L2
      Video feed available at: http://localhost:5001/video_feed
   ```

5. **Hard refresh dashboard in browser:**
   - Press `Ctrl + Shift + R` (Windows/Linux)
   - Press `Cmd + Shift + R` (Mac)

---

## Expected Behavior After Fix

### ✅ Success Indicators:
1. Container logs show `✅ Camera fully operational`
2. Dashboard video feed shows live camera stream (not "Camera Not Available")
3. Video is smooth and responsive
4. No error messages in red text

### 🔧 If Still Not Working:

**Run diagnostic commands** from `CAMERA_DEBUGGING_COMMANDS.md`:

```bash
# 1. Check if camera is detected
ls -l /dev/video0

# 2. Test camera outside Docker
python3 -c "import cv2; cap = cv2.VideoCapture(0, cv2.CAP_V4L2); print(cap.isOpened())"

# 3. Check container logs
docker logs smart-hive-edge | grep -i camera

# 4. Test video feed endpoint
curl -I http://localhost:5001/video_feed
```

**Refer to:** `USB_CAMERA_TROUBLESHOOTING.md` for detailed solutions

---

## Common Issues Addressed

### Issue 1: Permission Denied
**Solution:** Add user to video group
```bash
sudo usermod -aG video $USER
sudo reboot
```

### Issue 2: Wrong Camera Index
**Solution:** Check available devices and update config.py
```bash
v4l2-ctl --list-devices
```
Then set `CAMERA_DEVICE_INDEX = 0` (or 1, 2, etc.)

### Issue 3: Camera Needs Warmup
**Solution:** ✅ Already fixed! Code now waits 2 seconds automatically

### Issue 4: First Frame Capture Fails
**Solution:** ✅ Already fixed! Code retries 5 times

### Issue 5: Wrong OpenCV Backend
**Solution:** ✅ Already fixed! Code tries V4L2 first, then auto-detect

---

## Testing Recommendations

### Test 1: Direct Video Feed Access
Open in browser: `http://192.168.88.16:5001/video_feed`
- Should see live video stream directly (bypasses dashboard)

### Test 2: Dashboard View
Open dashboard: `http://192.168.88.16:5000`
- Click "Video: ON" toggle
- Should see live video in "AI Vision and Live Video Feed" panel

### Test 3: AI Vision Toggle
- Turn "AI Vision: ON"
- Should see YOLO bounding boxes overlay (if objects detected)
- Turn "AI Vision: OFF"
- Should see clean video feed without overlays

---

## Configuration Options

### In `config.py`:

```python
# Camera Configuration
CAMERA_TYPE = "USB"              # "USB" for USB cameras
CAMERA_DEVICE_INDEX = 0          # Try 0, 1, 2 if multiple cameras
CAMERA_WIDTH = 640               # Resolution
CAMERA_HEIGHT = 480

# Video Stream Settings
VIDEO_STREAM_FPS = 20            # Lower = less CPU usage
```

### Recommended Settings:

| Use Case | Resolution | FPS | CPU Usage |
|----------|-----------|-----|-----------|
| **Default** | 640x480 | 20 | Medium |
| **Low Power** | 320x240 | 15 | Low |
| **High Quality** | 1280x720 | 10 | High |

---

## Architecture Flow

```
┌─────────────┐
│ USB Camera  │ 
└──────┬──────┘
       │
       │ /dev/video0
       ↓
┌─────────────────────┐
│ Raspberry Pi OS     │
│ (Host System)       │
└──────┬──────────────┘
       │
       │ Docker device mapping
       ↓
┌─────────────────────┐
│ edge-app container  │
│ - app.py            │
│ - real_components.py│
└──────┬──────────────┘
       │
       │ HTTP endpoint
       │ /video_feed (port 5001)
       ↓
┌─────────────────────┐
│ dashboard container │
│ - Proxy to edge-app │
└──────┬──────────────┘
       │
       │ HTTP (port 5000)
       ↓
┌─────────────────────┐
│ Your Web Browser    │
│ http://Pi-IP:5000   │
└─────────────────────┘
```

---

## Key Improvements in This Fix

1. **Robustness:** Handles camera initialization failures gracefully
2. **Diagnostics:** Provides detailed error messages and logs
3. **Compatibility:** Works with different USB camera models
4. **Performance:** Reduced buffer size for lower latency
5. **Reliability:** Retry logic ensures camera captures successfully
6. **User Experience:** Clear error messages guide troubleshooting
7. **Documentation:** Comprehensive guides for common issues

---

## Files Modified

✅ `real_components.py` - Enhanced camera initialization  
✅ `app.py` - Improved status reporting  
✅ `CAMERA_DEBUGGING_COMMANDS.md` - NEW diagnostic commands reference  
✅ `USB_CAMERA_TROUBLESHOOTING.md` - NEW comprehensive troubleshooting guide

---

## Next Steps

1. **Deploy to Raspberry Pi** (commands above)
2. **Verify camera works** (check logs)
3. **Test video feed** (access dashboard)
4. **If issues persist:** Follow `USB_CAMERA_TROUBLESHOOTING.md`

---

## Success Criteria

- [ ] Camera detected: `/dev/video0` exists
- [ ] Container logs: `✅ Camera fully operational`
- [ ] Video endpoint works: `curl http://localhost:5001/video_feed` returns data
- [ ] Dashboard shows live video (not error message)
- [ ] Can toggle Video ON/OFF successfully
- [ ] Can toggle AI Vision ON/OFF successfully

**When all checkboxes are ticked, camera is fully operational!** 📷✅

---

## Support

If you encounter issues not covered in the troubleshooting guides:
1. Check container logs: `docker logs smart-hive-edge`
2. Run diagnostic commands from `CAMERA_DEBUGGING_COMMANDS.md`
3. Follow solutions in `USB_CAMERA_TROUBLESHOOTING.md`
4. Check Docker device mapping in `docker-compose.yml`

**The enhanced logging will guide you to the exact issue!**
