# 🆘 Troubleshooting Guide

Complete solutions for common issues in Smart Hive AI deployment.

---

## 🔑 AWS Issues

### Issue 1: "Unable to locate credentials"

**Error:**
```
❌ Error initializing DynamoDB: Unable to locate credentials
```

**Cause:** AWS credentials not configured or Docker can't access them.

**Solution:**

```bash
# Check credentials exist
cat ~/.aws/credentials
# Should show [default] section with access keys

# If missing, create it:
mkdir -p ~/.aws
nano ~/.aws/credentials
```

**Paste:**
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

**For Docker containers:**

Check `docker-compose.yml` has:
```yaml
volumes:
  - ~/.aws:/root/.aws:ro
```

Then restart:
```bash
docker compose restart
```

---

### Issue 2: "User is not authorized to perform: dynamodb:PutItem"

**Error:**
```
❌ ClientError: User is not authorized to perform: dynamodb:PutItem on resource
```

**Cause:** IAM user lacks DynamoDB permissions.

**Solution:**

1. Go to AWS Console → IAM → Users → `harmandeeppal`
2. Click "Add permissions" → "Create inline policy"
3. Use JSON editor:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:PutItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:UpdateItem",
                "dynamodb:DeleteItem",
                "dynamodb:DescribeTable",
                "dynamodb:ListTables"
            ],
            "Resource": [
                "arn:aws:dynamodb:ap-southeast-2:651706753211:table/SmartHiveTelemetry",
                "arn:aws:dynamodb:ap-southeast-2:651706753211:table/SmartHiveTelemetry/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::smart-hive-snapshots-hst-10102025",
                "arn:aws:s3:::smart-hive-snapshots-hst-10102025/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "iot:Connect",
                "iot:Publish",
                "iot:Subscribe",
                "iot:Receive"
            ],
            "Resource": "*"
        }
    ]
}
```

4. Name it: `SmartHive_Full_Access`
5. Create and attach

**Verify:**
```bash
aws sts get-caller-identity
# Should show your IAM user
```

---

### Issue 3: "Float types are not supported"

**Error:**
```
❌ TypeError: Float types are not supported. Use Decimal types instead.
```

**Cause:** DynamoDB doesn't accept Python `float` type.

**Solution:**

This is already fixed in `app.py`. Verify lines 200-250:

```python
from decimal import Decimal

def write_to_dynamodb(self, telemetry_data):
    item = {
        'device_id': config.THING_NAME,
        'timestamp': int(time.time()),
        'temperature': Decimal(str(round(float(telemetry_data['temperature']), 2))),
        'humidity': Decimal(str(round(float(telemetry_data['humidity']), 2))),
        'vibration_rms': Decimal(str(round(float(telemetry_data['vibration_rms']), 4))),
        'sound_db': Decimal(str(round(float(telemetry_data['sound_db']), 2))),
        'sound_freq': Decimal(str(round(float(telemetry_data['sound_freq']), 2)))
    }
```

If you see errors, rebuild containers:
```bash
docker compose down
docker compose up --build
```

---

### Issue 4: AWS Region Mismatch

**Error:**
```
❌ Could not connect to the endpoint URL
```

**Cause:** Wrong AWS region in config.

**Solution:**

Check `config.py`:
```python
AWS_REGION = "ap-southeast-2"  # Should match your DynamoDB table region
```

Check `~/.aws/config`:
```ini
[default]
region = ap-southeast-2
```

Verify DynamoDB table region in AWS Console.

---

## 🔧 Hardware Issues

### Issue 5: "I2C device not found"

**Error:**
```
Error initializing BME280: No I2C device at address 0x77
```

**Cause:** I2C not enabled or sensor not connected.

**Solution:**

**1. Enable I2C:**
```bash
sudo raspi-config
# Interface Options → I2C → Enable
sudo reboot
```

**2. Check connections:**
```
BME280/LIS3DH → Raspberry Pi
────────────────────────────
VCC → Pin 1 (3.3V)
GND → Pin 6 (Ground)
SCL → Pin 5 (GPIO3/SCL)
SDA → Pin 3 (GPIO2/SDA)
```

**3. Verify detection:**
```bash
sudo i2cdetect -y 1
```

Should show:
- `18` = LIS3DH
- `77` = BME280

**4. Try alternate addresses:**

BME280 can be at `0x76` or `0x77`. Update `config.py` if needed:
```python
BME280_ADDRESS = 0x76  # Try this if 0x77 doesn't work
```

LIS3DH can be at `0x18` or `0x19`:
```python
LIS3DH_ADDRESS = 0x19  # Try this if 0x18 doesn't work
```

---

### Issue 6: "Camera not found"

**Error:**
```
Error initializing camera: Unable to open video device
```

**Cause:** Camera not detected or wrong device index.

**Solution:**

**1. Check camera is detected:**
```bash
lsusb | grep -i camera
ls /dev/video*
```

**2. Try different device index:**

Edit `config.py`:
```python
CAMERA_DEVICE_INDEX = 0  # Try 0, 1, 2, etc.
```

**3. Check camera permissions:**
```bash
sudo usermod -aG video $USER
```

**4. Test camera manually:**
```bash
sudo apt-get install fswebcam -y
fswebcam test.jpg
```

---

### Issue 7: "Microphone not found"

**Error:**
```
Error initializing microphone: No microphone found
```

**Cause:** Microphone not detected or missing audio libraries.

**Solution:**

**1. Check microphone:**
```bash
arecord -l
```

Should list your USB microphone.

**2. Install audio dependencies:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio -y
```

**3. Restart containers:**
```bash
docker compose restart
```

**4. Test microphone:**
```bash
arecord -d 5 test.wav  # Record 5 seconds
aplay test.wav         # Play it back
```

---

## 🐳 Docker Issues

### Issue 8: Docker out of disk space

**Error:**
```
Error: No space left on device
```

**Solution:**

**1. Clean Docker cache:**
```bash
docker system prune -a -f
docker volume prune -f
```

**2. Check disk space:**
```bash
df -h
```

**3. Remove old images:**
```bash
docker images
docker rmi IMAGE_ID
```

**4. Use larger SD card:**
- Recommended: 64GB+ for production

---

### Issue 9: Container won't start

**Error:**
```
Container exited with code 1
```

**Solution:**

**1. Check logs:**
```bash
docker logs smart-hive-edge
docker logs smart-hive-dashboard
```

**2. Check for port conflicts:**
```bash
sudo netstat -tulpn | grep -E '5000|5001'
```

**3. Rebuild from scratch:**
```bash
docker compose down -v
docker compose up --build
```

**4. Check docker-compose.yml syntax:**
```bash
docker compose config
```

---

### Issue 10: Permission denied errors

**Error:**
```
PermissionError: [Errno 13] Permission denied
```

**Solution:**

**1. Fix AWS credentials permissions:**
```bash
chmod 600 ~/.aws/credentials
chmod 644 ~/.aws/config
```

**2. Fix project permissions:**
```bash
sudo chown -R pi:pi /home/pi/smart-hive-ai
```

**3. Add user to docker group:**
```bash
sudo usermod -aG docker pi
newgrp docker
```

---

## 🌐 Network Issues

### Issue 11: Can't access dashboard

**Problem:** `http://raspberrypi.local:5000` doesn't load.

**Solution:**

**1. Find Pi's IP address:**
```bash
hostname -I
# Use: http://192.168.x.x:5000
```

**2. Check containers are running:**
```bash
docker ps
# Should see: smart-hive-dashboard and smart-hive-edge
```

**3. Check firewall:**
```bash
sudo ufw status
sudo ufw allow 5000
sudo ufw allow 5001
```

**4. Test from Pi itself:**
```bash
curl http://localhost:5000
```

---

### Issue 12: AWS IoT connection failed

**Error:**
```
❌ Failed to connect to AWS IoT Core
```

**Solution:**

**1. Check certificates exist:**
```bash
ls -la /home/pi/smart-hive-ai/certs/
# Should see: certificate.pem.crt, private.pem.key, AmazonRootCA1.pem
```

**2. Verify endpoint in config.py:**
```python
IOT_ENDPOINT = "your-endpoint.iot.ap-southeast-2.amazonaws.com"
```

**3. Check Thing policy in AWS IoT Console:**

Policy should allow:
- `iot:Connect`
- `iot:Publish`
- `iot:Subscribe`
- `iot:Receive`

**4. Test connection:**
```bash
mosquitto_pub -h your-endpoint.iot.region.amazonaws.com \
  --cert certs/certificate.pem.crt \
  --key certs/private.pem.key \
  --cafile certs/AmazonRootCA1.pem \
  -t test/topic -m "test"
```

---

## 📊 Data Issues

### Issue 13: No data in DynamoDB

**Problem:** Table is empty or not updating.

**Solution:**

**1. Check ENABLE_DYNAMODB flag:**
```python
# config.py
ENABLE_DYNAMODB = True
```

**2. Check logs for writes:**
```bash
docker logs smart-hive-edge | grep DynamoDB
# Should see: ✅ DynamoDB: Wrote record at...
```

**3. Verify table name:**
```python
# config.py
DYNAMODB_TABLE = "SmartHiveTelemetry"
```

**4. Test write manually:**
```bash
aws dynamodb put-item \
  --table-name SmartHiveTelemetry \
  --item '{"device_id": {"S": "test"}, "timestamp": {"N": "1234567890"}}'
```

---

### Issue 14: Mock data instead of real

**Problem:** Seeing fixed values (34.5°C, 57.8% humidity).

**Solution:**

**1. Check IS_MOCK_ENVIRONMENT:**
```python
# config.py
IS_MOCK_ENVIRONMENT = False  # Must be False on Pi
```

**2. Verify sensors detected:**
```bash
sudo i2cdetect -y 1
# Should show I2C devices
```

**3. Check logs:**
```bash
docker logs smart-hive-edge | grep "Initialized"
# Should see: "Initialized Real BME280", not "Mock"
```

**4. Restart after config change:**
```bash
docker compose restart
```

---

### Issue 15: Timestamps confusing

**Problem:** Numbers like 1760358523 in DynamoDB.

**Explanation:** Unix timestamp (seconds since Jan 1, 1970 UTC).

**Convert to readable:**
```python
from datetime import datetime
ts = 1760358523
print(datetime.fromtimestamp(ts))
# Output: 2025-10-13 12:42:03
```

**Query by time range:**
```python
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
table = dynamodb.Table('SmartHiveTelemetry')

# Last 24 hours
start = int((datetime.now() - timedelta(days=1)).timestamp())

response = table.query(
    KeyConditionExpression='device_id = :device AND #ts > :start',
    ExpressionAttributeNames={'#ts': 'timestamp'},
    ExpressionAttributeValues={
        ':device': 'SmartHive_Pi',
        ':start': start
    }
)
```

---

## 🎯 Performance Issues

### Issue 16: System slow/laggy

**Cause:** Resource constraints on Raspberry Pi.

**Solution:**

**1. Check resource usage:**
```bash
htop  # Install: sudo apt-get install htop
docker stats
```

**2. Reduce telemetry frequency:**
```python
# config.py
TELEMETRY_INTERVAL_SECONDS = 30  # Increase from 5
S3_SNAPSHOT_INTERVAL_SECONDS = 600  # Increase from 120
VISION_LOOP_INTERVAL_SECONDS = 10  # Increase from 2
```

**3. Disable unused features temporarily:**
```python
# config.py
ENABLE_S3 = False  # If you don't need snapshots
```

**4. Use lightweight dashboard:**

Reduce Chart.js update frequency in `dashboard/static/app.js`.

---

### Issue 17: High temperature

**Problem:** Pi running hot (>80°C).

**Solution:**

**1. Add heatsinks or fan**

**2. Reduce CPU load:**
```python
# config.py
VISION_LOOP_INTERVAL_SECONDS = 10  # Reduce vision processing
```

**3. Check CPU frequency:**
```bash
vcgencmd measure_temp
vcgencmd measure_clock arm
```

**4. Improve ventilation** in deployment location.

---

## 🔍 Debugging Commands

### General Diagnostics

```bash
# System info
uname -a
cat /etc/os-release

# Docker status
docker ps -a
docker stats --no-stream

# Disk space
df -h

# Memory
free -h

# Network
ip addr
ping google.com

# Logs
docker logs smart-hive-edge --tail 100
docker logs smart-hive-dashboard --tail 100

# AWS credentials
aws sts get-caller-identity
aws dynamodb list-tables
aws s3 ls

# Hardware
sudo i2cdetect -y 1
lsusb
arecord -l
ls /dev/video*

# Temperature
vcgencmd measure_temp
```

---

## 📞 Still Stuck?

### Collect Diagnostic Info

```bash
# Create diagnostic report
cd /home/pi/smart-hive-ai

echo "=== System Info ===" > diagnostic.txt
uname -a >> diagnostic.txt
cat /etc/os-release >> diagnostic.txt

echo -e "\n=== Docker ===" >> diagnostic.txt
docker --version >> diagnostic.txt
docker compose version >> diagnostic.txt
docker ps -a >> diagnostic.txt

echo -e "\n=== I2C Devices ===" >> diagnostic.txt
sudo i2cdetect -y 1 >> diagnostic.txt

echo -e "\n=== USB Devices ===" >> diagnostic.txt
lsusb >> diagnostic.txt

echo -e "\n=== Disk Space ===" >> diagnostic.txt
df -h >> diagnostic.txt

echo -e "\n=== Container Logs ===" >> diagnostic.txt
docker logs smart-hive-edge --tail 50 >> diagnostic.txt 2>&1

cat diagnostic.txt
```

---

## ✅ Prevention Checklist

**Before reporting issues, verify:**

- [ ] Docker is running: `docker ps`
- [ ] AWS credentials exist: `cat ~/.aws/credentials`
- [ ] I2C enabled: `sudo i2cdetect -y 1`
- [ ] Sensors connected properly
- [ ] config.py has correct settings
- [ ] Containers built recently: `docker compose up --build`
- [ ] Logs checked: `docker logs smart-hive-edge`
- [ ] Network connectivity: `ping google.com`
- [ ] Enough disk space: `df -h`

---

## 🎓 Common Mistakes

1. **Forgetting to change IS_MOCK_ENVIRONMENT to False**
2. **Not copying AWS credentials to Pi**
3. **Wrong IAM permissions on AWS**
4. **I2C not enabled before connecting sensors**
5. **Wrong I2C addresses (0x76 vs 0x77)**
6. **Not rebuilding after config changes**
7. **Using old cached Docker images**
8. **Insufficient SD card space (<32GB)**

---

**Most issues are resolved by:**
1. Checking logs
2. Verifying credentials
3. Rebuilding containers
4. Following deployment guide exactly

See `DEPLOYMENT_GUIDE.md` for complete setup instructions.
