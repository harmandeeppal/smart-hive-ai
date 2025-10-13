# 🚀 Complete Raspberry Pi Deployment Guide

## ✅ Quick Start

**Your DynamoDB implementation works identically on Raspberry Pi with ZERO code changes.**

**Total Time:** 30-45 minutes (first time)  
**Code Changes Required:** ONE line (`IS_MOCK_ENVIRONMENT = False`)

---

## 📋 Prerequisites

### Hardware Required:
- ✅ Raspberry Pi 4 (2GB+ RAM recommended)
- ✅ MicroSD card (32GB+, Class 10)
- ✅ Power supply (official recommended)
- ✅ Network connection (Ethernet or WiFi)
- ✅ BME280 sensor (temperature/humidity)
- ✅ LIS3DH sensor (vibration)
- ✅ USB camera
- ✅ USB microphone

### Software Prerequisites:
- ✅ Raspberry Pi OS (64-bit recommended)
- ✅ Docker Engine & Docker Compose
- ✅ AWS credentials configured
- ✅ Project files

---

## 🎯 PART 1: Raspberry Pi Initial Setup (15 min)

### Step 1.1: Flash Raspberry Pi OS

**Using Raspberry Pi Imager (Recommended):**

1. Download from: https://www.raspberrypi.com/software/
2. Insert SD card and open Imager
3. Select "Raspberry Pi OS (64-bit)"
4. Click ⚙️ settings and configure:
   - ✅ Enable SSH
   - ✅ Set username: `pi`
   - ✅ Set password
   - ✅ Configure WiFi
   - ✅ Set hostname: `raspberrypi.local`
5. Write to SD card (~10 minutes)
6. Insert SD card into Pi and power on

### Step 1.2: Connect to Pi

```bash
# Wait 2-3 minutes for boot
ssh pi@raspberrypi.local
# Enter your password
```

### Step 1.3: Update System

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo reboot
```

---

## 🐳 PART 2: Install Docker (10 min)

### Step 2.1: Install Docker Engine

```bash
# Download installation script
curl -fsSL https://get.docker.com -o get-docker.sh

# Run installation (~3-5 minutes)
sudo sh get-docker.sh

# Add pi user to docker group
sudo usermod -aG docker pi
newgrp docker

# Verify
docker --version
```

### Step 2.2: Install Docker Compose

```bash
sudo apt-get install docker-compose-plugin -y

# Verify
docker compose version
```

### Step 2.3: Test Installation

```bash
docker run hello-world
# Should see: "Hello from Docker!"
```

---

## 📦 PART 3: Transfer Project Files (5 min)

### Option A: Using SCP (Windows PowerShell)

```powershell
# On your laptop
cd "C:\Users\harma\OneDrive - AUT University\IDE_Workspace\aut_projects\smart-hive-ai"
scp -r . pi@raspberrypi.local:/home/pi/smart-hive-ai
```

### Option B: Using Git

```bash
# On Raspberry Pi
cd /home/pi
git clone https://github.com/YOUR_USERNAME/smart-hive-ai.git
cd smart-hive-ai
```

### Verify Files

```bash
cd /home/pi/smart-hive-ai
ls -la
# Should see: app.py, config.py, docker-compose.yml, etc.
```

---

## 🔑 PART 4: Configure AWS (5 min)

### Step 4.1: Copy AWS Credentials

```bash
# Create directory
mkdir -p ~/.aws

# Create credentials file
nano ~/.aws/credentials
```

**Paste:**
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
```

Save: `CTRL+X`, `Y`, `ENTER`

### Step 4.2: Create Config File

```bash
nano ~/.aws/config
```

**Paste:**
```ini
[default]
region = ap-southeast-2
output = json
```

### Step 4.3: Verify Credentials

```bash
# Install AWS CLI
sudo apt-get install awscli -y

# Test
aws sts get-caller-identity
# Should show your AWS account details
```

---

## ⚙️ PART 5: Setup Hardware (5 min)

### Step 5.1: Enable I2C

```bash
sudo raspi-config
# Navigate: 3 Interface Options → I5 I2C → Yes
# Reboot when prompted
```

### Step 5.2: Connect Sensors

**I2C Sensors (BME280 & LIS3DH):**
```
Sensor Pin → Raspberry Pi Pin
────────────────────────────
VCC  → Pin 1  (3.3V)
GND  → Pin 6  (Ground)
SCL  → Pin 5  (GPIO3 / SCL)
SDA  → Pin 3  (GPIO2 / SDA)
```

**USB Devices:**
- USB Camera → Any USB port
- USB Microphone → Any USB port

### Step 5.3: Verify Hardware

```bash
# Check I2C devices
sudo i2cdetect -y 1
# Should see: 18 (LIS3DH) and 77 (BME280)

# Check USB devices
lsusb
# Should see camera and microphone
```

---

## 🔧 PART 6: Configure Application (2 min)

### Update config.py

```bash
cd /home/pi/smart-hive-ai
nano config.py
```

**Change line 74:**
```python
# Before:
IS_MOCK_ENVIRONMENT = True

# After:
IS_MOCK_ENVIRONMENT = False
```

Save and verify:
```bash
grep "IS_MOCK_ENVIRONMENT" config.py
```

---

## 🚀 PART 7: Deploy (5 min)

### Start Containers

```bash
cd /home/pi/smart-hive-ai
docker compose up --build
```

**Watch for success messages:**
```
✅ DynamoDB table 'SmartHiveTelemetry' initialized successfully.
✅ Successfully connected to AWS IoT Core.
✅ Initialized Real BME280 Sensor.
✅ Initialized Real LIS3DH Sensor.
✅ Starting video streaming server on port 5001...
```

### Run in Background (Optional)

```bash
# Press CTRL+C to stop foreground mode
docker compose up --build -d

# Check logs anytime:
docker logs -f smart-hive-edge

# Stop when needed:
docker compose down
```

---

## ✅ PART 8: Verification (5 min)

### Step 8.1: Check Dashboard

**Open browser on your laptop:**
```
http://raspberrypi.local:5000
```

**Should see:**
- ✅ Live temperature/humidity
- ✅ Live video feed
- ✅ All sensors updating
- ✅ Toggle controls working

### Step 8.2: Verify DynamoDB

**AWS Console:**
1. Go to DynamoDB → SmartHiveTelemetry
2. Explore table items
3. Check for new records with `device_id = SmartHive_Pi`

### Step 8.3: Check Logs

```bash
docker logs smart-hive-edge | grep DynamoDB
# Should show: ✅ DynamoDB: Wrote record at...
```

### Step 8.4: Verify S3 Uploads

**AWS Console:**
1. Go to S3 → `smart-hive-snapshots-hst-10102025`
2. Check for snapshot images

---

## 🔧 Configuration Changes

### Change Telemetry Interval

```bash
ssh pi@raspberrypi.local
cd /home/pi/smart-hive-ai
nano config.py

# Change:
TELEMETRY_INTERVAL_SECONDS = 60  # Was: 5

# Restart:
docker compose restart
```

**Common changes:**
- `TELEMETRY_INTERVAL_SECONDS = 60` (reduce DB writes)
- `S3_SNAPSHOT_INTERVAL_SECONDS = 600` (reduce S3 costs)
- `VISION_LOOP_INTERVAL_SECONDS = 5` (reduce CPU load)

---

## 📋 Deployment Checklist

### Pre-Deployment:
- [ ] Pi OS flashed and SSH enabled
- [ ] Can connect: `ssh pi@raspberrypi.local`
- [ ] System updated

### Docker:
- [ ] `docker --version` works
- [ ] `docker compose version` works
- [ ] `docker run hello-world` succeeds

### Project:
- [ ] Files at `/home/pi/smart-hive-ai`
- [ ] Can see `app.py`

### AWS:
- [ ] `~/.aws/credentials` exists
- [ ] `~/.aws/config` exists
- [ ] `aws sts get-caller-identity` works

### Hardware:
- [ ] I2C enabled
- [ ] BME280 detected (address 77)
- [ ] LIS3DH detected (address 18)
- [ ] Camera/mic detected with `lsusb`

### Application:
- [ ] `IS_MOCK_ENVIRONMENT = False`
- [ ] Containers running
- [ ] No errors in logs

### Verification:
- [ ] Dashboard accessible
- [ ] Real sensor data (not mock)
- [ ] DynamoDB receiving data
- [ ] S3 receiving images

---

## 🎯 Quick Commands Reference

| Task | Command |
|------|---------|
| SSH to Pi | `ssh pi@raspberrypi.local` |
| Start system | `docker compose up -d` |
| Stop system | `docker compose down` |
| View logs | `docker logs -f smart-hive-edge` |
| Restart | `docker compose restart` |
| Check sensors | `sudo i2cdetect -y 1` |
| Check USB | `lsusb` |
| Edit config | `nano /home/pi/smart-hive-ai/config.py` |

---

## 🎉 Success Criteria

Your deployment is successful when:

1. ✅ Dashboard loads at `http://raspberrypi.local:5000`
2. ✅ Real sensor readings (variable, not fixed)
3. ✅ DynamoDB shows new records every 5 seconds
4. ✅ S3 shows snapshot images
5. ✅ Video feed working
6. ✅ Toggle controls functional
7. ✅ No errors in logs
8. ✅ System stable for 24+ hours

---

## 💡 Pro Tips

### Auto-Start on Boot

```bash
sudo nano /etc/systemd/system/smart-hive.service
```

```ini
[Unit]
Description=Smart Hive AI
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/pi/smart-hive-ai
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable smart-hive.service
sudo systemctl start smart-hive.service
```

---

## 📊 Understanding Timestamps

DynamoDB uses Unix timestamps (seconds since Jan 1, 1970 UTC).

**Convert to readable format:**
```bash
python3 -c "from datetime import datetime; print(datetime.fromtimestamp(1760358523))"
```

**Query last 24 hours:**
```python
from datetime import datetime, timedelta
import boto3

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
table = dynamodb.Table('SmartHiveTelemetry')

start_time = int((datetime.now() - timedelta(days=1)).timestamp())

response = table.query(
    KeyConditionExpression='device_id = :device AND #ts > :start',
    ExpressionAttributeNames={'#ts': 'timestamp'},
    ExpressionAttributeValues={
        ':device': 'SmartHive_Pi',
        ':start': start_time
    }
)
```

---

## ✅ Deployment Complete!

**Total time:** 30-45 minutes  
**Code changes:** ONE line  
**Result:** Production-ready system collecting real data

See `TROUBLESHOOTING.md` for common issues and fixes.
