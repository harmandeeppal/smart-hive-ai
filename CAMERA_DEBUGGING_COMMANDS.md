# USB Camera Debugging Commands

## Commands to run on Raspberry Pi to diagnose camera issues

### 1. Check if USB camera is detected
```bash
# List all video devices
ls -l /dev/video*

# Should show: /dev/video0 (your USB camera)
# Check permissions (should show root or video group)
```

### 2. Check if camera is working with v4l2
```bash
# Install v4l-utils if not already installed
sudo apt-get install v4l-utils

# List camera capabilities
v4l2-ctl --list-devices

# Show camera formats and resolutions
v4l2-ctl -d /dev/video0 --list-formats-ext
```

### 3. Test camera with Python directly
```bash
# Run on Raspberry Pi (outside containers)
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera opened:', cap.isOpened()); ret, frame = cap.read(); print('Frame captured:', ret, frame.shape if ret else 'Failed'); cap.release()"
```

### 4. Check Docker container logs
```bash
# Check edge-app logs for camera initialization errors
docker logs smart-hive-edge | grep -i camera

# Check last 50 lines of edge-app logs
docker logs --tail 50 smart-hive-edge

# Follow logs in real-time
docker logs -f smart-hive-edge
```

### 5. Test camera access inside container
```bash
# Enter the running edge-app container
docker exec -it smart-hive-edge /bin/bash

# Inside container: Check if /dev/video0 exists
ls -l /dev/video*

# Inside container: Test camera with Python
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera opened:', cap.isOpened())"

# Exit container
exit
```

### 6. Test video feed endpoint directly
```bash
# Test from Raspberry Pi itself
curl http://localhost:5001/video_feed --output test_frame.jpg

# Test from your computer (replace IP with your Pi's IP)
curl http://192.168.88.16:5001/video_feed --output test_frame.jpg
```

### 7. Check container device permissions
```bash
# Check if container has proper device access
docker exec smart-hive-edge ls -l /dev/video0

# Should show character device with proper permissions
# If "No such file or directory" - device mapping failed
```

### 8. Restart edge-app container
```bash
cd ~/smart-hive-ai
docker-compose restart edge-app

# Watch logs as it restarts
docker logs -f smart-hive-edge
```

### 9. Rebuild edge-app if needed
```bash
cd ~/smart-hive-ai
docker-compose down edge-app
docker-compose build --no-cache edge-app
docker-compose up -d edge-app
```

## Expected Outputs

### Success:
- `/dev/video0` exists with proper permissions
- `cap.isOpened()` returns `True`
- Frame captured successfully with shape like `(480, 640, 3)`
- Video feed endpoint returns MJPEG stream data
- Container logs show: "✅ Camera available: 640x480"

### Failure Indicators:
- `/dev/video0` not found
- `cap.isOpened()` returns `False`
- Frame capture fails or returns `None`
- Container logs show: "⚠️ Camera not available"
- Video feed returns "Camera Not Available" error

## Common Issues and Fixes

### Issue 1: Camera not detected at all
**Solution:** Reconnect USB camera, try different USB port, check `lsusb` output

### Issue 2: Permission denied on /dev/video0
**Solution:** Add user to `video` group: `sudo usermod -aG video $USER`

### Issue 3: Camera works outside container but not inside
**Solution:** Check docker-compose.yml has `devices: - "/dev/video0:/dev/video0"`

### Issue 4: Multiple video devices (video0, video1, etc.)
**Solution:** Try different indices in config.py: `CAMERA_DEVICE_INDEX = 1`

### Issue 5: Camera shows black frames
**Solution:** Wait 2-3 seconds for camera warmup, check lighting conditions

## Next Steps
Run these commands in order and report which ones succeed/fail!
