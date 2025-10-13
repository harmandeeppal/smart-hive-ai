# Toggle Button Issue - Temperature & Humidity

## 🐛 Question 3: Toggle Off Disables Both Temperature AND Humidity

### Root Cause Analysis ✅

**Yes, this is correct behavior, but it's by design (not a bug).**

Here's why turning off temperature also turns off humidity:

---

## 🔍 The Issue

### Backend Code (`app.py` line 203-207)

```python
if self.sensor_events["temperature"].is_set():
    temp, humidity = self.temp_humidity_sensor.get_temp_humidity()
    payload["temperature"] = temp
    payload["humidity"] = humidity
```

**Problem:** The BME280 sensor returns BOTH temperature AND humidity in one function call: `get_temp_humidity()`.

When you toggle temperature OFF:
1. ❌ `self.sensor_events["temperature"].is_set()` becomes `False`
2. ❌ Entire `if` block is skipped
3. ❌ BOTH temperature AND humidity stop publishing

---

## 🏥 The Fix

You need to **separate the toggle controls** so each can be controlled independently.

### Option 1: Check Both Temperature AND Humidity Toggles (Recommended)

Update `app.py` telemetry loop:

```python
def telemetry_loop(self):
    """--- ENHANCEMENT: Unified loop for all telemetry sensors ---"""
    while self.is_running:
        # Wait until at least one sensor is enabled before continuing
        while self.is_running and not any([
            self.sensor_events["temperature"].is_set(),
            self.sensor_events["humidity"].is_set(),  # ✨ ADD THIS LINE
            self.sensor_events["vibration"].is_set(),
            self.sensor_events["sound"].is_set()
        ]):
            time.sleep(1)  # Sleep while all sensors are toggled off
        
        if not self.is_running:
            break
            
        try:
            payload = {"timestamp": int(time.time())}
            
            # ✨ NEW: Read sensor if EITHER toggle is ON
            if self.sensor_events["temperature"].is_set() or self.sensor_events["humidity"].is_set():
                temp, humidity = self.temp_humidity_sensor.get_temp_humidity()
                
                # Only add to payload if specific sensor is enabled
                if self.sensor_events["temperature"].is_set():
                    payload["temperature"] = temp
                
                if self.sensor_events["humidity"].is_set():
                    payload["humidity"] = humidity
            
            if self.sensor_events["vibration"].is_set():
                payload["vibration_rms"] = self.vibration_sensor.get_rms_acceleration()

            if self.sensor_events["sound"].is_set():
                payload["sound_db"] = self.sound_sensor.get_db_level()
                payload["sound_freq"] = self.sound_sensor.get_dominant_frequency()
            
            if len(payload) > 1: # Only publish if there's data
                self.mqtt_client.publish(config.TOPIC_TELEMETRY, json.dumps(payload), qos=1)
                print(f"Published Telemetry: {payload}")
                
        except Exception as e:
            print(f"Error in telemetry loop: {e}")
        
        time.sleep(config.TELEMETRY_INTERVAL_SECONDS)
```

### Option 2: Always Read BME280, Conditionally Publish (Alternative)

```python
def telemetry_loop(self):
    while self.is_running:
        # ... wait logic ...
        
        try:
            payload = {"timestamp": int(time.time())}
            
            # Always read the sensor (minimal overhead)
            temp, humidity = self.temp_humidity_sensor.get_temp_humidity()
            
            # But only publish if toggle is ON
            if self.sensor_events["temperature"].is_set():
                payload["temperature"] = temp
            
            if self.sensor_events["humidity"].is_set():
                payload["humidity"] = humidity
            
            # ... rest of code ...
```

---

## 🎯 Complete Implementation

Here's the full corrected code:

```python
def telemetry_loop(self):
    """Main loop for reading sensor data and publishing to MQTT."""
    while self.is_running:
        # Wait until at least one sensor is enabled before continuing
        while self.is_running and not any([
            self.sensor_events["temperature"].is_set(),
            self.sensor_events["humidity"].is_set(),     # ← ADDED
            self.sensor_events["vibration"].is_set(),
            self.sensor_events["sound"].is_set()
        ]):
            time.sleep(1)  # Sleep while all sensors are toggled off
        
        if not self.is_running:
            break
            
        try:
            payload = {"timestamp": int(time.time())}
            
            # Read BME280 if either temperature OR humidity is enabled
            if self.sensor_events["temperature"].is_set() or self.sensor_events["humidity"].is_set():
                temp, humidity = self.temp_humidity_sensor.get_temp_humidity()
                
                # Add to payload only if that specific sensor is ON
                if self.sensor_events["temperature"].is_set():
                    payload["temperature"] = temp
                
                if self.sensor_events["humidity"].is_set():
                    payload["humidity"] = humidity
            
            # Vibration sensor (independent)
            if self.sensor_events["vibration"].is_set():
                payload["vibration_rms"] = self.vibration_sensor.get_rms_acceleration()

            # Sound sensor (independent)
            if self.sensor_events["sound"].is_set():
                payload["sound_db"] = self.sound_sensor.get_db_level()
                payload["sound_freq"] = self.sound_sensor.get_dominant_frequency()
            
            # Publish if there's any data
            if len(payload) > 1:
                self.mqtt_client.publish(config.TOPIC_TELEMETRY, json.dumps(payload), qos=1)
                print(f"Published Telemetry: {payload}")
                
        except Exception as e:
            print(f"Error in telemetry loop: {e}")
        
        time.sleep(config.TELEMETRY_INTERVAL_SECONDS)
```

---

## 🧪 Testing the Fix

### Test Scenario 1: Toggle Temperature OFF, Humidity ON

**Expected Behavior:**
```
Dashboard:
  Temperature: -- °C (frozen, not updating)
  Humidity: 58.2% (continues updating)

Terminal Output:
  Published Telemetry: {'timestamp': 1697123456, 'humidity': 58.2}
```

### Test Scenario 2: Toggle Humidity OFF, Temperature ON

**Expected Behavior:**
```
Dashboard:
  Temperature: 34.5°C (continues updating)
  Humidity: -- % (frozen, not updating)

Terminal Output:
  Published Telemetry: {'timestamp': 1697123461, 'temperature': 34.5}
```

### Test Scenario 3: Toggle BOTH OFF

**Expected Behavior:**
```
Dashboard:
  Temperature: -- °C (frozen)
  Humidity: -- % (frozen)

Terminal Output:
  Paused sensor: temperature
  Paused sensor: humidity
  (no telemetry messages)
```

### Test Scenario 4: Toggle BOTH ON

**Expected Behavior:**
```
Dashboard:
  Temperature: 34.5°C (updating every 5 seconds)
  Humidity: 58.2% (updating every 5 seconds)

Terminal Output:
  Resumed sensor: temperature
  Resumed sensor: humidity
  Published Telemetry: {'timestamp': 1697123466, 'temperature': 34.5, 'humidity': 58.2}
```

---

## 📊 Before vs After

### Before (Current Buggy Behavior)

| Action | Temperature Display | Humidity Display | Issue |
|--------|-------------------|-----------------|-------|
| Toggle Temp OFF | ❌ Stops | ❌ Also stops! | Bug |
| Toggle Hum OFF | ❌ Also stops! | ❌ Stops | Bug |

### After (Fixed Behavior)

| Action | Temperature Display | Humidity Display | Status |
|--------|-------------------|-----------------|--------|
| Toggle Temp OFF | ❌ Stops | ✅ Continues | ✅ Fixed |
| Toggle Hum OFF | ✅ Continues | ❌ Stops | ✅ Fixed |

---

## 🔧 Implementation Steps

1. **Open `app.py`**
2. **Find `telemetry_loop()` function** (around line 187)
3. **Replace the entire function** with the corrected code above
4. **Save file**
5. **Rebuild containers:**
   ```bash
   docker-compose down
   docker-compose up --build
   ```
6. **Test all 4 scenarios** from the testing section

---

## 💡 Why This Happens

### Single Sensor, Dual Readings

The **BME280 sensor** is ONE physical chip that measures:
- Temperature (from thermistor)
- Humidity (from capacitive sensor)
- Pressure (from piezoresistive sensor, not used in this project)

When you call `get_temp_humidity()`, the sensor returns all readings together.

**The fix separates the logic:**
- **Hardware level**: Read sensor once (efficient)
- **Software level**: Conditionally publish each reading based on toggle state

---

## 🎓 Design Consideration

### Should They Be Separate Toggles?

**Yes, because:**
1. **User Control**: Beekeeper may only care about temperature trends
2. **Bandwidth**: Reduce MQTT messages if only monitoring one parameter
3. **Dashboard Clarity**: Hide irrelevant data during experiments
4. **Testing**: Isolate one sensor during calibration

**From your thesis perspective:**
- Document this as a design choice
- Explain the hardware constraint (single sensor, dual readings)
- Show how software abstraction provides independent control

---

## ✅ Validation Checklist

After implementing the fix:

- [ ] Temperature toggle OFF: Temperature freezes, Humidity continues
- [ ] Humidity toggle OFF: Humidity freezes, Temperature continues
- [ ] Both toggles OFF: Neither updates
- [ ] Both toggles ON: Both update every 5 seconds
- [ ] Edge device logs show correct sensor pause/resume messages
- [ ] Dashboard JavaScript state tracking works correctly
- [ ] Button colors change correctly (blue = ON, gray = OFF)

---

## 🚀 Quick Fix Command

```bash
# 1. Copy the corrected telemetry_loop() function

# 2. Replace in app.py (lines 187-225)

# 3. Rebuild
docker-compose down
docker-compose up --build

# 4. Test
# - Toggle temperature OFF
# - Verify humidity still updates
# - Toggle humidity OFF
# - Verify temperature still updates
```

---

## 📝 For Your Thesis Documentation

### Problem Statement
"The BME280 sensor returns both temperature and humidity in a single reading. The initial implementation treated this as a single toggle event, causing interdependence between ostensibly separate controls."

### Solution
"Implemented conditional publishing logic that reads the sensor once but publishes each metric independently based on its toggle state. This provides user-level control while maintaining hardware efficiency."

### Impact
"Users can now monitor temperature trends without humidity data cluttering the dashboard, or vice versa. This is particularly useful during calibration or when investigating specific environmental parameters."

---

## 🎯 Summary

**Current Behavior:** ❌ Temperature toggle controls BOTH temp and humidity  
**Root Cause:** Single `if` statement for both metrics  
**Fix:** Check toggles separately, publish conditionally  
**Testing:** 4 scenarios to validate independence  
**Time to Fix:** ~5 minutes  

**This is a simple logic fix, not a hardware limitation!** 🐝
