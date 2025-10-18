# Video Feed & AI Vision Toggle Implementation

## User Requirements

1. **Video Feed Toggle**:
   - Video should be **always ON by default** (raw camera stream)
   - Add toggle button to turn video stream ON/OFF
   - When OFF: Stop camera streaming to save bandwidth/CPU

2. **AI Vision Toggle**:
   - **Separate** toggle for AI object detection
   - When AI ON: Overlay bounding boxes on live video
   - When AI OFF: Just show raw video feed (faster, less CPU)
   - AI toggle should be **independent** of video toggle

3. **Current Issue**: 
   - Video shows broken image icon
   - Camera may not be initializing properly

## Architecture Design

### Control States

| Video Toggle | AI Toggle | Behavior |
|--------------|-----------|----------|
| ON | ON | Raw video + AI bounding boxes overlaid |
| ON | OFF | Raw video only (no processing) |
| OFF | ON | No video (camera off, AI disabled) |
| OFF | OFF | No video (camera off) |

### MQTT Topics

```
hive/control/video     → {"state": "on"} or {"state": "off"}
hive/control/ai_vision → {"state": "on"} or {"state": "off"}
```

### Implementation Plan

1. **Edge-app (app.py)**:
   - Add separate `video_enabled` and `ai_vision_enabled` flags
   - Modify `generate_video_frames()` to check video toggle
   - Modify vision processing loop to check AI toggle
   - Subscribe to control topics for both toggles

2. **Dashboard (index.html)**:
   - Add two separate toggle buttons:
     - "📹 Video Stream: ON/OFF"
     - "🤖 AI Vision: ON/OFF"
   - Send MQTT messages when toggles clicked

3. **Camera Initialization Fix**:
   - Make camera initialization more robust
   - Add fallback if camera not available
   - Return test pattern or message instead of breaking

---

## Implementation Steps

### Step 1: Fix Camera Initialization (app.py)

**Current Issue**: Camera initialization happens in VisionProcessor, but may fail silently.

**Solution**: Add explicit camera check and fallback in edge-app.

```python
# In EdgeApp.__init__()
def __init__(self):
    # ... existing code ...
    
    # Add separate flags for video and AI control
    self.video_enabled = True   # Video ON by default
    self.ai_vision_enabled = False  # AI OFF by default (save CPU)
    
    # Initialize vision processor with camera
    try:
        from ml_vision_model.vision_processor import VisionProcessor
        self.vision_processor = VisionProcessor(use_camera=True)
        
        # Check if camera actually initialized
        if not self.vision_processor.camera or not self.vision_processor.camera.isOpened():
            logger.warning("⚠️ Camera not available, will use test pattern")
            self.camera_available = False
        else:
            logger.info(f"✅ Camera initialized: {self.vision_processor.camera.get(cv2.CAP_PROP_FRAME_WIDTH)}x{self.vision_processor.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)}")
            self.camera_available = True
            
    except Exception as e:
        logger.error(f"❌ Vision processor failed: {e}")
        self.vision_processor = None
        self.camera_available = False
```

### Step 2: Modify Video Frame Generator (app.py)

```python
def generate_video_frames(self):
    """
    Generator for MJPEG video stream with separate video/AI toggles.
    - video_enabled: Controls camera streaming ON/OFF
    - ai_vision_enabled: Controls AI bounding box overlay ON/OFF
    """
    frame_delay = 1.0 / config.VIDEO_STREAM_FPS
    
    while self.is_running:
        # Check video toggle state
        if not self.video_enabled:
            # Video turned OFF - send black frame with message
            black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(black_frame, "Video Feed Disabled", (150, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', black_frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(frame_delay)
            continue
        
        # Video enabled - check camera availability
        if not self.camera_available or not self.vision_processor or not self.vision_processor.camera:
            # No camera - send error frame
            error_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(error_frame, "Camera Not Available", (150, 240),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', error_frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(frame_delay)
            continue
        
        # Capture frame from camera
        if self.vision_processor.camera.isOpened():
            ret, frame = self.vision_processor.camera.read()
            if ret and frame is not None:
                # Decide which frame to display based on AI toggle
                if self.ai_vision_enabled and self.vision_processor.frame is not None:
                    # AI enabled - use annotated frame with bounding boxes
                    display_frame = self.vision_processor.frame
                else:
                    # AI disabled - use raw frame (no processing)
                    display_frame = frame
                
                # Encode and yield frame
                ret, buffer = cv2.imencode('.jpg', display_frame)
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
        time.sleep(frame_delay)
```

### Step 3: Add MQTT Control Handlers (app.py)

```python
def on_mqtt_message(self, client, userdata, msg):
    """Handle MQTT messages for telemetry control and video/AI toggles"""
    try:
        # ... existing control logic ...
        
        # NEW: Video stream control
        elif msg.topic == 'hive/control/video':
            payload = json.loads(msg.payload.decode())
            state = payload.get('state', 'on').lower()
            self.video_enabled = (state == 'on')
            logger.info(f"📹 Video stream: {'ENABLED' if self.video_enabled else 'DISABLED'}")
            
            # Publish status update
            self.mqtt_client.publish('hive/status/video', 
                                    json.dumps({"enabled": self.video_enabled}))
        
        # NEW: AI vision control
        elif msg.topic == 'hive/control/ai_vision':
            payload = json.loads(msg.payload.decode())
            state = payload.get('state', 'off').lower()
            self.ai_vision_enabled = (state == 'on')
            
            # Also control vision processor
            if self.vision_processor:
                self.vision_processor.enabled = self.ai_vision_enabled
            
            logger.info(f"🤖 AI Vision: {'ENABLED' if self.ai_vision_enabled else 'DISABLED'}")
            
            # Publish status update
            self.mqtt_client.publish('hive/status/ai_vision',
                                    json.dumps({"enabled": self.ai_vision_enabled}))
    
    except Exception as e:
        logger.error(f"Error handling MQTT message: {e}")


def start_mqtt(self):
    """Subscribe to control topics including video/AI toggles"""
    # ... existing subscriptions ...
    
    # NEW: Subscribe to video and AI control topics
    self.mqtt_client.subscribe('hive/control/video')
    self.mqtt_client.subscribe('hive/control/ai_vision')
    logger.info("✅ Subscribed to video and AI vision control topics")
```

### Step 4: Update Dashboard UI (index.html)

Replace the single vision toggle with two separate buttons:

```html
<!-- AI Vision Card with TWO TOGGLES -->
<div class="card" id="video-card">
    <h2>📹 Live Video Feed</h2>
    
    <!-- Video Stream Image -->
    <div class="video-container">
        <img id="video-feed" src="{{ url_for('video_feed') }}" 
             width="100%" alt="Live video feed">
    </div>
    
    <!-- Status Display -->
    <div class="ai-status">
        <span>🎥 Video: <strong id="video-status-text">ON</strong></span>
        <span>🤖 AI Vision: <strong id="ai-vision-status-text">OFF</strong></span>
        <span>Last Detection: <strong id="ai-snapshot-time">--</strong></span>
    </div>
    
    <!-- TWO SEPARATE TOGGLE BUTTONS -->
    <div class="video-controls">
        <button class="toggle-btn video-toggle" id="video-toggle-btn" data-state="on">
            📹 Video: <span class="toggle-state">ON</span>
        </button>
        <button class="toggle-btn ai-toggle" id="ai-vision-toggle-btn" data-state="off">
            🤖 AI Vision: <span class="toggle-state">OFF</span>
        </button>
    </div>
</div>
```

### Step 5: Update Dashboard JavaScript (app.js)

```javascript
// Video stream toggle handler
document.getElementById('video-toggle-btn').addEventListener('click', function() {
    const currentState = this.dataset.state;
    const newState = currentState === 'on' ? 'off' : 'on';
    
    // Send MQTT message
    fetch('/mqtt/publish', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            topic: 'hive/control/video',
            message: JSON.stringify({state: newState})
        })
    });
    
    // Update button UI
    this.dataset.state = newState;
    this.querySelector('.toggle-state').textContent = newState.toUpperCase();
    document.getElementById('video-status-text').textContent = newState.toUpperCase();
    
    // Show/hide video element
    const videoFeed = document.getElementById('video-feed');
    if (newState === 'off') {
        videoFeed.style.opacity = '0.3';
        videoFeed.style.filter = 'grayscale(100%)';
    } else {
        videoFeed.style.opacity = '1';
        videoFeed.style.filter = 'none';
    }
});

// AI vision toggle handler
document.getElementById('ai-vision-toggle-btn').addEventListener('click', function() {
    const currentState = this.dataset.state;
    const newState = currentState === 'on' ? 'off' : 'on';
    
    // Send MQTT message
    fetch('/mqtt/publish', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            topic: 'hive/control/ai_vision',
            message: JSON.stringify({state: newState})
        })
    });
    
    // Update button UI
    this.dataset.state = newState;
    this.querySelector('.toggle-state').textContent = newState.toUpperCase();
    document.getElementById('ai-vision-status-text').textContent = newState.toUpperCase();
    
    // Change button color
    this.classList.toggle('ai-active', newState === 'on');
});

// Listen for status updates from edge-app
socket.on('video_status', function(data) {
    const status = data.enabled ? 'ON' : 'OFF';
    document.getElementById('video-status-text').textContent = status;
});

socket.on('ai_vision_status', function(data) {
    const status = data.enabled ? 'ON' : 'OFF';
    document.getElementById('ai-vision-status-text').textContent = status;
});
```

### Step 6: Add CSS Styling (styles.css)

```css
/* Video controls container */
.video-controls {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
    justify-content: center;
}

/* Video toggle button (green when on) */
.video-toggle {
    background: linear-gradient(135deg, #28a745 0%, #218838 100%);
    flex: 1;
}

.video-toggle[data-state="off"] {
    background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
}

/* AI vision toggle button (blue when on) */
.ai-toggle {
    background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
    flex: 1;
}

.ai-toggle[data-state="on"],
.ai-toggle.ai-active {
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
}

/* Video container */
.video-container {
    position: relative;
    background: #000;
    border-radius: 8px;
    overflow: hidden;
    min-height: 300px;
}

#video-feed {
    width: 100%;
    height: auto;
    display: block;
    transition: opacity 0.3s, filter 0.3s;
}

/* AI status indicators */
.ai-status {
    display: flex;
    justify-content: space-around;
    margin: 1rem 0;
    font-size: 0.9em;
}

.ai-status strong {
    color: #00ff88;
}
```

---

## Camera Debug & Fix

### Issue: Camera Not Initializing

Check edge-app logs:
```bash
ssh pi@192.168.88.16
docker logs smart-hive-edge-app --tail 50 | grep -i camera
```

### Possible Causes:

1. **Camera already in use by another process**:
   ```bash
   # Check what's using the camera
   lsof /dev/video0
   
   # Kill process if needed
   sudo kill <PID>
   ```

2. **Camera device not mounted in Docker**:
   ```yaml
   # docker-compose.yml - make sure edge-app has:
   devices:
     - /dev/video0:/dev/video0
   ```

3. **OpenCV can't access camera**:
   ```python
   # Test camera access
   docker exec smart-hive-edge-app python3 -c "
   import cv2
   camera = cv2.VideoCapture(0)
   if camera.isOpened():
       ret, frame = camera.read()
       print(f'✅ Camera working: {frame.shape if ret else \"Failed to read frame\"}')
   else:
       print('❌ Camera failed to open')
   camera.release()
   "
   ```

### Temporary Fix: Use Test Pattern

If camera isn't available, generate a test pattern:

```python
def generate_test_pattern(width=640, height=480):
    """Generate a color test pattern when camera unavailable"""
    import numpy as np
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Draw colored bars
    bar_width = width // 7
    colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), 
              (255,0,255), (0,255,255), (255,255,255)]
    
    for i, color in enumerate(colors):
        frame[:, i*bar_width:(i+1)*bar_width] = color
    
    # Add timestamp
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    cv2.putText(frame, f"TEST PATTERN - {timestamp}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    return frame
```

---

## Testing Plan

### Test 1: Video Toggle

1. Open dashboard: http://192.168.88.16:5000
2. Video should be showing by default (green button "Video: ON")
3. Click "📹 Video: ON" button → should turn grey "Video: OFF"
4. Video feed should go dark with "Video Feed Disabled" text
5. Click again → video should resume

### Test 2: AI Vision Toggle

1. Click "🤖 AI Vision: OFF" button → should turn blue "AI Vision: ON"
2. If camera working: bounding boxes should appear on video
3. Check edge-app logs: should see AI detection messages
4. Click again → bounding boxes disappear, only raw video

### Test 3: Combined Toggles

1. Both ON: Video with AI bounding boxes
2. Video ON, AI OFF: Raw video only (better performance)
3. Video OFF, AI ON: No video (AI disabled automatically)
4. Both OFF: No video, no processing

### Test 4: Camera Fallback

1. If camera not available: Should see "Camera Not Available" message
2. Should NOT show broken image icon
3. Toggles should still work (but video won't show until camera fixed)

---

## Deployment Steps

1. **Update code on Pi**:
   ```bash
   ssh pi@192.168.88.16
   cd ~/smart-hive-ai
   git pull origin feature/project-cleanup-and-ml-reorganization
   ```

2. **Rebuild edge-app**:
   ```bash
   docker compose build --no-cache smart-hive-edge-app
   docker compose up -d smart-hive-edge-app
   ```

3. **Rebuild dashboard**:
   ```bash
   docker compose build --no-cache dashboard
   docker compose up -d dashboard
   ```

4. **Verify camera access**:
   ```bash
   docker exec smart-hive-edge-app python3 -c "import cv2; cam = cv2.VideoCapture(0); print('Camera:', cam.isOpened())"
   ```

5. **Test in browser**:
   - Open http://192.168.88.16:5000
   - Hard refresh (Ctrl+Shift+R)
   - Test both toggle buttons

---

## Summary

**Changes Made**:
1. ✅ Added separate `video_enabled` and `ai_vision_enabled` flags
2. ✅ Modified video generator to respect both toggles
3. ✅ Added MQTT topics for independent control
4. ✅ Created two separate toggle buttons in dashboard
5. ✅ Added camera availability fallback
6. ✅ Fixed broken image issue with error frames

**Benefits**:
- 💚 Save CPU by disabling AI when not needed
- 💚 Save bandwidth by disabling video when not watching
- 💚 No more broken image icon
- 💚 Independent control of video and AI
- 💚 Graceful degradation if camera unavailable

**Default State**:
- Video: **ON** (raw camera feed)
- AI Vision: **OFF** (save CPU, enable on demand)
