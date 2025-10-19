# Smart Hive AI - Troubleshooting Guide

> **📚 For comprehensive troubleshooting guides, see:**
> - [../USB_CAMERA_TROUBLESHOOTING.md](../USB_CAMERA_TROUBLESHOOTING.md) - Camera issues
> - [../AUDIO_TROUBLESHOOTING.md](../AUDIO_TROUBLESHOOTING.md) - Audio ML issues
> - [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) - Complete troubleshooting section

## Table of Contents
- [Hardware Issues](#hardware-issues)
- [Sensor Problems](#sensor-problems)
- [AWS Connectivity](#aws-connectivity)
- [Docker Issues](#docker-issues)
- [Video Streaming](#video-streaming)
- [Audio ML Issues](#audio-ml-issues)
- [DynamoDB Data Flow](#dynamodb-data-flow)

## Hardware Issues

### I2C Devices Not Detected

**Problem**: Sensors not showing up in `i2cdetect` scan

**Solution**:
```bash
# Enable I2C interface
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable

# Verify I2C is enabled
ls /dev/i2c-*

# Scan for devices
sudo i2cdetect -y 1
```

### I2C Permission Denied

**Problem**: Container cannot access I2C devices

**Symptoms**:
```
Error initializing Real BME280: No I2C device at address: 0x76
PermissionError: [Errno 13] Permission denied: '/dev/i2c-1'
```

**Solution**:
```bash
# Add user to i2c group
sudo usermod -a -G i2c pi

# Reboot to apply changes
sudo reboot

# Verify group membership
groups pi
# Should show: pi adm dialout cdrom sudo audio video plugdev games users input netdev i2c
```

### BME280 Sensor Issues

**Problem**: BME280 not initializing

**Common Causes**:
1. Wrong I2C address (0x76 vs 0x77)
2. Loose wiring connections
3. Insufficient power supply

**Diagnosis**:
```bash
# Check which address the sensor uses
sudo i2cdetect -y 1

# If sensor shows at 0x77 instead of 0x76, update config.py:
BME280_ADDRESS = 0x77
```

**Wiring Check**:
- VCC -> 3.3V (Pin 1)
- GND -> Ground (Pin 6)
- SCL -> GPIO 3 (Pin 5)
- SDA -> GPIO 2 (Pin 3)

### LIS3DH Accelerometer Issues

**Problem**: Vibration sensor not responding

**Diagnosis**:
```bash
# Verify sensor address
sudo i2cdetect -y 1
# Should show device at 0x19 or 0x18

# If different address, update config.py:
LIS3DH_ADDRESS = 0x18  # or 0x19
```

### USB Camera Not Found

**Problem**: Camera device not accessible

**Solution**:
```bash
# List video devices
ls -la /dev/video*

# Test camera
v4l2-ctl --list-devices

# Check permissions
sudo usermod -a -G video pi

# Verify camera works
ffplay /dev/video0
```

### Microphone Not Detected

**Problem**: USB microphone not recognized

**Solution**:
```bash
# List audio devices
arecord -l

# Test recording
arecord -D hw:1,0 -d 3 test.wav
aplay test.wav

# Check ALSA configuration
sudo nano /etc/asound.conf
```

## Sensor Problems

### Mock vs Real Environment

**Problem**: Accidentally using mock sensors in production

**Symptoms**:
- Sensor readings are too consistent
- No variation in data
- Missing "Successfully initialized Real..." messages

**Solution**:
```python
# In config.py, ensure:
IS_MOCK_ENVIRONMENT = False
```

### Sensor Initialization Failures

**Problem**: Some sensors fail to initialize

**Graceful Degradation**:
The system continues operation with available sensors. Check logs:

```bash
docker logs smart-hive-edge | grep -i "initialized"
docker logs smart-hive-edge | grep -i "error"
```

## AWS Connectivity

### AWS IoT Connection Failed

**Problem**: Cannot connect to AWS IoT Core

**Diagnosis**:
```bash
# Verify credentials exist
ls -la ~/.aws/
# Should show: credentials, config

# Test AWS CLI access
aws sts get-caller-identity

# Verify certificates
ls -la certs/
# Should show: AmazonRootCA1.pem, certificate.pem.crt, private.pem.key
```

**Certificate Issues**:
```bash
# Check certificate permissions
chmod 644 certs/*.pem.crt
chmod 600 certs/*.pem.key

# Verify certificate validity
openssl x509 -in certs/your-certificate.pem.crt -text -noout
```

**Endpoint Configuration**:
```bash
# Verify AWS_ENDPOINT in .env file
cat .env | grep AWS_ENDPOINT

# Should match your IoT endpoint:
AWS_ENDPOINT=xxxxxx-ats.iot.ap-southeast-2.amazonaws.com
```

### MQTT Connection Drops

**Problem**: Intermittent MQTT disconnections

**Solution**:
1. Check network stability
2. Verify IoT Core policy allows connection
3. Monitor AWS IoT Core metrics in console

```bash
# View MQTT connection logs
docker logs smart-hive-edge | grep -i "mqtt"
```

### DynamoDB Write Failures

**Problem**: Telemetry not appearing in DynamoDB

**Diagnosis**:
```bash
# Run diagnostic script
docker exec smart-hive-edge python3 scripts/diagnose_dynamodb.py
```

**Common Issues**:

1. **IAM Permissions Missing**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:ap-southeast-2:*:table/SmartHiveTelemetry"
    }
  ]
}
```

2. **Wrong Region**:
```python
# In config.py, verify:
AWS_REGION = "ap-southeast-2"  # Match your table's region
```

3. **ENABLE_DYNAMODB = False**:
```python
# In config.py:
ENABLE_DYNAMODB = True
```

## Docker Issues

### Container Permission Problems

**Problem**: Container cannot access hardware devices

**Solution**:
```yaml
# In docker-compose.yml, ensure:
services:
  edge-app:
    devices:
      - /dev/i2c-1:/dev/i2c-1
      - /dev/video0:/dev/video0
      - /dev/snd:/dev/snd
    privileged: true
```

### Container Startup Failures

**Problem**: Container exits immediately

**Diagnosis**:
```bash
# View container logs
docker logs smart-hive-edge

# Check container status
docker ps -a

# Inspect container
docker inspect smart-hive-edge
```

### AWS Credentials Not Mounted

**Problem**: Container cannot access AWS credentials

**Solution**:
```yaml
# In docker-compose.yml:
volumes:
  - ~/.aws:/root/.aws:ro
```

**Verify**:
```bash
# Check credentials are mounted
docker exec smart-hive-edge ls -la /root/.aws/

# Test AWS access from container
docker exec smart-hive-edge python3 -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

### Model File Not Found

**Problem**: TFLite model cannot be loaded

**Error**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'models/queen_bee.tflite'
```

**Solution**:
```bash
# Verify model exists
ls -la models/queen_bee.tflite

# Check docker-compose mounts entire project
docker exec smart-hive-edge ls -la /app/models/
```

## Video Streaming

### Video Feed Not Loading

**Problem**: Dashboard shows "Could not connect to video stream"

**Diagnosis**:
```bash
# Check if edge-app is running
docker ps | grep edge-app

# Test video endpoint directly
curl http://localhost:5001/video_feed

# Check edge-app logs
docker logs smart-hive-edge | grep -i "video"
```

**Solutions**:
1. Verify camera is connected and accessible
2. Check Docker network connectivity
3. Ensure port 5001 is not blocked

### Black Screen / No Frames

**Problem**: Video stream shows black screen

**Causes**:
1. Camera not properly initialized
2. Wrong camera device index
3. Insufficient lighting

**Solution**:
```python
# In config.py, try different device:
CAMERA_DEVICE_INDEX = 0  # Try 0, 1, 2, etc.

# Or test with command line:
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

### AI Detection Not Working

**Problem**: Queen bee detection not triggering

**Diagnosis**:
```bash
# Check vision processing mode
docker logs smart-hive-edge | grep -i "vision"

# Verify model loaded successfully
docker logs smart-hive-edge | grep -i "tflite"
```

**Configuration**:
```python
# In config.py:
VISION_DETECTION_MODE = "continuous"  # or "interval"
VISION_PROCESS_EVERY_N_FRAMES = 3
VISION_CONFIDENCE_THRESHOLD = 0.5  # Lower for more detections
```

## DynamoDB Data Flow

### Data Gap in DynamoDB

**Problem**: Missing records in DynamoDB table

**Diagnosis**:
```bash
# Check recent writes
python3 scripts/check_dynamodb_timestamps.py

# Run full diagnostic
python3 scripts/diagnose_dynamodb.py
```

**Verify**:
1. Container has been running continuously
2. ENABLE_DYNAMODB = True in config
3. AWS credentials are valid
4. IAM permissions include PutItem

### Timestamp Timezone Issues

**Problem**: Timestamps not showing correct timezone

**Solution**:
The system automatically adds `timestamp_nz` field with New Zealand timezone.

**Verify**:
```bash
# Check logs for timezone conversion
docker logs smart-hive-edge | grep "timestamp_nz"

# Query DynamoDB for recent records
aws dynamodb query \
  --table-name SmartHiveTelemetry \
  --key-condition-expression "device_id = :id" \
  --expression-attribute-values '{":id":{"S":"SmartHive_Pi"}}' \
  --limit 1 \
  --scan-index-forward false
```

## General Troubleshooting

### System Not Starting

**Checklist**:
1. Check all hardware connections
2. Verify power supply is adequate (5V 3A for Pi 4)
3. Confirm SD card has sufficient space
4. Review Docker Compose configuration
5. Check environment variables in .env file

### Performance Issues

**Symptoms**:
- Slow dashboard updates
- High CPU usage
- System lagging

**Optimization**:
```python
# In config.py, reduce processing:
VISION_PROCESS_EVERY_N_FRAMES = 5  # Process fewer frames
VIDEO_STREAM_FPS = 15  # Lower frame rate
TELEMETRY_INTERVAL_SECONDS = 120  # Less frequent telemetry
```

### Getting Help

**Collect diagnostic information**:
```bash
# System information
uname -a
cat /etc/os-release

# Docker information
docker --version
docker compose version

# Container status
docker ps -a

# Recent logs
docker logs smart-hive-edge --tail 100 > edge-logs.txt
docker logs smart-hive-dashboard --tail 100 > dashboard-logs.txt

# I2C devices
sudo i2cdetect -y 1 > i2c-devices.txt

# USB devices
lsusb > usb-devices.txt
```

## Quick Reference Commands

```bash
# Restart containers
docker compose restart

# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d

# View live logs
docker logs -f smart-hive-edge

# Check I2C devices
sudo i2cdetect -y 1

# Test AWS credentials
aws sts get-caller-identity

# Run diagnostics
docker exec smart-hive-edge python3 scripts/diagnose_dynamodb.py

# Monitor system resources
htop
```

## Additional Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [AWS IoT Core Developer Guide](https://docs.aws.amazon.com/iot/)
- [Docker Documentation](https://docs.docker.com/)
- [Project GitHub Repository](https://github.com/harmandeeppal/smart-hive-ai)
