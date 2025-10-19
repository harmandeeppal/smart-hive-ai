# USB Camera Troubleshooting Guide
### Smart Hive AI - Video Feed Setup

## Problem
Dashboard shows "Camera Not Available" error with red text.

## Architecture Overview
```
USB Camera → /dev/video0 → edge-app container → app.py → /video_feed endpoint → dashboard
```

## Quick Diagnostic Commands

### 1️⃣ Check Camera Hardware (Run on Raspberry Pi)
```bash
# Check if camera is detected by system
ls -l /dev/video*
# Expected output: crw-rw----+ 1 root video ... /dev/video0

# List USB devices to see camera
lsusb
# Should show your USB camera (e.g., "Logitech, Inc. Webcam")

# Check camera capabilities
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext
```

**Expected Results:**
- `/dev/video0` exists
- Permissions show `video` group has read/write access
- `v4l2-ctl` shows camera with supported formats (YUYV, MJPEG, etc.)

---

### 2️⃣ Test Camera Outside Docker (Run on Raspberry Pi)
```bash
# Test with Python directly on host
python3 -c "
import cv2
import time

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
print(f'Camera opened: {cap.isOpened()}')

if cap.isOpened():
    # Wait for camera warmup
    time.sleep(2)
    ret, frame = cap.read()
    print(f'Frame captured: {ret}')
    if ret:
        print(f'Frame shape: {frame.shape}')
        print('✅ SUCCESS - Camera working!')
    else:
        print('❌ FAILED - Camera opened but cannot capture frames')
else:
    print('❌ FAILED - Cannot open camera')
cap.release()
"
```

**Expected Results:**
- `Camera opened: True`
- `Frame captured: True`
- `Frame shape: (480, 640, 3)` or similar
- `✅ SUCCESS` message

---

### 3️⃣ Check Docker Container Access (Run on Raspberry Pi)
```bash
# Check if edge-app container is running
docker ps | grep edge-app

# Check container logs for camera errors
docker logs smart-hive-edge | grep -i camera

# Check last 100 lines of logs
docker logs --tail 100 smart-hive-edge

# Enter container and check camera device
docker exec -it smart-hive-edge /bin/bash
ls -l /dev/video*  # Should show /dev/video0
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
exit
```

**Expected Results:**
- Container is running (status: Up)
- Logs show: `✅ Camera fully operational`
- `/dev/video0` exists inside container
- `VideoCapture(0).isOpened()` returns `True`

---

### 4️⃣ Test Video Feed Endpoint (Run on Raspberry Pi)
```bash
# Test directly from Raspberry Pi
curl -I http://localhost:5001/video_feed

# Should return:
# HTTP/1.1 200 OK
# Content-Type: multipart/x-mixed-replace; boundary=frame

# Save a test frame
timeout 5 curl http://localhost:5001/video_feed --output test_frame.jpg
```

**Expected Results:**
- HTTP 200 OK response
- Content-Type shows `multipart/x-mixed-replace`
- Test frame saved successfully (should be ~50-100KB)

---

### 5️⃣ Test Dashboard Proxy (Run from your computer)
```bash
# Replace IP with your Raspberry Pi's IP address
curl -I http://192.168.88.16:5000/video_feed

# Should proxy to edge-app:5001
```

---

## Common Issues and Solutions

### Issue 1: `/dev/video0` does not exist
**Symptoms:**
- `ls /dev/video*` returns "No such file or directory"
- `lsusb` doesn't show camera

**Solutions:**
1. **Reconnect USB camera** - Unplug and plug back in
2. **Try different USB port** - Some ports may have power issues
3. **Check camera power** - USB cameras need sufficient power
4. **Verify camera works on Windows/Mac** - Rule out hardware failure
5. **Check `dmesg` output:** 
   ```bash
   dmesg | grep -i video
   dmesg | grep -i usb
   ```

---

### Issue 2: Permission denied errors
**Symptoms:**
- Camera detected but Python can't open it
- "Permission denied" in logs
- `/dev/video0` shows wrong permissions

**Solutions:**
1. **Add user to video group:**
   ```bash
   sudo usermod -aG video $USER
   sudo usermod -aG video pi  # if using pi user
   ```

2. **Reboot after adding to group:**
   ```bash
   sudo reboot
   ```

3. **Set proper permissions (if needed):**
   ```bash
   sudo chmod 666 /dev/video0
   ```

---

### Issue 3: Camera works on host but not in container
**Symptoms:**
- `python3` test on Raspberry Pi succeeds
- Container logs show camera initialization failed
- `/dev/video0` missing inside container

**Solutions:**
1. **Verify docker-compose.yml device mapping:**
   ```yaml
   devices:
     - "/dev/video0:/dev/video0"
   ```

2. **Check privileged mode is enabled:**
   ```yaml
   privileged: true
   ```

3. **Restart container:**
   ```bash
   cd ~/smart-hive-ai
   docker-compose restart edge-app
   ```

4. **Rebuild container (if code changed):**
   ```bash
   docker-compose down edge-app
   docker-compose build --no-cache edge-app
   docker-compose up -d edge-app
   docker logs -f smart-hive-edge
   ```

---

### Issue 4: Multiple video devices (video0, video1, video10, etc.)
**Symptoms:**
- `ls /dev/video*` shows multiple devices
- Camera at wrong index

**Solutions:**
1. **Identify correct camera:**
   ```bash
   v4l2-ctl --list-devices
   ```

2. **Update config.py:**
   ```python
   CAMERA_DEVICE_INDEX = 0  # Try 0, 1, 2, etc.
   ```

3. **Restart edge-app:**
   ```bash
   docker-compose restart edge-app
   ```

---

### Issue 5: Camera shows black frames or "Cannot capture frames"
**Symptoms:**
- Camera opens successfully
- `isOpened()` returns `True`
- But frames are all black or `read()` returns `False`

**Solutions:**
1. **Wait for camera warmup** - USB cameras need 2-3 seconds to initialize
2. **Check lighting** - Make sure camera has adequate lighting
3. **Try different backend:**
   - Code now automatically tries V4L2 and ANY backends
   - Check logs to see which backend succeeded

4. **Check camera format support:**
   ```bash
   v4l2-ctl -d /dev/video0 --list-formats-ext
   ```

5. **Test with fswebcam:**
   ```bash
   sudo apt-get install fswebcam
   fswebcam -d /dev/video0 -r 640x480 test.jpg
   ```

---

### Issue 6: "Camera Not Available" message persists after fixes
**Symptoms:**
- Camera works in tests
- Container logs show success
- Dashboard still shows error

**Solutions:**
1. **Hard refresh browser:**
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

2. **Clear browser cache:**
   - Open DevTools (F12)
   - Right-click refresh button → "Empty Cache and Hard Reload"

3. **Check dashboard container:**
   ```bash
   docker logs smart-hive-dashboard | grep video
   ```

4. **Restart dashboard:**
   ```bash
   docker-compose restart dashboard
   ```

---

## Configuration Settings

### In config.py:
```python
# Camera Configuration
CAMERA_TYPE = "USB"              # Use "USB" for USB cameras
CAMERA_DEVICE_INDEX = 0          # Usually 0 for first USB camera
CAMERA_WIDTH = 640               # Resolution width
CAMERA_HEIGHT = 480              # Resolution height

# Video Stream Settings
VIDEO_STREAM_FPS = 20            # Frames per second (lower = less CPU)
```

### Recommended Settings:
- **640x480 @ 20 FPS** - Good balance (default)
- **320x240 @ 15 FPS** - Lower resource usage
- **1280x720 @ 10 FPS** - Higher quality, more CPU

---

## Enhanced Logging in Latest Version

The updated code includes verbose logging during camera initialization:

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

---

## Quick Fix Workflow

1. **Run diagnostic commands** (sections 1-4 above)
2. **Identify which step fails**
3. **Apply corresponding solution**
4. **Rebuild container** (if code/config changed):
   ```bash
   cd ~/smart-hive-ai
   git pull origin feature/audio-windowed-inference
   docker-compose build --no-cache edge-app
   docker-compose up -d edge-app
   docker logs -f smart-hive-edge
   ```
5. **Verify success** - Look for ✅ messages in logs
6. **Hard refresh dashboard** (Ctrl+Shift+R)

---

## Testing Video Feed Without Dashboard

If you want to view the video feed directly without the dashboard:

1. **In web browser, navigate to:**
   ```
   http://192.168.88.16:5001/video_feed
   ```
   (Replace IP with your Raspberry Pi's IP)

2. **Should see live video stream** - If this works but dashboard doesn't, the issue is with the dashboard proxy

---

## Need More Help?

Check these files for additional context:
- `CAMERA_DEBUGGING_COMMANDS.md` - Command reference
- `docs/TROUBLESHOOTING.md` - General troubleshooting
- `docs/VIDEO_STREAM_CONFIGURATION.md` - Video configuration guide

---

## Summary Checklist

- [ ] Camera detected: `ls -l /dev/video0` shows device
- [ ] Permissions OK: User in `video` group
- [ ] Host test passes: `python3 -c "import cv2..."` succeeds
- [ ] Container access: `/dev/video0` exists in container
- [ ] Container test passes: Camera opens inside container
- [ ] Logs show success: `✅ Camera fully operational`
- [ ] Endpoint works: `curl http://localhost:5001/video_feed` returns data
- [ ] Dashboard updated: Hard refresh browser
- [ ] Config correct: `CAMERA_DEVICE_INDEX` matches device
- [ ] Code updated: Latest version with enhanced logging

**Once all items are checked, camera should work!** 📷✅
