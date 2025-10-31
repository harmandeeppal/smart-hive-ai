# Camera Service Guide

Use this guide to configure the USB camera stream, run diagnostics, and resolve common issues surfaced in the dashboard.

## Stream Configuration (`config.py`)
| Setting | Description | Default |
| --- | --- | --- |
| `CAMERA_TYPE` | `"USB"` for webcams, `"CSI"` for ribbon-cable cameras. | `"USB"` |
| `CAMERA_DEVICE_INDEX` | Index passed to OpenCV (0 for the first detected camera). | `0` |
| `CAMERA_WIDTH` / `CAMERA_HEIGHT` | Capture resolution in pixels. | `640` × `480` |
| `VIDEO_STREAM_FPS` | Target frames per second for MJPEG output. | `20` |
| `VISION_PROCESS_EVERY_N_FRAMES` | Frequency for handing frames to the optional vision service. | `3` |

After adjusting these values, rebuild and restart the edge container:

```bash
docker compose build --no-cache smart-hive-edge
docker compose up -d smart-hive-edge
```

### Performance Tips
- Keep 640×480 at 15–20 FPS for a good balance between clarity and CPU load.
- Plug cameras directly into the Pi rather than through unpowered hubs.
- Disable the vision service (set `ENABLE_VISION_MODEL = False` and remove the container) if you only require streaming—this saves CPU and memory.

## Diagnostics Checklist (run on the Raspberry Pi)
```bash
# 1. Detect video devices and permissions
ls -l /dev/video*

# 2. Verify USB enumeration
lsusb

# 3. Inspect supported formats/resolutions
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext
```

### Test Capture Outside Docker
```bash
python3 -c "
import cv2, time
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
print('Camera opened:', cap.isOpened())
time.sleep(2)
ret, frame = cap.read()
print('Frame captured:', ret, frame.shape if ret else None)
cap.release()
"
```
If `ret` is `False`, the problem is hardware or OS-level—check cables, power, and `sudo raspi-config` camera settings.

## Container-Level Checks
```bash
docker ps | grep smart-hive-edge
docker logs smart-hive-edge | grep -i camera
docker exec -it smart-hive-edge /bin/bash
```
Inside the container:
```bash
ls -l /dev/video*
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera opened:', cap.isOpened())"
exit
```
If `/dev/video0` is missing inside the container, confirm the `devices:` mapping exists in `docker-compose.yml` and restart the stack.

## Checking the Stream Endpoints
```bash
# Direct stream from the edge container
curl -I http://localhost:5001/video_feed
timeout 5 curl http://localhost:5001/video_feed --output test_frame.jpg

# Dashboard proxy
curl -I http://<pi-ip>:5000/video_feed
```
Expect a `200 OK` response with `Content-Type: multipart/x-mixed-replace; boundary=frame`. The downloaded JPEG should open without errors.

## Dashboard Integration
- The dashboard proxies requests to the edge service using the container hostname `smart-hive-edge`. Ensure `dashboard/dashboard_app.py` references `http://smart-hive-edge:5001/video_feed`.
- Clear the browser cache after deploying dashboard updates to avoid stale assets.
- If the dashboard shows a broken image icon, recheck the hostname and confirm the direct stream (`http://localhost:5001/video_feed`) works as expected.

## Common Remedies
1. **Permission denied** – add the `pi` user to the `video` group (`sudo usermod -a -G video pi`) and reboot.
2. **Multiple cameras** – change `CAMERA_DEVICE_INDEX` to target the correct device.
3. **Intermittent feed** – reduce `VIDEO_STREAM_FPS` or resolution and verify that no other process is accessing `/dev/video0`.
4. **Stream works locally but not via dashboard** – confirm the dashboard container is running, the proxy route is correct, and there are no mixed-content warnings if accessing over HTTPS.

## Restart Sequence
```bash
docker compose restart smart-hive-edge
docker logs -f smart-hive-edge
```
Look for `Camera initialized successfully` messages to confirm the service is back online.

Document any deviations (custom resolutions, additional diagnostics) in this guide so future operators have a single source of truth for camera maintenance.
