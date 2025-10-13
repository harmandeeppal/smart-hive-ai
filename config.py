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

# -----------------------------------------------------------------------------
# --- Task Loop Intervals (in seconds) ---
# -----------------------------------------------------------------------------
# How often to read and publish sensor telemetry data
TELEMETRY_INTERVAL_SECONDS = 5
# How often to run the AI vision processing loop
VISION_LOOP_INTERVAL_SECONDS = 1
# How often to upload a general snapshot to S3
S3_SNAPSHOT_INTERVAL_SECONDS = 300 # 5 minutes


# --- Application Settings ---
# Set to False when deploying on the Raspberry Pi
IS_MOCK_ENVIRONMENT = True