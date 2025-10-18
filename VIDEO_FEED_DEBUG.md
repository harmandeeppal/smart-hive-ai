# Video Feed Diagnostic & Fix Guide

## 🔍 Problem Identified

Your dashboard shows a **black rectangle with dead icon** instead of the live video feed.

### Possible Causes:
1. **Video stream not generating frames** (camera issue)
2. **MJPEG stream format incorrect** (boundary/headers)
3. **Browser compatibility** (some browsers don't support MJPEG in `<img>` tags)
4. **Flask streaming response buffering** issue

---

## 🧪 Diagnostic Steps

### Step 1: Check if camera is capturing frames

```bash
# On Pi, check edge-app logs for camera frames
ssh pi@192.168.88.16
docker logs smart-hive-edge 2>&1 | grep -E "Camera|Frame" | tail -20
```

**Expected output:**
```
Camera successfully captured test frame: (480, 640, 3)
📹 Camera frame publisher started
```

### Step 2: Test video feed from terminal

```bash
# Test if video feed is actually streaming data
python3 test_video_feed.py
```

Or manually:
```bash
ssh pi@192.168.88.16
# Download diagnostic script
cd ~/smart-hive-ai
python3 test_video_feed.py
```

### Step 3: Check browser console (F12)

1. Open dashboard: http://192.168.88.16:5000
2. Press **F12** to open Developer Tools
3. Go to **Console** tab
4. Look for errors related to `/video_feed`
5. Go to **Network** tab
6. Filter by "video_feed"
7. Check:
   - Status code (should be 200)
   - Response headers (should have `Content-Type: multipart/x-mixed-replace`)
   - Response body (should show streaming data, not empty)

**Common errors**:
- `ERR_CONNECTION_REFUSED` → edge-app not running
- `ERR_EMPTY_RESPONSE` → stream not generating frames
- `Failed to load resource` → browser can't render MJPEG

---

## 🔧 Fix Options

### Fix 1: Add error handling to video image (Quick Fix)

**Problem**: `<img>` tag shows broken icon if stream fails  
**Solution**: Add JavaScript error handler to show fallback message

**File**: `dashboard/templates/index.html`

```html
<!-- BEFORE -->
<img src="{{ url_for('video_feed') }}" width="100%" alt="Live video feed from the hive.">

<!-- AFTER -->
<img id="video-stream" 
     src="{{ url_for('video_feed') }}" 
     width="100%" 
     alt="Live video feed from the hive."
     onerror="this.onerror=null; this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22640%22 height=%22480%22><text x=%2250%%22 y=%2250%%22 text-anchor=%22middle%22 fill=%22white%22>Camera Offline</text></svg>'; this.style.backgroundColor='#333';">
```

### Fix 2: Verify video stream is generating frames

**Check edge-app generate_video_frames() is running**:

```bash
docker exec smart-hive-edge ps aux | grep python
docker logs smart-hive-edge 2>&1 | grep "video streaming server"
```

**Expected**:
```
Starting video streaming server on port 5001...
```

### Fix 3: Add explicit Content-Type in dashboard proxy

**Problem**: Dashboard proxy might not be forwarding correct headers  
**Solution**: Force correct Content-Type

**File**: `dashboard/dashboard_app.py`

```python
# CURRENT (line 159-162):
return Response(resp.iter_content(chunk_size=1024), 
                content_type=resp.headers['Content-Type'],
                status=resp.status_code)

# IMPROVED (explicit Content-Type):
return Response(resp.iter_content(chunk_size=1024), 
                content_type='multipart/x-mixed-replace; boundary=frame',
                status=resp.status_code)
```

### Fix 4: Use JavaScript to handle video stream (Most Robust)

**Problem**: Direct `<img>` src might not work in all browsers  
**Solution**: Use JavaScript to refresh/reload stream periodically

Add to `dashboard/static/app.js`:

```javascript
// Reload video stream every 30 seconds (prevents stream hang)
setInterval(function() {
    const videoImg = document.getElementById('video-stream');
    if (videoImg) {
        const src = videoImg.src;
        videoImg.src = '';
        setTimeout(() => { videoImg.src = src; }, 100);
    }
}, 30000);
```

---

## 🚀 Recommended Solution

### Quick Test First:

```bash
# On your Windows machine:
cd C:\Users\harma\OneDrive - AUT University\IDE_Workspace\aut_projects\smart-hive-ai

# Run diagnostic
python test_video_feed.py
```

This will tell us if the stream is **actually generating data** or if it's **empty/broken**.

### Then Apply Fix:

**If diagnostic shows frames ARE being sent** → Browser rendering issue  
✅ **Apply Fix 1** (add error handling) + **Fix 4** (JavaScript reload)

**If diagnostic shows NO frames** → Camera/streaming issue  
✅ Check camera initialization in edge-app logs  
✅ Verify `generate_video_frames()` is running  
✅ Check if camera device `/dev/video0` is accessible

---

## 📊 Expected Behavior After Fix

**Working Video Feed**:
1. Camera captures frames at 20 FPS (config.VIDEO_STREAM_FPS)
2. `generate_video_frames()` yields MJPEG frames
3. Flask serves on http://edge-app:5001/video_feed
4. Dashboard proxies to http://192.168.88.16:5000/video_feed
5. Browser displays live video stream

**If Camera Fails**:
- Shows "Camera Offline" message instead of broken icon
- Dashboard remains functional (doesn't break entire UI)

---

## 🔍 Next Steps

1. **Run diagnostic test** (`python test_video_feed.py`)
2. **Check browser console** (F12 → Console tab)
3. **Report results** so I can provide the exact fix

Let me know what the test shows!
