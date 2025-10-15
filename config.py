# config.py

import os
from dotenv import load_dotenv

load_dotenv() # Loads variables from .env file

# --- AWS IoT Core Settings ---
AWS_ENDPOINT = os.getenv("AWS_ENDPOINT")
THING_NAME = "SmartHive_Pi"

# --- Certificate Paths ---
CERT_FILE_NAME = os.getenv("CERT_FILE_NAME")
KEY_FILE_NAME = os.getenv("KEY_FILE_NAME")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CA_PATH = os.path.join(BASE_DIR, "certs", "AmazonRootCA1.pem")
CERT_PATH = os.path.join(BASE_DIR, "certs", CERT_FILE_NAME)
KEY_PATH = os.path.join(BASE_DIR, "certs", KEY_FILE_NAME)

# --- Flask Secret Key ---
SECRET_KEY = os.getenv("SECRET_KEY")

# --- MQTT Topics ---
TOPIC_TELEMETRY = "hive/telemetry"
TOPIC_VISION = "hive/vision"
TOPIC_CONTROL = "hive/control"

# --- AWS S3 Settings ---
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
ENABLE_S3 = os.getenv("ENABLE_S3", "false").lower() == "true"  # Set to "true" in .env to enable S3 uploads

# -----------------------------------------------------------------------------
# --- Task Loop Intervals (in seconds) ---
# -----------------------------------------------------------------------------
# How often to read and publish sensor telemetry data
TELEMETRY_INTERVAL_SECONDS = 60

# --- AI Vision Detection Settings ---
# AI detection mode: "continuous" or "interval"
# - "continuous": Runs AI on video frames continuously (real-time detection)
# - "interval": Runs AI only at specified intervals (legacy mode)
VISION_DETECTION_MODE = "continuous"  # Recommended: "continuous"

# How often AI processes frames (only used in "continuous" mode)
# Process every Nth frame to balance CPU usage vs detection speed
# Examples: 1 = every frame (fastest), 2 = every other frame, 3 = every 3rd frame
VISION_PROCESS_EVERY_N_FRAMES = 3  # Process every 3rd frame (6-7 FPS detection)

# Cooldown period after queen detection (seconds)
# Prevents spam notifications for the same queen
VISION_DETECTION_COOLDOWN_SECONDS = 3600  # 1 hour cooldown

# Minimum confidence threshold for queen detection (0.0 - 1.0)
VISION_CONFIDENCE_THRESHOLD = 0.5  # 50% confidence required

# Legacy interval mode setting (only used if VISION_DETECTION_MODE = "interval")
VISION_LOOP_INTERVAL_SECONDS = 3600  # Every 1 hour (legacy mode)

# How often to upload a general snapshot to S3
S3_SNAPSHOT_INTERVAL_SECONDS = 3600

# Video stream frame rate (frames per second for live feed)
# Lower values save CPU/bandwidth, higher values = smoother video
VIDEO_STREAM_FPS = 20  # 20 FPS = 0.05s delay between frames

# -----------------------------------------------------------------------------
# --- Hardware Pin Configuration (SunFounder Raspberry Pi Sensor Kit) ---
# -----------------------------------------------------------------------------
# I2C Bus Configuration
I2C_BUS = 1  # Default I2C bus on Raspberry Pi (GPIO pins: SCL=Pin 5, SDA=Pin 3)

# BME280 Temperature & Humidity Sensor I2C Address
# Common addresses: 0x77 (default) or 0x76
# To check your sensor's address, run: sudo i2cdetect -y 1
BME280_ADDRESS = 0x76

# LIS3DH Accelerometer/Vibration Sensor I2C Address
# Common addresses: 0x18 (default) or 0x19
# To check your sensor's address, run: sudo i2cdetect -y 1
LIS3DH_ADDRESS = 0x19

# Camera Configuration
# Options: "USB" for Logitech USB Camera, "PICAMERA" for Raspberry Pi Camera Module
CAMERA_TYPE = "USB"
CAMERA_DEVICE_INDEX = 0  # Usually 0 for the first USB camera
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Microphone Configuration
# For Samson USB Microphone or system default
MICROPHONE_SAMPLE_RATE = 44100  # Hz
MICROPHONE_DURATION_MS = 100     # Milliseconds for dB sampling
MICROPHONE_FREQ_DURATION_SEC = 1.0  # Seconds for frequency analysis (needs longer sample)


# --- Application Settings ---
# Set to False when deploying on the Raspberry Pi
IS_MOCK_ENVIRONMENT = False

# --- AWS DynamoDB Settings ---
DYNAMODB_TABLE = "SmartHiveTelemetry"
ENABLE_DYNAMODB = True  # Set to False to disable database logging
AWS_REGION = "ap-southeast-2"  # CHANGE THIS to match your DynamoDB table region