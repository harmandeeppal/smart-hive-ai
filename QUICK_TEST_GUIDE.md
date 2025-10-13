# Quick Test Guide - Dashboard Fixes
## Test These 4 Fixes Now!

---

## ⚡ QUICK START

```powershell
# Stop current containers
docker-compose down

# Rebuild with fixes
docker-compose up --build

# Open dashboard
# http://localhost:5000
```

---

## ✅ TEST #1: Arrow Positioning (30 seconds)

**What to check:**
1. Look at Temperature card
2. Find the arrow marker (▼) below the colored bar
3. Watch it move as temperature changes

**Expected Result:**
- ▼ appears on the gradient bar
- Moves smoothly as values change
- Positioned correctly:
  - Far left = Too Cold (<32°C)
  - Middle = Optimal (33-36°C)
  - Far right = Too Hot (>37°C)

**Screenshot Comparison:**
- Before: No arrow visible OR arrow stuck
- After: Arrow visible and moving ✓

---

## ✅ TEST #2: Toggle Functionality (1 minute)

**Steps:**
1. Watch Temperature value updating (changes every 5 seconds)
2. Click "Toggle: OFF" button on Temperature card
3. Wait 10 seconds
4. Click "Toggle: ON" button

**Expected Result:**
- Button turns GRAY when OFF
- Temperature value STOPS changing
- Other sensors (humidity, vibration, sound) keep updating
- Button turns BLUE when ON
- Temperature resumes updating

**Check Docker Logs:**
```powershell
docker logs smart-hive-edge --tail 20
```
Should show:
```
Paused sensor: temperature
Resumed sensor: temperature
```

---

## ✅ TEST #3: Video Feed (10 seconds)

**What to check:**
1. Look at "AI Vision - Live Feed" card
2. Should see animated video
3. Should see "QUEEN DETECTED (XX%)" occasionally

**Expected Result:**
- ❌ Before: Broken image icon (🖼️❌)
- ✅ After: Live video with moving bee animations

**Mock Video Shows:**
- White background
- Blue circles (simulated bees)
- Occasional green rectangle (queen detection)
- Status changes between "Actively Scanning" and "QUEEN DETECTED"

---

## ✅ TEST #4: Enhanced Alerts (2 minutes)

### A. Check Current Alerts
Look at each card's Status and Action text:

**Temperature:** Should show emoji and detailed action
- Example: "✓ Optimal" + "None required."

**Humidity:** Should show emoji and detailed action
- Example: "✓ Optimal" + "None required."

**Sound Profile:** Should show emoji and detailed action
- Example: "👑 QUEEN STATUS ALERT" + "Abnormal sound detected. Check brood frames..."

### B. Force Abnormal Condition

**Option 1: Force Hot Temperature**
```powershell
# Stop containers
docker-compose down

# Edit mock_components.py (line ~17)
# Change: temp = 34.5 + random.uniform(-0.2, 0.2)
# To:     temp = 38.5

# Restart
docker-compose up --build
```

**Expected:**
- Temperature: 38.5°C
- Status: "☀️ Too Hot"
- Action: "Open entrance fully. Prop outer cover for ventilation. Provide shade cloth."
- Arrow positioned at far right (red zone)

**Option 2: Force High Vibration**
```python
# Edit mock_components.py (line ~31)
# Return: return 0.20  # Instead of ~0.05
```

**Expected:**
- Vibration: 0.2000 RMS
- Status: "🚨 Agitation Alert"
- Action: "Hive disturbed or under attack. Check visual feed for pests. Avoid opening hive for 2+ hours."

---

## 🎯 SUCCESS CRITERIA

All 4 tests pass if:

1. ✅ Arrows (▼) visible and moving on Temperature & Humidity
2. ✅ Toggle OFF stops that sensor's updates completely
3. ✅ Video feed displays (not broken icon)
4. ✅ Status messages include emojis (❄️, ☀️, 💦, 💧, 🚨, 🛑, 👑, 🏃, 💀, ✓)
5. ✅ Action text provides specific, detailed recommendations

---

## 🐛 TROUBLESHOOTING

### Arrow still not visible?
```powershell
# Clear browser cache
Ctrl + Shift + R (Windows)
Cmd + Shift + R (Mac)
```

### Toggle not working?
Check browser console (F12):
```javascript
// Should see:
Connected to dashboard server!
Received telemetry: {temperature: 34.5, humidity: 58.1, ...}
```

### Video feed still broken?
Check dashboard container logs:
```powershell
docker logs smart-hive-dashboard --tail 50
```
Should see:
```
Dashboard MQTT client connected successfully.
```

### Alerts not showing emojis?
Check if browser supports UTF-8. Try different browser (Chrome, Firefox, Edge).

---

## 📸 VISUAL CONFIRMATION

### Before Fixes:
```
Temperature: 34.5°C
[=============================] (no arrow)
Status: Optimal
Action: None required.
```

### After Fixes:
```
Temperature: 34.5°C
[=========▼===================]
Status: ✓ Optimal
Action: None required.
[Toggle: ON] (blue button)
```

---

## 🎓 WHAT CHANGED?

| Issue | Before | After |
|-------|--------|-------|
| Arrow | Not visible | ▼ Moving smoothly |
| Toggle | Visual only | Actually stops data |
| Video | 🖼️❌ Broken | 📹 Live stream |
| Alerts | Generic text | 👑 Emoji + Details |

---

## 🚀 READY FOR RASPBERRY PI?

Once all 4 tests pass on laptop:

1. Change `config.py`: `IS_MOCK_ENVIRONMENT = False`
2. Connect real sensors to Raspberry Pi
3. Deploy and test with actual hardware
4. Calibrate thresholds based on your hive's baseline

---

**Test now and let me know results!** 🐝
