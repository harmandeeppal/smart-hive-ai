# 🔧 BME280 Sensor Troubleshooting Guide

**Issue:** `Error initializing Real BME280: No I2C device at address: 0x76`

**Status:** System running but BME280 not detected

---

## 🎯 Quick Diagnosis

Run this on Raspberry Pi:

```bash
sudo i2cdetect -y 1
```

**Expected output with BME280:**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- 18 19 -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
70: -- -- -- -- -- -- 76 77                         
```

**Your current output (likely):**
```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:          -- -- -- -- -- -- -- -- -- -- -- -- -- 
10: -- -- -- -- -- -- -- -- 18 19 -- -- -- -- -- -- 
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
...
70: -- -- -- -- -- -- -- --   ← BME280 missing
```

---

## 🔍 Scenario Analysis

### **Scenario 1: BME280 Shows as 77 (Not 76)**

If you see `77` instead of `76`:

**Solution:** Update config.py

```bash
nano /home/pi/smart-hive-ai/config.py
```

Change line 51:
```python
# From:
BME280_ADDRESS = 0x76

# To:
BME280_ADDRESS = 0x77
```

Restart:
```bash
docker compose restart
docker logs -f smart-hive-edge
```

---

### **Scenario 2: BME280 Not Detected at All**

If neither `76` nor `77` appears:

#### **Step 1: Check Physical Connection**

```
BME280 Pin → Raspberry Pi Pin
──────────────────────────────
VCC  → Pin 1  (3.3V)  ✅
GND  → Pin 6  (Ground) ✅
SCL  → Pin 5  (GPIO3)  ✅
SDA  → Pin 3  (GPIO2)  ✅
```

**Verify:**
- Wires firmly connected
- No loose connections
- Correct pins (compare with LIS3DH which IS working at 0x19)

#### **Step 2: Check I2C is Enabled**

```bash
# Verify I2C enabled
ls /dev/i2c*
# Should show: /dev/i2c-1
```

If not:
```bash
sudo raspi-config
# 3 Interface Options → I5 I2C → Yes
# Reboot
```

#### **Step 3: Test BME280 Hardware**

**Option A: Test with another device**
- If you have another I2C device, swap connections
- Verify BME280 works on another Pi (if available)

**Option B: Check sensor with multimeter**
- Measure VCC (should be 3.3V)
- Measure continuity on SDA/SCL lines

#### **Step 4: Check for I2C Address Conflict**

BME280 shares I2C bus with LIS3DH. Ensure:
- Only ONE device at address 0x76/0x77
- LIS3DH is at 0x18 or 0x19 (confirmed working at 0x19 ✅)

---

### **Scenario 3: BME280 Intermittent Detection**

If BME280 appears sometimes:

**Possible causes:**
1. **Loose wiring** - Re-seat all connections
2. **Power issue** - BME280 + LIS3DH + USB devices drawing too much
3. **I2C speed** - Try lowering I2C clock speed

**Lower I2C speed:**
```bash
sudo nano /boot/config.txt
```

Add/modify:
```ini
dtparam=i2c_arm=on,i2c_arm_baudrate=10000
```

Reboot:
```bash
sudo reboot
```

---

## 🛠️ System Configuration Options

### **Option 1: Run Without BME280 (Temporary)**

If BME280 is not available, system can still run with other sensors.

**The application handles this gracefully:**
- ✅ System continues running
- ✅ Other sensors work normally
- ⚠️ Temperature/Humidity data not available

**To disable temperature/humidity in dashboard:**

In `config.py`:
```python
# Add this flag
BME280_PRESENT = False
```

Update code to check this flag before reading BME280.

---

### **Option 2: Use Mock BME280 (Testing)**

For testing without hardware:

```bash
nano /home/pi/smart-hive-ai/config.py
```

```python
IS_MOCK_ENVIRONMENT = True  # Temporarily switch to mock mode
```

Restart:
```bash
docker compose restart
```

**Result:**
- Mock BME280 provides fake data
- All other real sensors still work
- Dashboard shows data (but temp/humidity are simulated)

---

### **Option 3: Try BMP280 Instead**

If you have BMP280 (pressure sensor without humidity):

**Update config.py:**
```python
USE_BMP280_INSTEAD = True  # Add this flag
```

**Update real_components.py:**
```python
# Import BMP280 library instead
import adafruit_bmp280
```

---

## 📊 Current System Status

Based on your logs:

| Component | Status | Address/Port |
|-----------|--------|--------------|
| LIS3DH (Vibration) | ✅ Working | 0x19 |
| INMP441 (Microphone) | ✅ Working | USB Audio |
| Vision Processor | ✅ Working | USB Camera |
| AWS IoT Core | ✅ Connected | MQTT |
| DynamoDB | ✅ Working | Cloud |
| **BME280 (Temp/Humidity)** | ❌ **Not Detected** | **0x76 missing** |

**Impact:**
- 🟢 System is running
- 🟢 Most features work
- 🟡 Temperature/Humidity data unavailable
- 🟢 Vibration, sound, vision all working

---

## ✅ Recommended Next Steps

### **Priority 1: Verify Hardware**

```bash
# 1. Check I2C devices
sudo i2cdetect -y 1

# 2. Check physical connections
# Verify BME280 wired correctly

# 3. If BME280 at 0x77, update config
nano /home/pi/smart-hive-ai/config.py
# Change BME280_ADDRESS = 0x77

# 4. Restart
docker compose restart
```

---

### **Priority 2: System Already Functional**

**Good news:** Your system is mostly working! ✅

You can:
- ✅ View dashboard at `http://raspberrypi.local:5000`
- ✅ See vibration data
- ✅ See sound data
- ✅ See video feed with AI detection
- ⚠️ Temperature/Humidity will show errors

**Decision:**
- If BME280 is critical → Fix hardware
- If not urgent → Continue testing other features

---

### **Priority 3: Graceful Degradation (Optional)**

Make system handle missing BME280 better:

**Update `real_components.py`:**

```python
class RealBME280:
    def __init__(self, address=None):
        self.sensor = None
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            address = address or config.BME280_ADDRESS
            self.sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=address)
            print(f"✅ Successfully initialized Real BME280 Sensor at address 0x{address:02X}.")
        except Exception as e:
            print(f"⚠️  Warning: BME280 not available: {e}")
            print(f"⚠️  Temperature/Humidity data will not be available")
    
    def get_temp_humidity(self):
        if self.sensor:
            return (self.sensor.temperature, self.sensor.humidity)
        else:
            # Return None or default values when sensor not available
            return (None, None)
```

**Update `app.py` telemetry loop:**

```python
if self.sensor_events["temperature"].is_set() or self.sensor_events["humidity"].is_set():
    temp, humidity = self.temp_humidity_sensor.get_temp_humidity()
    
    # Only add if values are valid
    if self.sensor_events["temperature"].is_set() and temp is not None:
        payload["temperature"] = temp
    
    if self.sensor_events["humidity"].is_set() and humidity is not None:
        payload["humidity"] = humidity
```

---

## 🎉 Bottom Line

**Your deployment is 90% successful!** 🎉

✅ **Working:**
- AWS connectivity
- DynamoDB logging
- Vision AI
- Vibration sensor
- Sound sensor
- Video streaming
- Dashboard

⚠️ **Needs attention:**
- BME280 temperature/humidity sensor

**Recommendation:**
1. Check `sudo i2cdetect -y 1` output
2. Verify BME280 address (76 vs 77)
3. Check physical wiring
4. Continue using system with 4/5 sensors working

**The system is production-ready for vibration, sound, and vision monitoring!** 🚀

---

## 📞 Need Help?

Share the output of:
```bash
sudo i2cdetect -y 1
```

And I can provide specific guidance for your hardware configuration.
