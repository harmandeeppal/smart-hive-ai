# Smart Hive AI - Deployment Guide

## Table of Contents
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [AWS Configuration](#aws-configuration)
- [Raspberry Pi Setup](#raspberry-pi-setup)
- [Docker Deployment](#docker-deployment)
- [Verification](#verification)
- [Production Optimization](#production-optimization)

## Prerequisites

### Hardware Requirements
- Raspberry Pi 4 (2GB+ RAM recommended)
- MicroSD Card (16GB minimum, Class 10)
- 5V 3A USB-C Power Supply
- BME280 Temperature/Humidity Sensor
- LIS3DH Accelerometer
- USB Microphone (Samson or compatible)
- USB Webcam (Logitech C270 or compatible)
- Internet connectivity (Ethernet or WiFi)

### Software Requirements
- Raspberry Pi OS (64-bit recommended)
- Docker and Docker Compose
- Git
- Python 3.9+ (for local development)

### AWS Requirements
- AWS Account with IoT Core enabled
- IAM user with appropriate permissions
- DynamoDB table created
- IoT Thing and certificates generated

## Initial Setup

### 1. Prepare Raspberry Pi

**Install Raspberry Pi OS**:
```bash
# Download Raspberry Pi Imager from:
# https://www.raspberrypi.org/software/

# Flash SD card with Raspberry Pi OS (64-bit)
# Enable SSH during imaging for headless setup
```

**First Boot Configuration**:
```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y git i2c-tools python3-pip

# Enable I2C interface
sudo raspi-config
# Navigate to: Interface Options -> I2C -> Enable

# Reboot
sudo reboot
```

### 2. Verify Hardware Connections

**I2C Sensors**:
```bash
# Scan for I2C devices
sudo i2cdetect -y 1

# Expected output:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- 19 -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 70: -- -- -- -- -- -- 76 --
```

**USB Devices**:
```bash
# List USB devices
lsusb

# List video devices
ls -la /dev/video*

# List audio devices
arecord -l
```

### 3. Configure User Permissions

```bash
# Add pi user to required groups
sudo usermod -a -G i2c,video,audio pi

# Verify group membership
groups pi

# Reboot to apply
sudo reboot
```

## AWS Configuration

### 1. Create IoT Thing

**Via AWS Console**:
1. Navigate to AWS IoT Core
2. Go to "Manage" -> "Things"
3. Click "Create" -> "Create a single thing"
4. Name: `SmartHive_Pi`
5. Click "Next"

### 2. Generate Certificates

1. Choose "Auto-generate a new certificate"
2. Download all certificates:
   - Device certificate (certificate.pem.crt)
   - Private key (private.pem.key)
   - Amazon Root CA 1 (AmazonRootCA1.pem)
3. Click "Activate" to activate the certificate
4. Click "Attach policy"

### 3. Create and Attach IoT Policy

**Policy Name**: `SmartHivePolicy`

**Policy Document**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect"
      ],
      "Resource": "arn:aws:iot:ap-southeast-2:YOUR_ACCOUNT_ID:client/SmartHive_Pi"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish",
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:ap-southeast-2:YOUR_ACCOUNT_ID:topic/hive/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Subscribe"
      ],
      "Resource": [
        "arn:aws:iot:ap-southeast-2:YOUR_ACCOUNT_ID:topicfilter/hive/*"
      ]
    }
  ]
}
```

### 4. Create DynamoDB Table

**Via AWS CLI**:
```bash
aws dynamodb create-table \
  --table-name SmartHiveTelemetry \
  --attribute-definitions \
    AttributeName=device_id,AttributeType=S \
    AttributeName=timestamp,AttributeType=N \
  --key-schema \
    AttributeName=device_id,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-2
```

**Via AWS Console**:
1. Navigate to DynamoDB
2. Click "Create table"
3. Table name: `SmartHiveTelemetry`
4. Partition key: `device_id` (String)
5. Sort key: `timestamp` (Number)
6. Use default settings for other options
7. Click "Create table"

### 5. Create IAM User

**Create User**:
```bash
aws iam create-user --user-name smarthive-user
```

**Attach Policy**:
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
      "Resource": "arn:aws:dynamodb:ap-southeast-2:YOUR_ACCOUNT_ID:table/SmartHiveTelemetry"
    }
  ]
}
```

**Note:** This policy only grants DynamoDB access. S3 storage is not used in current implementation.

**Generate Access Keys**:
```bash
aws iam create-access-key --user-name smarthive-user
# Save the AccessKeyId and SecretAccessKey
```

## Raspberry Pi Setup

### 1. Clone Repository

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local

# Clone repository
cd ~
git clone https://github.com/harmandeeppal/smart-hive-ai.git
cd smart-hive-ai
```

### 2. Configure AWS Credentials

```bash
# Configure AWS CLI
aws configure
# Enter:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: ap-southeast-2
# - Default output format: json

# Verify configuration
aws sts get-caller-identity
```

### 3. Add Certificates

```bash
# Create certs directory if not exists
mkdir -p certs

# Copy certificates (from your local machine)
scp your-certificate.pem.crt pi@raspberrypi.local:~/smart-hive-ai/certs/
scp your-private.pem.key pi@raspberrypi.local:~/smart-hive-ai/certs/

# Download Amazon Root CA (on Raspberry Pi)
cd ~/smart-hive-ai/certs
wget https://www.amazontrust.com/repository/AmazonRootCA1.pem

# Set correct permissions
chmod 644 *.pem.crt AmazonRootCA1.pem
chmod 600 *.pem.key
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Required .env Variables**:
```bash
# AWS IoT Core Endpoint
AWS_ENDPOINT=xxxxxx-ats.iot.ap-southeast-2.amazonaws.com

# Certificate filenames (just the filenames, not full paths)
CERT_FILE_NAME=your-certificate.pem.crt
KEY_FILE_NAME=your-private.pem.key

# Flask secret key (generate a random string)
SECRET_KEY=your-random-secret-key-here

# DynamoDB Configuration (optional - enables cloud storage)
ENABLE_DYNAMODB=false
```

**Note:** Set `ENABLE_DYNAMODB=true` only if you want to store data in AWS DynamoDB. System works locally without it.

**Find Your IoT Endpoint**:
```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS
```

### 5. Update config.py

```bash
nano config.py
```

**Verify Settings**:
```python
# Ensure production mode
IS_MOCK_ENVIRONMENT = False

# Enable DynamoDB
ENABLE_DYNAMODB = True

# Verify AWS region matches your DynamoDB table
AWS_REGION = "ap-southeast-2"

# Verify sensor addresses match your hardware
BME280_ADDRESS = 0x76
LIS3DH_ADDRESS = 0x19
```

## Docker Deployment

### 1. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add pi user to docker group
sudo usermod -aG docker pi

# Install Docker Compose
sudo apt install -y docker-compose

# Verify installation
docker --version
docker compose version

# Logout and login for group changes to take effect
exit
# SSH back in
ssh pi@raspberrypi.local
```

### 2. Build and Start Containers

```bash
cd ~/smart-hive-ai

# Pull/build Docker images
docker compose build

# Start services in detached mode
docker compose up -d

# Check container status
docker ps
```

**Expected Output**:
```
CONTAINER ID   IMAGE                  STATUS         PORTS
xxxxxxxxxxxx   smart-hive-edge        Up 10 seconds  0.0.0.0:5001->5001/tcp
xxxxxxxxxxxx   smart-hive-dashboard   Up 10 seconds  0.0.0.0:5000->5000/tcp
```

### 3. Monitor Startup

```bash
# View edge application logs
docker logs -f smart-hive-edge

# Expected initialization messages:
# INITIALIZING REAL HARDWARE...
#   BME280 Temperature/Humidity sensor initialized
#   LIS3DH Vibration sensor initialized
#   INMP441 Sound sensor initialized
#   USB Camera initialized (V4L2 backend, 640x480)
# Dashboard MQTT client connected successfully.
# Smart Hive System initialized successfully
```

## Verification

### 1. Check Sensor Initialization

```bash
# View initialization logs
docker logs smart-hive-edge | grep "initialized"

# Should show all sensors initialized:
# ✓ BME280 (Temperature/Humidity)
# ✓ LIS3DH (Vibration)
# ✓ INMP441 (Microphone)
# ✓ USB Camera
```

### 2. Check Audio ML Service

```bash
# Check audio ML container
docker logs smart-hive-audio | grep "model"

# Expected: "Audio model loaded successfully"
# Should show: 312 features, Random Forest classifier
```

### 3. Verify MQTT Connection

```bash
# Check MQTT connection
docker logs smart-hive-edge | grep -i "mqtt"

# Expected: "MQTT connected successfully"

# Test MQTT messages
docker exec -it mosquitto mosquitto_sub -t "hive/#" -v
# Should see telemetry and audio ML messages
```

### 4. Test Video Stream

```bash
# From another computer on same network:
curl http://raspberrypi.local:5001/video_feed

# Should return MJPEG stream data

# Or open in browser:
# http://raspberrypi.local:5001/video_feed
```

### 5. Access Dashboard

**From Web Browser**:
```
http://raspberrypi.local:5000
```

**Expected**:
- Live USB camera video feed from hive
- Real-time sensor readings (temperature, humidity, vibration, sound)
- Audio ML predictions with confidence levels
- Sensor toggle controls
- Status indicators for each metric

### 6. Verify DynamoDB Writes (If Enabled)

**Only if `ENABLE_DYNAMODB=true` in your .env file:**

```bash
# Run diagnostic script
docker exec smart-hive-edge python3 scripts/diagnose_dynamodb.py

# Check recent records
docker exec smart-hive-edge python3 scripts/check_dynamodb_timestamps.py
```

**Via AWS Console**:
1. Navigate to DynamoDB
2. Select `SmartHiveTelemetry` table
3. Click "Explore table items"
4. Verify records with `device_id: SmartHive_Pi`

**Note:** DynamoDB is optional. System works locally with MQTT broker only.

## Production Optimization

### 1. System Performance

```bash
# Monitor system resources
htop

# Check CPU temperature
vcgencmd measure_temp

# Monitor disk space
df -h
```

### 2. Auto-Start on Boot

```bash
# Enable Docker service
sudo systemctl enable docker

# Docker Compose services will auto-start
# Verify with:
sudo reboot

# After reboot, check:
docker ps
```

### 3. Log Rotation

```bash
# Configure Docker log rotation
sudo nano /etc/docker/daemon.json
```

**Add**:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

```bash
# Restart Docker
sudo systemctl restart docker
```

### 4. Monitoring and Maintenance

```bash
# Create maintenance script
nano ~/maintenance.sh
```

**Add**:
```bash
#!/bin/bash
# Smart Hive Maintenance Script

echo "=== Smart Hive System Status ==="
echo "Date: $(date)"
echo ""

echo "Container Status:"
docker ps

echo ""
echo "Disk Usage:"
df -h /

echo ""
echo "Memory Usage:"
free -h

echo ""
echo "CPU Temperature:"
vcgencmd measure_temp

echo ""
echo "Recent Logs:"
docker logs smart-hive-edge --tail 20
```

```bash
# Make executable
chmod +x ~/maintenance.sh

# Run
./maintenance.sh
```

### 5. Backup Strategy

```bash
# Backup configuration and certificates
tar -czf smarthive-backup-$(date +%Y%m%d).tar.gz \
  ~/smart-hive-ai/.env \
  ~/smart-hive-ai/certs/ \
  ~/.aws/

# Copy to safe location
# scp smarthive-backup-*.tar.gz user@backup-server:/path/
```

## Updating the System

### 1. Update Code

```bash
cd ~/smart-hive-ai

# Pull latest changes
git pull origin main

# Rebuild containers
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 2. Update System Packages

```bash
# Update Raspberry Pi OS
sudo apt update
sudo apt upgrade -y

# Update Docker
sudo apt upgrade docker-ce docker-ce-cli containerd.io
```

## Troubleshooting Deployment

If you encounter issues during deployment, refer to:
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Docker Logs](#view-logs)
- [System Diagnostics](#run-diagnostics)

### View Logs

```bash
# Edge application
docker logs smart-hive-edge

# Dashboard
docker logs smart-hive-dashboard

# Follow logs in real-time
docker logs -f smart-hive-edge
```

### Run Diagnostics

```bash
# I2C devices
sudo i2cdetect -y 1

# DynamoDB connectivity
docker exec smart-hive-edge python3 scripts/diagnose_dynamodb.py

# AWS credentials
docker exec smart-hive-edge python3 -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

## Next Steps

After successful deployment:
1. Monitor system for 24 hours to ensure stability
2. Adjust sensor thresholds in config.py if needed
3. Set up alerting for queen detection events
4. Configure regular backups
5. Review AWS costs and optimize as needed

## Support

For additional help:
- Documentation index: [../index.md](../index.md)
- Issues: [GitHub Issues](https://github.com/harmandeeppal/smart-hive-ai/issues)
- Troubleshooting: [reference/troubleshooting.md](../reference/troubleshooting.md)
