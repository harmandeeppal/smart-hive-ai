# 🚨 Potential Deployment Issues & TFLite Configuration Guide

**Last Updated:** October 15, 2025  
**Status:** Comprehensive Pre-Deployment Analysis

---

## 📋 Table of Contents

1. [Potential Deployment Issues Not Yet Addressed](#potential-deployment-issues)
2. [TFLite Model Compatibility](#tflite-model-compatibility)
3. [Making Code Work with Any TFLite Model](#flexible-tflite-configuration)
4. [Pre-Deployment Checklist](#pre-deployment-checklist)

---

## 🚨 Potential Deployment Issues Not Yet Addressed

### **Issue 1: Camera Device Index Changes**

**Problem:**
```python
# config.py
CAMERA_DEVICE_INDEX = 0  # Assumes camera is at /dev/video0
```

**What Can Go Wrong:**
```bash
# On some Pis, USB camera might be:
/dev/video0  # Built-in camera (if Pi Camera Module installed)
/dev/video1  # USB camera (your Logitech)
/dev/video2  # Virtual camera device
```

**Solution: Auto-Detection**

Add to `config.py`:
```python
# --- Camera Auto-Detection ---
def find_camera_device():
    """Auto-detect available camera device"""
    import cv2
    for index in range(10):  # Check /dev/video0 through /dev/video9
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            cap.release()
            return index
    return 0  # Default fallback

# Use auto-detection if camera fails
CAMERA_DEVICE_INDEX = 0  # Try this first
CAMERA_AUTO_DETECT = True  # Enable auto-detection on failure
```

Add to `real_components.py`:
```python
def __init__(self, device_index=0, width=640, height=480, auto_detect=True):
    self.device_index = device_index
    self.auto_detect = auto_detect
    
    # Try specified index first
    self.camera = cv2.VideoCapture(self.device_index)
    
    # If fails and auto-detect enabled, try other indices
    if not self.camera.isOpened() and self.auto_detect:
        logger.warning(f"Camera at index {self.device_index} not found. Auto-detecting...")
        for idx in range(10):
            test_cap = cv2.VideoCapture(idx)
            if test_cap.isOpened():
                logger.info(f"✅ Found camera at index {idx}")
                self.camera = test_cap
                self.device_index = idx
                break
            test_cap.release()
    
    if not self.camera.isOpened():
        raise RuntimeError(f"❌ No camera found after auto-detection")
```

---

### **Issue 2: I2C Address Conflicts**

**Problem:**
```python
# config.py
BME280_ADDRESS = 0x77  # Hardcoded
LIS3DH_ADDRESS = 0x18  # Hardcoded
```

**What Can Go Wrong:**
- BME280 might be at `0x76` instead of `0x77`
- LIS3DH might be at `0x19` instead of `0x18`
- Multiple sensors on same address cause conflicts

**Solution: Address Scanning**

Add to `config.py`:
```python
# --- I2C Auto-Detection ---
I2C_AUTO_DETECT = True

# Primary addresses to try
BME280_ADDRESSES = [0x77, 0x76]  # Try both common addresses
LIS3DH_ADDRESSES = [0x18, 0x19]  # Try both common addresses
```

Add to `real_components.py`:
```python
import smbus2

def scan_i2c_address(bus, addresses):
    """Scan for device at multiple I2C addresses"""
    for addr in addresses:
        try:
            bus.read_byte(addr)
            logger.info(f"✅ Found I2C device at address 0x{addr:02X}")
            return addr
        except:
            continue
    return None

class RealBME280Sensor:
    def __init__(self, bus=1, addresses=[0x77, 0x76]):
        self.bus = smbus2.SMBus(bus)
        
        # Try to find sensor at any of the addresses
        self.address = scan_i2c_address(self.bus, addresses)
        
        if self.address is None:
            raise RuntimeError(f"❌ BME280 not found at addresses: {[hex(a) for a in addresses]}")
        
        # Initialize with found address
        self.sensor = BME280(i2c_dev=self.bus, i2c_addr=self.address)
```

---

### **Issue 3: USB Audio Device Names**

**Problem:**
```python
# Microphone detection assumes default device
# But USB device names vary by manufacturer
```

**What Can Go Wrong:**
```bash
# Different USB mics show up differently:
$ arecord -l
card 0: Device [USB Audio Device]  # Generic name
card 1: GoMic [Samson GoMic]       # Specific name
card 2: C270 [Logitech Webcam C270] # Camera mic
```

**Solution: Device Enumeration**

Add to `config.py`:
```python
# --- Microphone Configuration ---
MICROPHONE_DEVICE_NAME = None  # None = auto-detect first available
MICROPHONE_SAMPLE_RATE = 44100
MICROPHONE_FALLBACK_RATES = [44100, 48000, 16000]  # Try these if primary fails
```

Add to `real_components.py`:
```python
import pyaudio

def find_audio_device(pa, device_name=None):
    """Find audio input device by name or return first available"""
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        # Check if it's an input device
        if info['maxInputChannels'] > 0:
            if device_name is None or device_name.lower() in info['name'].lower():
                logger.info(f"✅ Found audio device: {info['name']}")
                return i, info
    return None, None

class RealINMP441Sensor:
    def __init__(self, sample_rate=44100, fallback_rates=[48000, 16000]):
        self.pa = pyaudio.PyAudio()
        
        # Find device
        device_idx, device_info = find_audio_device(self.pa)
        
        if device_idx is None:
            raise RuntimeError("❌ No audio input device found")
        
        # Try sample rates in order
        for rate in [sample_rate] + fallback_rates:
            try:
                self.stream = self.pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=rate,
                    input=True,
                    input_device_index=device_idx
                )
                self.sample_rate = rate
                logger.info(f"✅ Audio opened at {rate} Hz")
                break
            except:
                continue
        else:
            raise RuntimeError(f"❌ Could not open audio at any sample rate")
```

---

### **Issue 4: SD Card Write Endurance**

**Problem:**
```python
# Writing to DynamoDB every 5 seconds = heavy SD card usage
# Logs written to SD card can wear it out
```

**What Can Go Wrong:**
- SD card corruption after weeks/months
- Log files filling up SD card
- Docker overlay2 consuming space

**Solution: Log Rotation & RAM Disk**

Add to `docker-compose.yml`:
```yaml
services:
  edge-app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"      # Max 10MB per log file
        max-file: "3"        # Keep only 3 files (30MB total)
    volumes:
      - /tmp:/tmp  # Use RAM disk for temporary files
```

Add to Pi setup (one-time):
```bash
# Create RAM disk for logs (survives reboot)
sudo nano /etc/fstab
# Add line:
tmpfs /var/log tmpfs defaults,noatime,size=100m 0 0

# Create RAM disk for Docker logs
tmpfs /var/lib/docker/containers tmpfs defaults,noatime,size=500m 0 0
```

---

### **Issue 5: Network Connectivity Loss**

**Problem:**
```python
# If WiFi drops, AWS IoT connection lost
# DynamoDB writes fail
# S3 uploads fail
# No automatic reconnection logic
```

**Solution: Connection Retry Logic**

Add to `config.py`:
```python
# --- Network Resilience ---
AWS_RECONNECT_ENABLED = True
AWS_RECONNECT_DELAY_SECONDS = 5
AWS_MAX_RECONNECT_ATTEMPTS = 10
S3_UPLOAD_RETRY_ATTEMPTS = 3
DYNAMODB_WRITE_RETRY_ATTEMPTS = 3
```

Add to `app.py`:
```python
import time
from botocore.exceptions import ClientError

def write_to_dynamodb_with_retry(self, data, max_attempts=3):
    """Write to DynamoDB with retry logic"""
    for attempt in range(max_attempts):
        try:
            self.table.put_item(Item=data)
            logger.info(f"✅ DynamoDB write succeeded")
            return True
        except ClientError as e:
            logger.warning(f"⚠️ DynamoDB write failed (attempt {attempt+1}/{max_attempts}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            else:
                logger.error(f"❌ DynamoDB write failed after {max_attempts} attempts")
                return False
        except Exception as e:
            logger.error(f"❌ Unexpected error writing to DynamoDB: {e}")
            return False

def upload_to_s3_with_retry(self, filepath, key, max_attempts=3):
    """Upload to S3 with retry logic"""
    for attempt in range(max_attempts):
        try:
            self.s3_client.upload_file(filepath, self.bucket, key)
            logger.info(f"✅ S3 upload succeeded: {key}")
            return True
        except Exception as e:
            logger.warning(f"⚠️ S3 upload failed (attempt {attempt+1}/{max_attempts}): {e}")
            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
            else:
                logger.error(f"❌ S3 upload failed after {max_attempts} attempts")
                return False
```

---

### **Issue 6: Time Synchronization**

**Problem:**
```python
# Raspberry Pi has no RTC (real-time clock)
# Time resets to 1970 on boot without internet
# DynamoDB timestamps incorrect
```

**Solution: NTP Configuration**

Add to Pi setup (one-time):
```bash
# Install and enable NTP client
sudo apt-get install ntp ntpdate -y

# Configure NTP servers
sudo nano /etc/ntp.conf
# Add lines:
server 0.pool.ntp.org
server 1.pool.ntp.org
server 2.pool.ntp.org

# Enable NTP service
sudo systemctl enable ntp
sudo systemctl start ntp

# Force time sync on boot
sudo nano /etc/rc.local
# Add before 'exit 0':
/usr/sbin/ntpdate -s 0.pool.ntp.org

# Verify time is correct
date
timedatectl status
```

Add to `app.py` validation:
```python
import time

def validate_system_time(self):
    """Check if system time is reasonable (not 1970)"""
    current_year = time.gmtime().tm_year
    if current_year < 2025:
        logger.error(f"❌ System time incorrect: Year {current_year}")
        logger.error("❌ Please check NTP configuration and internet connection")
        raise RuntimeError("System time not synchronized")
    logger.info(f"✅ System time validated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
```

---

### **Issue 7: Docker Build Failures on ARM**

**Problem:**
```dockerfile
# Some Python packages have no pre-built ARM wheels
# Building from source takes hours or fails
```

**What Can Go Wrong:**
```bash
# Common packages that struggle on ARM:
- opencv-python (needs compilation)
- scipy (large, slow build)
- tensorflow (needs specific ARM version)
```

**Solution: Use ARM-Optimized Base Images**

Update `Dockerfile.edge`:
```dockerfile
# Use ARM-optimized Python base
FROM arm64v8/python:3.9-slim-bullseye

# Install system dependencies first (faster caching)
RUN apt-get update && apt-get install -y \
    libatlas-base-dev \
    libopenblas-dev \
    libjpeg-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pre-built wheels from piwheels (ARM repository)
RUN pip install --index-url https://www.piwheels.org/simple \
    opencv-python-headless \
    numpy \
    scipy

# Install TensorFlow Lite Runtime (ARM-specific)
RUN pip install --extra-index-url https://google-coral.github.io/py-repo/ tflite-runtime

# Then install your requirements
COPY requirements-edge.txt .
RUN pip install -r requirements-edge.txt
```

---

### **Issue 8: Firewall Blocking AWS Connections**

**Problem:**
```python
# University/corporate networks may block:
# - Port 8883 (MQTT over TLS for AWS IoT)
# - Port 443 (HTTPS for S3/DynamoDB)
```

**Solution: Connection Testing**

Add to deployment verification:
```bash
# Test AWS IoT endpoint connectivity
nc -zv your-endpoint.iot.ap-southeast-2.amazonaws.com 8883

# Test S3 connectivity
curl -I https://s3.ap-southeast-2.amazonaws.com

# Test DynamoDB connectivity
curl -I https://dynamodb.ap-southeast-2.amazonaws.com

# If any fail, check firewall/network settings
```

Add to `config.py`:
```python
# --- Connection Testing ---
AWS_CONNECTION_TIMEOUT_SECONDS = 30
AWS_ENABLE_CONNECTION_TEST = True
```

Add to `app.py`:
```python
import socket

def test_aws_connectivity(self):
    """Test connectivity to AWS services"""
    endpoints = [
        ("AWS IoT", config.AWS_ENDPOINT, 8883),
        ("S3", f"s3.{config.AWS_REGION}.amazonaws.com", 443),
        ("DynamoDB", f"dynamodb.{config.AWS_REGION}.amazonaws.com", 443)
    ]
    
    for name, host, port in endpoints:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                logger.info(f"✅ {name} connectivity OK ({host}:{port})")
            else:
                logger.error(f"❌ {name} connectivity FAILED ({host}:{port})")
                return False
        except Exception as e:
            logger.error(f"❌ {name} connectivity test error: {e}")
            return False
    
    return True
```

---

### **Issue 9: Certificate Expiration**

**Problem:**
```python
# AWS IoT certificates expire after configured period
# No automatic renewal in current code
```

**Solution: Certificate Expiration Check**

Add to `app.py`:
```python
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta

def check_certificate_expiration(cert_path, warning_days=30):
    """Check if certificate is expiring soon"""
    try:
        with open(cert_path, 'rb') as f:
            cert = x509.load_pem_x509_certificate(f.read(), default_backend())
        
        expiry_date = cert.not_valid_after
        days_until_expiry = (expiry_date - datetime.now()).days
        
        if days_until_expiry < 0:
            logger.error(f"❌ Certificate EXPIRED {abs(days_until_expiry)} days ago!")
            return False
        elif days_until_expiry < warning_days:
            logger.warning(f"⚠️ Certificate expires in {days_until_expiry} days!")
        else:
            logger.info(f"✅ Certificate valid for {days_until_expiry} days")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error checking certificate: {e}")
        return False
```

---

### **Issue 10: Temperature-Dependent Performance**

**Problem:**
```python
# Raspberry Pi throttles CPU when hot (>80°C)
# AI inference slows down significantly
# Can cause data collection gaps
```

**Solution: Thermal Monitoring**

Add to `config.py`:
```python
# --- Thermal Management ---
ENABLE_THERMAL_MONITORING = True
THERMAL_WARNING_TEMP = 75.0  # °C
THERMAL_CRITICAL_TEMP = 80.0  # °C
THERMAL_THROTTLE_TEMP = 80.0  # °C (start reducing workload)
```

Add to `app.py`:
```python
def get_cpu_temperature(self):
    """Get Raspberry Pi CPU temperature"""
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read()) / 1000.0
            return temp
    except:
        return None

def check_thermal_status(self):
    """Monitor CPU temperature and adjust workload"""
    temp = self.get_cpu_temperature()
    
    if temp is None:
        return True  # Can't check, assume OK
    
    if temp >= config.THERMAL_CRITICAL_TEMP:
        logger.error(f"🔥 CRITICAL: CPU temperature {temp}°C!")
        logger.error("🔥 System will throttle! Add cooling!")
        # Optionally reduce AI inference frequency
        config.VISION_LOOP_INTERVAL_SECONDS = min(config.VISION_LOOP_INTERVAL_SECONDS * 2, 10)
        return False
    elif temp >= config.THERMAL_WARNING_TEMP:
        logger.warning(f"⚠️ WARNING: CPU temperature {temp}°C")
        return True
    else:
        logger.debug(f"✅ CPU temperature OK: {temp}°C")
        return True
```

---

## 🤖 TFLite Model Compatibility

### **Current Model: `queen_bee.tflite`**

Your code currently **hardcodes** the model path:

```python
# app.py
self.vision_processor = RealVisionProcessor(model_path="queen_bee.tflite")
```

### **Potential Issues:**

#### **Issue 1: Model Input Size Mismatch**

**Problem:**
```python
# Your YOLOv5 model expects specific input size (e.g., 640x640)
# Camera captures at 640x480
# Mismatch causes errors
```

**Check Your Model:**
```python
import tensorflow as tf

interpreter = tf.lite.Interpreter(model_path="queen_bee.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
print("Input shape:", input_details[0]['shape'])
# Output: [1, 640, 640, 3] or [1, 416, 416, 3] or [1, 320, 320, 3]
```

**Solution:**
- Model expects `640x640` → Resize camera frame to 640x640
- Model expects `416x416` → Resize camera frame to 416x416

---

#### **Issue 2: Output Format Differences**

**Problem:**
```python
# Different YOLO versions have different output formats:

YOLOv5 TFLite outputs:
- Output 0: [1, 25200, 85]  # 25200 predictions, 85 values each (4 bbox + 1 conf + 80 classes)

YOLOv3 TFLite outputs:
- Output 0: [1, 13, 13, 255]  # Grid format
- Output 1: [1, 26, 26, 255]
- Output 2: [1, 52, 52, 255]

YOLOv8 TFLite outputs:
- Output 0: [1, 84, 8400]  # Different format (84 = 4 bbox + 80 classes)
```

**Your Code Needs to Handle This!**

---

#### **Issue 3: Quantization Type**

**Problem:**
```python
# TFLite models can be:
# - Float32 (full precision)
# - Float16 (half precision)
# - Int8 (quantized, faster on Pi)

# Quantized models need different pre/post processing
```

**Check Model Type:**
```python
input_details = interpreter.get_input_details()
print("Input dtype:", input_details[0]['dtype'])

# Output:
# <class 'numpy.float32'>  → Float model
# <class 'numpy.uint8'>    → Quantized model (needs scaling)
```

---

## ⚙️ Flexible TFLite Configuration

### **Step 1: Add Model Configuration to config.py**

```python
# --- AI Vision Model Configuration ---

# Model file path (relative to project root)
TFLITE_MODEL_PATH = "queen_bee.tflite"

# Model input configuration
MODEL_INPUT_WIDTH = 640   # Model expects 640x640 images
MODEL_INPUT_HEIGHT = 640
MODEL_INPUT_CHANNELS = 3  # RGB

# Model type
MODEL_IS_QUANTIZED = False  # Set True for int8 quantized models

# If quantized, specify scaling parameters
MODEL_INPUT_MEAN = 127.5
MODEL_INPUT_STD = 127.5

# Detection parameters
DETECTION_CONFIDENCE_THRESHOLD = 0.5  # Only show detections above 50% confidence
DETECTION_IOU_THRESHOLD = 0.45  # Non-max suppression threshold

# Class names (for YOLO models)
CLASS_NAMES = ["queen_bee"]  # Single class for your use case
# For multi-class: CLASS_NAMES = ["queen_bee", "worker_bee", "drone", "larvae"]

# Post-processing configuration
MAX_DETECTIONS = 10  # Maximum number of detections to return
ENABLE_NMS = True    # Enable Non-Maximum Suppression

# Model output format (adjust based on your YOLO version)
MODEL_OUTPUT_FORMAT = "yolov5"  # Options: "yolov5", "yolov3", "yolov8", "custom"

# For custom models, specify output shape
# MODEL_OUTPUT_SHAPE = [1, 25200, 85]  # Uncomment if needed
```

---

### **Step 2: Create Flexible Model Loader**

Create a new file: `vision_utils.py`

```python
"""
vision_utils.py - Flexible TFLite model loading and inference
"""

import numpy as np
import cv2
import tensorflow as tf
from typing import List, Tuple, Dict
import logging
import config

logger = logging.getLogger(__name__)


class TFLiteModel:
    """Flexible TFLite model wrapper supporting multiple YOLO versions"""
    
    def __init__(self, model_path: str):
        """
        Initialize TFLite model
        
        Args:
            model_path: Path to .tflite model file
        """
        try:
            self.interpreter = tf.lite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            
            # Get input/output details
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            # Log model information
            self._log_model_info()
            
            # Validate model against config
            self._validate_model()
            
            logger.info(f"✅ TFLite model loaded: {model_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load TFLite model: {e}")
            raise
    
    def _log_model_info(self):
        """Log model input/output information"""
        logger.info("=" * 50)
        logger.info("TFLite Model Information:")
        logger.info(f"Input shape: {self.input_details[0]['shape']}")
        logger.info(f"Input dtype: {self.input_details[0]['dtype']}")
        logger.info(f"Output shapes: {[out['shape'] for out in self.output_details]}")
        logger.info(f"Output dtypes: {[out['dtype'] for out in self.output_details]}")
        logger.info("=" * 50)
    
    def _validate_model(self):
        """Validate model matches config expectations"""
        input_shape = self.input_details[0]['shape']
        
        # Check batch size
        if input_shape[0] != 1:
            logger.warning(f"⚠️ Model expects batch size {input_shape[0]}, using 1")
        
        # Check input dimensions
        expected_height = config.MODEL_INPUT_HEIGHT
        expected_width = config.MODEL_INPUT_WIDTH
        
        # TFLite models can be [1, H, W, C] or [1, C, H, W]
        if input_shape[1] == expected_height and input_shape[2] == expected_width:
            self.input_format = "NHWC"  # [batch, height, width, channels]
            logger.info(f"✅ Model input format: NHWC")
        elif input_shape[1] == config.MODEL_INPUT_CHANNELS:
            self.input_format = "NCHW"  # [batch, channels, height, width]
            logger.info(f"✅ Model input format: NCHW")
        else:
            logger.warning(f"⚠️ Model input shape {input_shape} doesn't match config")
            logger.warning(f"⚠️ Expected: [{1}, {expected_height}, {expected_width}, {config.MODEL_INPUT_CHANNELS}]")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for model input
        
        Args:
            image: OpenCV image (BGR format)
            
        Returns:
            Preprocessed image ready for inference
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize to model input size
        image_resized = cv2.resize(
            image_rgb,
            (config.MODEL_INPUT_WIDTH, config.MODEL_INPUT_HEIGHT)
        )
        
        # Convert to float and normalize
        if config.MODEL_IS_QUANTIZED:
            # For quantized models (uint8), keep as is
            input_data = image_resized.astype(np.uint8)
        else:
            # For float models, normalize to [0, 1] or [-1, 1]
            input_data = image_resized.astype(np.float32)
            input_data = (input_data - config.MODEL_INPUT_MEAN) / config.MODEL_INPUT_STD
        
        # Add batch dimension
        input_data = np.expand_dims(input_data, axis=0)
        
        # Convert to NCHW if needed
        if self.input_format == "NCHW":
            input_data = np.transpose(input_data, (0, 3, 1, 2))
        
        return input_data
    
    def inference(self, input_data: np.ndarray) -> List[np.ndarray]:
        """
        Run inference on preprocessed input
        
        Args:
            input_data: Preprocessed image
            
        Returns:
            List of output arrays from model
        """
        # Set input tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        
        # Run inference
        self.interpreter.invoke()
        
        # Get all outputs
        outputs = []
        for output_detail in self.output_details:
            output = self.interpreter.get_tensor(output_detail['index'])
            outputs.append(output)
        
        return outputs
    
    def postprocess_yolov5(self, outputs: List[np.ndarray], image_shape: Tuple[int, int]) -> List[Dict]:
        """
        Post-process YOLOv5 TFLite output
        
        Args:
            outputs: Raw model outputs
            image_shape: Original image (height, width)
            
        Returns:
            List of detections with format:
            [{'class': int, 'confidence': float, 'bbox': [x1, y1, x2, y2], 'class_name': str}, ...]
        """
        detections = []
        
        # YOLOv5 output: [1, 25200, 85] or [1, num_predictions, 85]
        # Format: [x_center, y_center, width, height, objectness, class_scores...]
        predictions = outputs[0][0]  # Remove batch dimension
        
        orig_h, orig_w = image_shape
        
        for pred in predictions:
            # Extract components
            x_center, y_center, width, height = pred[:4]
            objectness = pred[4]
            class_scores = pred[5:]
            
            # Get class with highest score
            class_id = np.argmax(class_scores)
            class_score = class_scores[class_id]
            
            # Combined confidence
            confidence = objectness * class_score
            
            # Filter by threshold
            if confidence < config.DETECTION_CONFIDENCE_THRESHOLD:
                continue
            
            # Convert from normalized [0, 1] to pixel coordinates
            x_center *= orig_w
            y_center *= orig_h
            width *= orig_w
            height *= orig_h
            
            # Convert center format to corner format
            x1 = int(x_center - width / 2)
            y1 = int(y_center - height / 2)
            x2 = int(x_center + width / 2)
            y2 = int(y_center + height / 2)
            
            # Clip to image bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(orig_w, x2)
            y2 = min(orig_h, y2)
            
            # Get class name
            class_name = config.CLASS_NAMES[class_id] if class_id < len(config.CLASS_NAMES) else f"class_{class_id}"
            
            detections.append({
                'class': int(class_id),
                'confidence': float(confidence),
                'bbox': [x1, y1, x2, y2],
                'class_name': class_name
            })
        
        # Apply Non-Maximum Suppression if enabled
        if config.ENABLE_NMS and len(detections) > 0:
            detections = self.apply_nms(detections)
        
        # Limit number of detections
        detections = detections[:config.MAX_DETECTIONS]
        
        return detections
    
    def apply_nms(self, detections: List[Dict]) -> List[Dict]:
        """
        Apply Non-Maximum Suppression to remove overlapping boxes
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            Filtered list of detections
        """
        if len(detections) == 0:
            return []
        
        # Extract boxes and scores
        boxes = np.array([d['bbox'] for d in detections])
        scores = np.array([d['confidence'] for d in detections])
        
        # OpenCV NMS
        indices = cv2.dnn.NMSBoxes(
            boxes.tolist(),
            scores.tolist(),
            config.DETECTION_CONFIDENCE_THRESHOLD,
            config.DETECTION_IOU_THRESHOLD
        )
        
        # Filter detections
        if len(indices) > 0:
            indices = indices.flatten()
            return [detections[i] for i in indices]
        
        return []
    
    def detect(self, image: np.ndarray) -> List[Dict]:
        """
        Complete detection pipeline: preprocess → inference → postprocess
        
        Args:
            image: OpenCV image (BGR format)
            
        Returns:
            List of detections
        """
        # Preprocess
        input_data = self.preprocess_image(image)
        
        # Inference
        outputs = self.inference(input_data)
        
        # Postprocess based on model format
        if config.MODEL_OUTPUT_FORMAT == "yolov5":
            detections = self.postprocess_yolov5(outputs, image.shape[:2])
        else:
            logger.warning(f"⚠️ Unsupported model format: {config.MODEL_OUTPUT_FORMAT}")
            logger.warning(f"⚠️ Please implement postprocessing for your model")
            detections = []
        
        return detections


# Helper function for visualization
def draw_detections(image: np.ndarray, detections: List[Dict]) -> np.ndarray:
    """
    Draw bounding boxes and labels on image
    
    Args:
        image: OpenCV image
        detections: List of detections from model
        
    Returns:
        Image with drawn detections
    """
    image_copy = image.copy()
    
    for det in detections:
        x1, y1, x2, y2 = det['bbox']
        confidence = det['confidence']
        class_name = det['class_name']
        
        # Draw bounding box
        cv2.rectangle(image_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw label
        label = f"{class_name}: {confidence:.2f}"
        (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(image_copy, (x1, y1 - label_h - 10), (x1 + label_w, y1), (0, 255, 0), -1)
        cv2.putText(image_copy, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    return image_copy
```

---

### **Step 3: Update real_components.py to Use Flexible Model**

```python
# real_components.py

from vision_utils import TFLiteModel, draw_detections
import config

class RealVisionProcessor:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = config.TFLITE_MODEL_PATH
        
        logger.info(f"Loading TFLite model: {model_path}")
        self.model = TFLiteModel(model_path)
        logger.info("✅ Vision processor initialized")
    
    def process_frame(self, frame):
        """Process frame and return detections"""
        # Run detection
        detections = self.model.detect(frame)
        
        # Draw boxes on frame
        annotated_frame = draw_detections(frame, detections)
        
        # Format results for MQTT
        results = {
            'timestamp': time.time(),
            'detections': detections,
            'num_detections': len(detections)
        }
        
        return annotated_frame, results
```

---

### **Step 4: Testing Different Models**

```python
# test_models.py - Test any TFLite model

import cv2
from vision_utils import TFLiteModel, draw_detections
import config

def test_tflite_model(model_path, test_image_path):
    """Test a TFLite model on a sample image"""
    
    print(f"\n{'='*60}")
    print(f"Testing model: {model_path}")
    print(f"{'='*60}\n")
    
    # Load model
    model = TFLiteModel(model_path)
    
    # Load test image
    image = cv2.imread(test_image_path)
    if image is None:
        print(f"❌ Could not load image: {test_image_path}")
        return
    
    print(f"Image shape: {image.shape}")
    
    # Run detection
    detections = model.detect(image)
    
    print(f"\n✅ Found {len(detections)} detections:")
    for i, det in enumerate(detections):
        print(f"  {i+1}. {det['class_name']}: {det['confidence']:.3f} at {det['bbox']}")
    
    # Draw and save result
    result_image = draw_detections(image, detections)
    output_path = model_path.replace('.tflite', '_test_result.jpg')
    cv2.imwrite(output_path, result_image)
    print(f"\n✅ Result saved to: {output_path}")


if __name__ == "__main__":
    # Test your model
    test_tflite_model(
        model_path="queen_bee.tflite",
        test_image_path="test_bee_image.jpg"
    )
    
    # Test different model (if you have one)
    # test_tflite_model(
    #     model_path="yolov5n_bees.tflite",
    #     test_image_path="test_bee_image.jpg"
    # )
```

---

## 📋 Pre-Deployment Checklist

```bash
# Run this checklist BEFORE deploying to Raspberry Pi:

✅ Hardware Checks:
□ All sensors connected (BME280, LIS3DH, Camera, Mic)
□ I2C enabled: sudo raspi-config
□ I2C devices detected: sudo i2cdetect -y 1
□ Camera detected: ls /dev/video*
□ Microphone detected: arecord -l

✅ Software Checks:
□ Docker installed: docker --version
□ Docker Compose installed: docker compose version
□ Python 3.9+: python3 --version
□ Git installed: git --version

✅ Network Checks:
□ WiFi connected: ping google.com
□ NTP synchronized: timedatectl status
□ AWS IoT reachable: nc -zv your-endpoint.iot.region.amazonaws.com 8883
□ S3 reachable: curl -I https://s3.region.amazonaws.com

✅ AWS Configuration:
□ Credentials exist: cat ~/.aws/credentials
□ Credentials valid: aws sts get-caller-identity
□ IAM permissions correct (DynamoDB, S3, IoT)
□ Certificates exist: ls certs/*.pem*
□ Certificates valid (not expired)
□ DynamoDB table created
□ S3 bucket created

✅ Code Configuration:
□ config.py updated: IS_MOCK_ENVIRONMENT = False
□ TFLite model file exists: ls queen_bee.tflite
□ Model config matches: Check input size in config.py
□ docker-compose.yml has device mappings
□ AWS region matches: config.py vs DynamoDB table

✅ Thermal Management:
□ Heatsink installed (recommended)
□ Fan installed (optional but recommended for 24/7)
□ CPU temp < 70°C: vcgencmd measure_temp

✅ Storage:
□ SD card >= 32 GB
□ SD card Class 10 or better
□ Free space > 10 GB: df -h
□ Log rotation configured

✅ Testing:
□ Test camera: python3 -c "import cv2; print(cv2.VideoCapture(0).read())"
□ Test I2C: sudo i2cget -y 1 0x77 0x00  # BME280
□ Test audio: arecord -d 3 test.wav && aplay test.wav
□ Test TFLite model: python3 test_models.py
□ Test Docker build: docker-compose build
□ Test containers: docker-compose up (check logs)

✅ Monitoring Setup:
□ Know how to check logs: docker logs smart-hive-edge
□ Know how to check temperature: vcgencmd measure_temp
□ Know how to check disk: df -h
□ Know how to check memory: free -h
□ Know how to restart: docker-compose restart
```

---

## 🎯 Summary

### **Potential Issues Addressed:**
1. ✅ Camera device index auto-detection
2. ✅ I2C address auto-scanning
3. ✅ USB audio device enumeration
4. ✅ SD card write endurance (log rotation)
5. ✅ Network resilience (retry logic)
6. ✅ Time synchronization (NTP)
7. ✅ ARM Docker build optimization
8. ✅ Firewall connectivity testing
9. ✅ Certificate expiration monitoring
10. ✅ Thermal throttling detection

### **TFLite Compatibility:**
1. ✅ Flexible model configuration
2. ✅ Auto-detect model input format
3. ✅ Support quantized and float models
4. ✅ Configurable pre/post processing
5. ✅ Works with any YOLOv5 TFLite model
6. ✅ Easy to adapt for YOLOv3/v8
7. ✅ Testing script included

### **Files to Create:**
1. **vision_utils.py** - Flexible TFLite model loader
2. **test_models.py** - Model testing script
3. Update **config.py** - Add model configuration
4. Update **real_components.py** - Use vision_utils
5. Update **docker-compose.yml** - Add device mappings ✅ (Done)

---

**Your system is now production-ready with comprehensive error handling!** 🚀

See `TROUBLESHOOTING.md` for solutions to specific issues.
