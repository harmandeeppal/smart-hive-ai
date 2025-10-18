# Deploy Dashboard UI Updates to Raspberry Pi

## Issue
The audio visualization enhancements (waveform, sound level bars, 2-column layout) were committed to Git but are NOT yet deployed to the Raspberry Pi. The Pi is still running the old dashboard code.

## What Was Changed (Commits 143b064 and 3918d96)

### Modified Files:
1. **dashboard/templates/index.html** - Added canvas and level bars
2. **dashboard/static/styles.css** - Dark theme styling  
3. **dashboard/static/app.js** - Waveform animation logic

### Expected Visual Changes:
- ✅ Audio card 2 columns wide (matches video card)
- ✅ Dark visualizer box with canvas (#1a1a2e background)
- ✅ Animated green waveform (#00ff88 color)
- ✅ 10 vertical sound level bars
- ✅ Live dB value updates
- ✅ 3-column classification results grid
- ✅ Gradient recording button (red gradient)

---

## Deployment Steps (Run on Raspberry Pi)

### Step 1: SSH to Raspberry Pi
```bash
ssh pi@192.168.88.16
```

### Step 2: Navigate to Project Directory
```bash
cd ~/smart-hive-ai
```

### Step 3: Pull Latest Changes
```bash
git fetch origin
git pull origin feature/project-cleanup-and-ml-reorganization
```

**Expected Output:**
```
remote: Counting objects: 12, done.
remote: Compressing objects: 100% (8/8), done.
remote: Total 12 (delta 6), reused 9 (delta 3)
Unpacking objects: 100% (12/12), done.
From https://github.com/harmandeeppal/smart-hive-ai
   3918d96..XXXXXXX  feature/project-cleanup-and-ml-reorganization -> origin/feature/project-cleanup-and-ml-reorganization
Updating 3918d96..XXXXXXX
Fast-forward
 dashboard/templates/index.html | 55 ++++++++++++-
 dashboard/static/styles.css    | 105 ++++++++++++++++++++-
 dashboard/static/app.js        | 167 ++++++++++++++++++++++++++++++++-
 3 files changed, 381 insertions(+), 19 deletions(-)
```

### Step 4: Verify Files Updated
```bash
# Check last modified time
ls -lh dashboard/templates/index.html
ls -lh dashboard/static/styles.css
ls -lh dashboard/static/app.js

# Quick verification - should see "audio-waveform" canvas
grep -n "audio-waveform" dashboard/templates/index.html
```

**Expected:**
```
Line numbers showing canvas element with id="audio-waveform"
```

### Step 5: Rebuild Dashboard Container
```bash
# Stop dashboard
docker compose stop dashboard

# Rebuild with latest code (no cache to ensure fresh build)
docker compose build --no-cache dashboard

# Start dashboard
docker compose up -d dashboard
```

**Expected Output:**
```
[+] Building 45.2s (12/12) FINISHED
[+] Running 1/1
 ✔ Container smart-hive-dashboard  Started
```

### Step 6: Verify Container Running
```bash
docker ps --filter "name=dashboard"
```

**Expected:**
```
CONTAINER ID   IMAGE                         STATUS         PORTS
xxxxxxxxxxxx   smart-hive-dashboard:latest   Up 10 seconds  0.0.0.0:5000->5000/tcp
```

### Step 7: Check Dashboard Logs
```bash
docker logs smart-hive-dashboard --tail 20
```

**Expected:**
```
INFO:werkzeug:WARNING: This is a development server.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.88.16:5000
```

---

## Verification on Windows Browser

### Step 1: Open Dashboard
```
http://192.168.88.16:5000
```

### Step 2: Hard Refresh (IMPORTANT!)
```
Press: Ctrl + Shift + R
(This clears cached CSS/JavaScript)
```

### Step 3: Visual Checklist

**Audio ML Card Should Now Show:**

1. **Card Width**
   - [ ] Audio card is same width as video card (2 columns)
   - [ ] Card has minimum 400px height

2. **Visualizer Container**
   - [ ] Dark background box (#1a1a2e color)
   - [ ] Rounded corners (8px border-radius)
   - [ ] Padding around content

3. **Canvas Waveform**
   - [ ] Canvas element visible (600x120px)
   - [ ] Dark background (#0f0f1e)
   - [ ] Green waveform line animating smoothly (#00ff88)
   - [ ] Grid lines visible in background
   - [ ] Waveform updates when sound_db changes

4. **Sound Level Bars**
   - [ ] 10 vertical bars below waveform
   - [ ] Bars arranged horizontally
   - [ ] Gradient colors (green → yellow → red from bottom to top)
   - [ ] Bars light up when sound detected
   - [ ] Height increases with sound level

5. **dB Display**
   - [ ] "-- dB" shown initially
   - [ ] Updates to live value (e.g., "42.5 dB") when telemetry arrives
   - [ ] Positioned next to level bars

6. **Classification Results**
   - [ ] 3-column grid layout
   - [ ] "Classification:", "Confidence:", "Status:" labels
   - [ ] Values show: Waiting... initially
   - [ ] Green color for "Queen Present"
   - [ ] Red color for "Queen Absent"

7. **Recording Button**
   - [ ] Red gradient background (from #dc3545 to #c82333)
   - [ ] Box shadow visible (red glow)
   - [ ] Text: "🎤 Record 1 Minute & Analyze"
   - [ ] Progress bar appears when recording

---

## Troubleshooting

### Issue: Still Seeing Old UI After git pull

**Cause:** Files not pulled correctly

**Solution:**
```bash
# Force reset to remote state
git fetch origin
git reset --hard origin/feature/project-cleanup-and-ml-reorganization

# Verify commit hash matches
git log -1 --oneline
# Should show: 3918d96 docs: Add audio visualization enhancement guide
```

### Issue: Container Built But Changes Not Visible

**Cause:** Docker using cached layers

**Solution:**
```bash
# Remove container and image
docker compose down dashboard
docker rmi smart-hive-dashboard:latest

# Rebuild from scratch
docker compose build --no-cache dashboard
docker compose up -d dashboard
```

### Issue: Browser Still Shows Old UI

**Cause:** Browser cache not cleared

**Solution:**
```
1. Press Ctrl + Shift + R (hard refresh)
2. If still old, press F12 → Network tab → Disable cache checkbox
3. Refresh again
4. If still old, clear all browser cache for this site
```

### Issue: Canvas Shows But No Animation

**Cause:** JavaScript error preventing animation

**Solution:**
```
1. Press F12 to open browser console
2. Check Console tab for errors
3. Look for errors related to "audio-waveform" or "animateWaveform"
4. Share error message for debugging
```

### Issue: Waveform Not Updating with Sound

**Cause:** Telemetry not publishing sound_db field

**Solution:**
```bash
# Check if sound_db in telemetry
docker exec mosquitto mosquitto_sub -t 'hive/telemetry' -C 1

# Should see:
{
  "temperature": 24.5,
  "humidity": 55.0,
  "sound_db": 42.3,  ← This field must be present
  ...
}

# If missing, check edge-app logs
docker logs smart-hive-edge-app --tail 20
```

---

## Expected Timeline

| Step | Duration | Description |
|------|----------|-------------|
| git pull | 10 seconds | Download latest code |
| docker build | 2-3 minutes | Rebuild dashboard image |
| docker up | 10 seconds | Start container |
| Browser refresh | 5 seconds | Clear cache and reload |
| **Total** | **~3-4 minutes** | Full deployment |

---

## File Size Verification

After git pull, file sizes should be:

```bash
# Check file sizes match
wc -l dashboard/templates/index.html  # Should be ~200 lines
wc -l dashboard/static/styles.css     # Should be ~300 lines  
wc -l dashboard/static/app.js         # Should be ~500 lines

# Check for specific additions
grep -c "audio-waveform" dashboard/templates/index.html  # Should be 1+
grep -c "animateWaveform" dashboard/static/app.js        # Should be 1+
grep -c "level-bar" dashboard/static/styles.css          # Should be 5+
```

---

## Quick Deployment Script

Create this script on Pi for easy deployment:

```bash
# Create script: ~/deploy-dashboard.sh
cat > ~/deploy-dashboard.sh << 'EOF'
#!/bin/bash
echo "🔄 Deploying dashboard updates..."

cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization

echo "🛑 Stopping dashboard..."
docker compose stop dashboard

echo "🔨 Rebuilding dashboard..."
docker compose build --no-cache dashboard

echo "🚀 Starting dashboard..."
docker compose up -d dashboard

echo "✅ Dashboard deployed!"
echo "🌐 Open: http://192.168.88.16:5000"
echo "🔄 Remember to hard refresh (Ctrl+Shift+R) in browser!"

docker logs smart-hive-dashboard --tail 10
EOF

chmod +x ~/deploy-dashboard.sh
```

**Usage:**
```bash
~/deploy-dashboard.sh
```

---

## Success Criteria

✅ **Deployment successful when:**

1. `git pull` shows files updated
2. `docker compose build` completes without errors
3. `docker ps` shows dashboard container running
4. Browser shows 2-column audio card
5. Canvas displays animated green waveform
6. 10 level bars visible and responsive
7. dB value updates from telemetry
8. Recording button has red gradient

---

## Summary

**Problem:** Dashboard changes committed to Git but not deployed to Raspberry Pi.

**Solution:** SSH to Pi → git pull → rebuild dashboard container → hard refresh browser.

**Key Commands:**
```bash
# On Raspberry Pi
cd ~/smart-hive-ai
git pull origin feature/project-cleanup-and-ml-reorganization
docker compose build --no-cache dashboard
docker compose up -d dashboard

# On Windows Browser
# Open: http://192.168.88.16:5000
# Press: Ctrl + Shift + R
```

**Estimated Time:** 3-4 minutes total.
