"""
Smart Hive AI - Configuration Module

Description:
    Central configuration management for the Smart Hive AI system.
    Loads environment variables and defines system-wide constants for AWS IoT Core,
    sensor polling intervals, AI detection settings, and feature flags.

Author: Smart Hive AI Team
Created: 2024
Last Modified: October 2025

Configuration Categories:
    - AWS IoT Core: MQTT endpoint, certificates, thing name
    - AWS Services: DynamoDB, S3 bucket settings
    - MQTT Topics: Telemetry, vision, control topics
    - Sensor Intervals: Telemetry collection frequency
    - AI Vision: Detection mode and processing frequency
    - Environment: Mock/real hardware toggle

Environment Variables Required:
    - AWS_ENDPOINT: AWS IoT Core endpoint URL
    - CERT_FILE_NAME: Client certificate filename
    - KEY_FILE_NAME: Private key filename
    - SECRET_KEY: Flask application secret key
    - S3_BUCKET_NAME: S3 bucket for image uploads (optional)
    - ENABLE_S3: Enable/disable S3 uploads (optional)

Usage:
    import config
    print(config.AWS_ENDPOINT)
    print(config.TELEMETRY_INTERVAL_SECONDS)
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -----------------------------------------------------------------------------
# AWS IoT Core Settings
# -----------------------------------------------------------------------------

# AWS IoT Core MQTT endpoint (loaded from environment)
AWS_ENDPOINT = os.getenv("AWS_ENDPOINT")

# AWS IoT Thing name (device identifier)
THING_NAME = "SmartHive_Pi"

# -----------------------------------------------------------------------------
# Certificate Paths
# -----------------------------------------------------------------------------

# Certificate filenames (loaded from environment)
CERT_FILE_NAME = os.getenv("CERT_FILE_NAME", "")
KEY_FILE_NAME = os.getenv("KEY_FILE_NAME", "")

# Construct absolute paths to certificate files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CA_PATH = os.path.join(BASE_DIR, "certs", "AmazonRootCA1.pem")

# Only construct cert/key paths if filenames are provided
if CERT_FILE_NAME:
    CERT_PATH = os.path.join(BASE_DIR, "certs", CERT_FILE_NAME)
else:
    CERT_PATH = None

if KEY_FILE_NAME:
    KEY_PATH = os.path.join(BASE_DIR, "certs", KEY_FILE_NAME)
else:
    KEY_PATH = None

# -----------------------------------------------------------------------------
# Flask Configuration
# -----------------------------------------------------------------------------

# Flask secret key for session management (loaded from environment)
SECRET_KEY = os.getenv("SECRET_KEY")

# -----------------------------------------------------------------------------
# MQTT Broker Configuration (Local or Remote)
# -----------------------------------------------------------------------------

# MQTT Broker hostname/IP address
# For Docker: "mosquitto" (service name in docker-compose)
# For local: "localhost" or "127.0.0.1"
# For remote: IP address or hostname
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")

# MQTT Broker port
# 1883 = standard unencrypted MQTT
# 8883 = TLS encrypted MQTT
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# MQTT Client ID (unique identifier)
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID", "SmartHive_Python")

# MQTT keepalive interval (seconds)
MQTT_KEEPALIVE = 60

# Enable TLS for MQTT connection (set False for local mosquitto)
MQTT_USE_TLS = os.getenv("MQTT_USE_TLS", "false").lower() == "true"

# MQTT username (if broker requires authentication)
MQTT_USERNAME = os.getenv("MQTT_USERNAME")

# MQTT password (if broker requires authentication)
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

# QoS level for MQTT messages (0, 1, or 2)
MQTT_QOS = 1

# Connection timeout (seconds)
MQTT_CONNECT_TIMEOUT = 10

# Add certificate paths for TLS (if using AWS IoT or TLS broker)
CA_CERT = os.path.join(BASE_DIR, "certs", "AmazonRootCA1.pem")
CERT_FILE = CERT_PATH  # Use AWS certificates if available
KEY_FILE = KEY_PATH     # Use AWS certificates if available

# -----------------------------------------------------------------------------
# MQTT Topics
# -----------------------------------------------------------------------------

# Topic for publishing sensor telemetry data
TOPIC_TELEMETRY = "hive/telemetry"

# Topic for publishing camera frames (Option A: Edge App → Vision Service)
# Edge-app publishes JPEG frames here, Vision service subscribes
TOPIC_CAMERA_FRAME = "hive/telemetry/camera/frame"

# Topic for publishing AI vision detection results (legacy edge-app built-in vision)
# Used by app.py when running vision locally on Pi (not microservice)
TOPIC_VISION = "hive/vision"

# Topic for receiving control commands (unified for sensors + ML services)
TOPIC_CONTROL = "hive/control"

# -----------------------------------------------------------------------------
# AWS S3 Settings
# -----------------------------------------------------------------------------

# S3 bucket name for image uploads (loaded from environment)
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# Feature flag to enable/disable S3 uploads
ENABLE_S3 = os.getenv("ENABLE_S3", "false").lower() == "true"

# -----------------------------------------------------------------------------
# Task Loop Intervals
# -----------------------------------------------------------------------------

# Telemetry collection interval in seconds
# Defines how often sensor data is read and published to MQTT
TELEMETRY_INTERVAL_SECONDS = 60

# -----------------------------------------------------------------------------
# AI Vision Detection Settings
# -----------------------------------------------------------------------------

# AI detection mode: "continuous" or "interval"
# - "continuous": Runs AI on video frames continuously (real-time detection)
# - "interval": Runs AI only at specified intervals (legacy mode)
VISION_DETECTION_MODE = "continuous"  # Recommended: "continuous"

# Frame processing frequency (only used in "continuous" mode)
# Process every Nth frame to balance CPU usage vs detection speed
# Examples: 1 = every frame (fastest), 2 = every other frame, 3 = every 3rd frame
VISION_PROCESS_EVERY_N_FRAMES = 3  # Process every 3rd frame (approximately 6-7 FPS)

# Cooldown period after queen detection in seconds
# Prevents duplicate detections and excessive alerts
VISION_DETECTION_COOLDOWN_SECONDS = 3600  # 1 hour cooldown

# Minimum confidence threshold for queen detection (0.0 - 1.0)
VISION_CONFIDENCE_THRESHOLD = 0.5  # 50% confidence required

# Legacy interval mode setting (only used if VISION_DETECTION_MODE = "interval")
VISION_LOOP_INTERVAL_SECONDS = 3600  # Every 1 hour (legacy mode)

# S3 snapshot upload interval in seconds
S3_SNAPSHOT_INTERVAL_SECONDS = 3600

# Video stream frame rate (frames per second for live feed)
# Lower values save CPU/bandwidth, higher values provide smoother video
VIDEO_STREAM_FPS = 20  # 20 FPS = 0.05s delay between frames

# -----------------------------------------------------------------------------
# Hardware Pin Configuration
# -----------------------------------------------------------------------------

# I2C Bus Configuration for Raspberry Pi
I2C_BUS = 1  # Default I2C bus on Raspberry Pi (GPIO pins: SCL=Pin 5, SDA=Pin 3)

# BME280 Temperature and Humidity Sensor I2C Address
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

# Camera Frame Publishing to MQTT (for Vision Service consumption)
# ─────────────────────────────────────────────────────────────
# JPEG quality for frame compression (1-100, higher = better quality)
CAMERA_FRAME_JPEG_QUALITY = 80

# Resize frames before publishing to reduce bandwidth
# 1.0 = full resolution (640x480)
# 0.5 = half resolution (320x240)
CAMERA_FRAME_RESIZE_SCALE = 0.5

# Frequency of frame publishing to MQTT (frames per second)
# Higher = more frequent updates, more bandwidth
# Recommended: 2-5 FPS for inference tasks
CAMERA_FRAME_PUBLISH_FPS = 3

# MQTT topic for camera frame stream
TOPIC_CAMERA_FRAME = "hive/telemetry/camera/frame"

# Enable/disable frame publishing to MQTT
ENABLE_CAMERA_FRAME_PUBLISHING = True

# Microphone Configuration
# For Samson USB Microphone or system default
MICROPHONE_SAMPLE_RATE = 44100  # Hz
MICROPHONE_DURATION_MS = 100     # Milliseconds for dB sampling
MICROPHONE_FREQ_DURATION_SEC = 1.0  # Seconds for frequency analysis (needs longer sample)

# -----------------------------------------------------------------------------
# Application Settings
# -----------------------------------------------------------------------------

# Environment mode toggle
# Set to False when deploying on the Raspberry Pi with real hardware
# Set to True for development/testing with mock sensors
IS_MOCK_ENVIRONMENT = False

# -----------------------------------------------------------------------------
# AWS DynamoDB Settings
# -----------------------------------------------------------------------------

# DynamoDB table name for telemetry storage
DYNAMODB_TABLE = "SmartHiveTelemetry"

# Feature flag to enable/disable DynamoDB writes
ENABLE_DYNAMODB = True

# AWS region where DynamoDB table is located
AWS_REGION = "ap-southeast-2"

# ─────────────────────────────────────────────────────────────────────────────
# ML MODELS CONFIGURATION (NEW)
# ─────────────────────────────────────────────────────────────────────────────
# Machine Learning models for vision and audio-based queen bee detection
# All settings can be tuned without modifying code

# VISION MODEL (YOLO Queen Bee Detection)
# ─────────────────────────────────────────
# Enable/disable vision model entirely
ENABLE_VISION_MODEL = True

# Path to YOLO model file (PyTorch format)
VISION_MODEL_PATH = "models/vision_model.pt"

# Minimum confidence threshold for detection (0.0-1.0)
# Higher = more conservative, fewer false positives
# Recommended: 0.6-0.8
VISION_CONFIDENCE_THRESHOLD = 0.7

# Process every N frames (balance accuracy vs CPU)
# 1 = every frame (most accurate, ~20 FPS)
# 3 = every 3rd frame (balanced, ~6-7 FPS)
# 5 = every 5th frame (fastest, ~4 FPS)
VISION_PROCESS_EVERY_N_FRAMES = 3

# Inference timeout (seconds) - kill if takes longer than this
VISION_FRAME_TIMEOUT_SEC = 5

# MQTT topic for vision results
TOPIC_VISION_RESULTS = "hive/vision/detection"

# AUDIO MODEL (ML-based Queen Bee Sound Classification)
# ─────────────────────────────────────────────────────
# Enable/disable audio model entirely
ENABLE_AUDIO_MODEL = True

# Path to pre-trained audio classification model
# Audio model path (scikit-learn classifier, pre-trained)
# Located in ml_audio_model directory
AUDIO_MODEL_PATH = "models/audio_model.pkl"

# Audio sampling rate in Hz (must match model training)
AUDIO_SAMPLE_RATE = 22050

# Default recording duration in seconds (can be overridden per recording)
AUDIO_RECORD_DURATION_SEC = 30

# Minimum confidence for classification (0.0-1.0)
# Higher = more confident predictions
AUDIO_CONFIDENCE_THRESHOLD = 0.6

# Save audio recordings to disk
AUDIO_SAVE_RECORDINGS = False

# Directory to save audio files if enabled
AUDIO_RECORDINGS_DIR = "audio_recordings"

# MQTT topic for audio results
TOPIC_AUDIO_RESULTS = "hive/audio/classification"

# -
# WINDOWED INFERENCE SETTINGS (MUST MATCH TRAINING)
# 
# Window size in seconds for sliding window inference
AUDIO_WINDOW_SECONDS = 1.0

# Hop size in seconds (overlap between windows)
AUDIO_HOP_SECONDS = 0.5

# Aggregation method for combining per-window predictions
AUDIO_AGGREGATION_METHOD = 'max_proba'

