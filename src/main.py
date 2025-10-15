"""
Smart Hive AI - Main Application Module.

This module provides the core system orchestration for the Smart Hive AI monitoring system.
It integrates environmental sensors, computer vision, sound analysis, and AWS cloud services
to enable real-time honeybee colony health monitoring with AI-powered queen detection.

Classes:
    SmartHiveSystem: Main system orchestrator handling all sensors and cloud integration

Functions:
    main: Entry point for the application

Author:
    Harmandeep Pal
    Auckland University of Technology

Created:
    October 2025

License:
    MIT License

Copyright:
    (c) 2025 Harmandeep Pal. All rights reserved.
"""

import time
import json
import ssl
import threading
import logging
from typing import Dict, Optional, Tuple, Any
import cv2
import numpy as np
from flask import Flask, Response
import paho.mqtt.client as mqtt
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal
from datetime import datetime

# Local imports
import config

# Conditional sensor imports based on environment
if config.IS_MOCK_ENVIRONMENT:
    from mock_components import (MockBME280, MockLIS3DH, 
                                  MockINMP441, MockVisionProcessor)
else:
    from real_components import (RealBME280, RealLIS3DH, 
                                  RealVisionProcessor, RealINMP441)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SmartHiveSystem:
    """
    Main orchestrator for the Smart Hive AI monitoring system.
    
    This class manages the complete lifecycle of the monitoring system including:
    - Hardware sensor initialization and data collection
    - AWS IoT Core MQTT communication
    - DynamoDB telemetry persistence
    - S3 snapshot uploads
    - Real-time video streaming with AI overlays
    - Queen bee detection using TensorFlow Lite
    
    Attributes:
        is_running: System operational state
        temp_humidity_sensor: BME280 temperature/humidity sensor instance
        vibration_sensor: LIS3DH accelerometer instance
        sound_sensor: INMP441 microphone instance
        vision_processor: Computer vision processor with queen detection
        mqtt_client: AWS IoT Core MQTT client
        s3_client: AWS S3 client for snapshot uploads
        dynamodb: AWS DynamoDB resource
        table: DynamoDB table reference for telemetry storage
        sensor_events: Threading events for sensor enable/disable control
        flask_app: Flask application for video streaming
    
    Example:
        >>> system = SmartHiveSystem()
        >>> if system.is_running:
        ...     system.run()
    """
    
    def __init__(self):
        """Initialize the Smart Hive system with all components and AWS services."""
        logger.info("Initializing Smart Hive System...")
        self.is_running = True
        
        # Initialize hardware components
        try:
            self.initialize_components()
        except Exception as e:
            logger.critical(f"Failed to initialize hardware components: {e}", 
                          exc_info=True)
            self.is_running = False
            return
        
        # Initialize AWS cloud services
        try:
            self.initialize_aws_clients()
        except Exception as e:
            logger.critical(f"Failed to initialize AWS clients: {e}", 
                          exc_info=True)
            self.is_running = False
            return

        # Initialize sensor control events
        self.sensor_events = {
            "temperature": threading.Event(),
            "humidity": threading.Event(),
            "vibration": threading.Event(),
            "sound": threading.Event(),
            "vision": threading.Event()
        }
        
        # Enable all sensors by default
        for event in self.sensor_events.values():
            event.set()

        # Initialize Flask video streaming server
        self.flask_app = Flask(__name__)
        self.setup_routes()
        
        logger.info("Smart Hive System initialized successfully")

    def initialize_components(self) -> None:
        """
        Initialize all hardware sensors or mock components.
        
        Initializes BME280, LIS3DH, INMP441, and vision processor based on
        the IS_MOCK_ENVIRONMENT configuration flag. In mock mode, simulated
        sensors are used. In production mode, real hardware is accessed.
        
        Raises:
            RuntimeError: If critical components (vision processor) fail to initialize
            
        Note:
            Individual sensor failures are logged but don't stop initialization.
            Vision processor failure is critical and will raise an exception.
        """
        if config.IS_MOCK_ENVIRONMENT:
            logger.info("Initializing MOCK environment components")
            self.temp_humidity_sensor = MockBME280()
            self.vibration_sensor = MockLIS3DH()
            self.sound_sensor = MockINMP441()
            self.vision_processor = MockVisionProcessor(
                model_path="queen_bee.tflite"
            )
        else:
            logger.info("Initializing REAL hardware components")
            
            # BME280 Temperature/Humidity Sensor
            try:
                self.temp_humidity_sensor = RealBME280()
                logger.info("BME280 Temperature/Humidity sensor initialized")
            except Exception as e:
                logger.warning(f"BME280 initialization failed: {e}")
                self.temp_humidity_sensor = None
            
            # LIS3DH Vibration Sensor
            try:
                self.vibration_sensor = RealLIS3DH()
                logger.info("LIS3DH Vibration sensor initialized")
            except Exception as e:
                logger.warning(f"LIS3DH initialization failed: {e}")
                self.vibration_sensor = None
            
            # INMP441 Sound Sensor
            try:
                self.sound_sensor = RealINMP441()
                logger.info("INMP441 Sound sensor initialized")
            except Exception as e:
                logger.warning(f"INMP441 initialization failed: {e}")
                self.sound_sensor = None
            
            # Vision Processor (Critical Component)
            try:
                self.vision_processor = RealVisionProcessor(
                    model_path="queen_bee.tflite"
                )
                logger.info("Vision Processor initialized")
            except Exception as e:
                logger.error(f"Vision Processor initialization failed: {e}", 
                           exc_info=True)
                raise RuntimeError("Vision Processor is required but failed to initialize")

    def initialize_aws_clients(self) -> None:
        """
        Initialize AWS service clients (IoT Core, S3, DynamoDB).
        
        Establishes connections to:
        - AWS IoT Core (MQTT over TLS)
        - S3 (snapshot uploads, if enabled)
        - DynamoDB (telemetry storage, if enabled)
        
        Raises:
            ConnectionError: If AWS IoT Core connection fails
            
        Note:
            S3 and DynamoDB failures are logged but don't prevent initialization.
        """
        # AWS IoT Core MQTT Client
        self.mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id=config.THING_NAME
        )
        
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_control_message

        # Configure TLS for AWS IoT Core
        self.mqtt_client.tls_set(
            ca_certs=config.CA_PATH,
            certfile=config.CERT_PATH,
            keyfile=config.KEY_PATH,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS
        )
        
        try:
            self.mqtt_client.connect(config.AWS_ENDPOINT, 8883, 60)
            self.mqtt_client.loop_start()
            logger.info("AWS IoT Core MQTT client connected")
        except Exception as e:
            logger.error(f"Failed to connect to AWS IoT Core: {e}")
            self.is_running = False
            raise ConnectionError("AWS IoT Core connection failed")

        # S3 Client (Optional)
        if config.ENABLE_S3 and not config.IS_MOCK_ENVIRONMENT:
            try:
                self.s3_client = boto3.client('s3')
                self.s3_client.head_bucket(Bucket=config.S3_BUCKET_NAME)
                logger.info(f"S3 bucket '{config.S3_BUCKET_NAME}' connected")
            except Exception as e:
                logger.warning(f"S3 bucket error: {e}. S3 uploads disabled.")
                self.s3_client = None
        else:
            self.s3_client = None
            if not config.ENABLE_S3:
                logger.info("S3 disabled by configuration")

        # DynamoDB Client (Optional)
        if config.ENABLE_DYNAMODB:
            try:
                self.dynamodb = boto3.resource('dynamodb', 
                                              region_name=config.AWS_REGION)
                self.table = self.dynamodb.Table(config.DYNAMODB_TABLE)
                logger.info(f"DynamoDB table '{config.DYNAMODB_TABLE}' initialized")
            except Exception as e:
                logger.error(f"DynamoDB initialization error: {e}")
                self.table = None
        else:
            self.table = None
            logger.info("DynamoDB disabled by configuration")

    def on_mqtt_connect(self, client: mqtt.Client, userdata: Any, 
                        flags: Dict, rc: int) -> None:
        """
        Callback handler for MQTT connection events.
        
        Args:
            client: MQTT client instance
            userdata: User-defined data passed to callbacks
            flags: Response flags from the broker
            rc: Connection result code
            
        Note:
            Automatically subscribes to control topic upon successful connection.
        """
        if rc == 0:
            logger.info("Successfully connected to AWS IoT Core")
            client.subscribe(config.TOPIC_CONTROL)
            logger.info(f"Subscribed to control topic: {config.TOPIC_CONTROL}")
        else:
            logger.error(f"Failed to connect to AWS IoT Core, return code {rc}")

    def on_control_message(self, client: mqtt.Client, userdata: Any, 
                           msg: mqtt.MQTTMessage) -> None:
        """
        Callback handler for control messages from dashboard.
        
        Processes sensor enable/disable commands received via MQTT.
        
        Args:
            client: MQTT client instance
            userdata: User-defined data passed to callbacks
            msg: MQTT message containing control command
            
        Message Format:
            {
                "sensor": "temperature|humidity|vibration|sound|vision",
                "state": "on|off"
            }
        """
        try:
            payload = json.loads(msg.payload.decode())
            sensor = payload.get("sensor")
            state = payload.get("state")

            if sensor in self.sensor_events:
                if state == "on":
                    self.sensor_events[sensor].set()
                    logger.info(f"Resumed sensor: {sensor}")
                elif state == "off":
                    self.sensor_events[sensor].clear()
                    logger.info(f"Paused sensor: {sensor}")
                else:
                    logger.warning(f"Invalid state '{state}' for sensor '{sensor}'")
            else:
                logger.warning(f"Unknown sensor in control message: {sensor}")
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from control topic: {msg.payload}")
        except Exception as e:
            logger.error(f"Error in on_control_message: {e}", exc_info=True)

    def setup_routes(self) -> None:
        """Configure Flask routes for video streaming endpoint."""
        @self.flask_app.route('/video_feed')
        def video_feed():
            """
            Video streaming route returning MJPEG stream.
            
            Returns:
                Flask Response with multipart MJPEG stream
            """
            return Response(
                self.generate_video_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )

    def generate_video_frames(self):
        """
        Generator function yielding JPEG-encoded video frames.
        
        Captures frames from the vision processor and yields them in MJPEG format
        for live streaming. Includes AI detection overlays when available.
        
        Yields:
            bytes: JPEG-encoded frame in multipart format
            
        Note:
            Frame rate is controlled by VIDEO_STREAM_FPS configuration parameter.
        """
        frame_delay = 1.0 / config.VIDEO_STREAM_FPS
        
        while self.is_running:
            if (self.vision_processor.camera and 
                self.vision_processor.camera.isOpened()):
                ret, frame = self.vision_processor.camera.read()
                
                if ret and frame is not None:
                    # Use annotated frame if available, otherwise raw frame
                    display_frame = (self.vision_processor.frame 
                                   if self.vision_processor.frame is not None 
                                   else frame)
                    
                    ret, buffer = cv2.imencode('.jpg', display_frame)
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' 
                               + frame_bytes + b'\r\n')
            
            time.sleep(frame_delay)

    def start_video_server(self) -> None:
        """Start Flask video streaming server in background thread."""
        logger.info("Starting video streaming server on port 5001")
        self.flask_app.run(host='0.0.0.0', port=5001, debug=False)

    def write_to_dynamodb(self, telemetry_data: Dict[str, Any]) -> None:
        """
        Write telemetry data to AWS DynamoDB table.
        
        Stores sensor readings with timestamp in DynamoDB for historical analysis.
        Automatically converts floats to Decimal for DynamoDB compatibility and
        adds New Zealand timezone timestamp for human readability.
        
        Args:
            telemetry_data: Dictionary containing sensor readings and timestamp
            
        Data Format:
            {
                'timestamp': 1697123456,
                'temperature': 34.5,
                'humidity': 58.2,
                'vibration_rms': 0.0521,
                'sound_db': 52.3,
                'sound_freq': 265.0
            }
            
        Note:
            Failures are logged but don't crash the system.
        """
        if not self.table:
            return
        
        try:
            # Prepare DynamoDB item
            item = {
                'device_id': config.THING_NAME,
                'timestamp': int(telemetry_data.get('timestamp', time.time()))
            }
            
            # Add human-readable NZ timestamp
            try:
                from zoneinfo import ZoneInfo
                nz_time = datetime.fromtimestamp(
                    item['timestamp'], 
                    tz=ZoneInfo('Pacific/Auckland')
                )
            except (ImportError, Exception):
                # Fallback to pytz for compatibility
                import pytz
                nz_tz = pytz.timezone('Pacific/Auckland')
                utc_time = datetime.utcfromtimestamp(item['timestamp']).replace(
                    tzinfo=pytz.UTC
                )
                nz_time = utc_time.astimezone(nz_tz)
            
            item['timestamp_nz'] = nz_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            
            # Add sensor readings (convert float to Decimal)
            if 'temperature' in telemetry_data:
                item['temperature'] = Decimal(str(round(
                    float(telemetry_data['temperature']), 2)))
            
            if 'humidity' in telemetry_data:
                item['humidity'] = Decimal(str(round(
                    float(telemetry_data['humidity']), 2)))
            
            if 'vibration_rms' in telemetry_data:
                item['vibration_rms'] = Decimal(str(round(
                    float(telemetry_data['vibration_rms']), 4)))
            
            if 'sound_db' in telemetry_data:
                item['sound_db'] = Decimal(str(round(
                    float(telemetry_data['sound_db']), 1)))
            
            if 'sound_freq' in telemetry_data:
                item['sound_freq'] = Decimal(str(round(
                    float(telemetry_data['sound_freq']), 1)))
            
            # Write to DynamoDB
            self.table.put_item(Item=item)
            
            readable_time = nz_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            logger.info(f"DynamoDB: Wrote record at {readable_time} "
                       f"({len(item)-3} sensors)")
            
        except Exception as e:
            logger.error(f"DynamoDB write error: {e}", exc_info=True)

    def upload_detection_snapshot(self, frame: np.ndarray, 
                                  confidence: float) -> None:
        """
        Upload queen detection snapshot to S3.
        
        Args:
            frame: Video frame containing detected queen
            confidence: Detection confidence score (0.0-1.0)
            
        Note:
            Skipped if S3 is disabled or unavailable.
        """
        if not config.ENABLE_S3 or not self.s3_client:
            return
        
        try:
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_bytes = buffer.tobytes()
                timestamp = int(time.time())
                filename = f"detection_{timestamp}_conf_{int(confidence*100)}.jpg"
                
                if config.IS_MOCK_ENVIRONMENT:
                    logger.info(f"[MOCK] Would upload '{filename}' to S3")
                else:
                    self.s3_client.put_object(
                        Bucket=config.S3_BUCKET_NAME,
                        Key=filename,
                        Body=frame_bytes
                    )
                    logger.info(f"Uploaded detection snapshot: {filename}")
        except Exception as e:
            logger.error(f"Detection snapshot upload error: {e}", exc_info=True)

    def s3_snapshot_loop(self) -> None:
        """
        Periodic camera snapshot upload loop.
        
        Continuously captures and uploads camera snapshots to S3 at configured
        intervals for historical archival purposes.
        
        Note:
            Runs in background thread. Disabled if ENABLE_S3 is False.
        """
        if not config.ENABLE_S3:
            logger.info("S3 snapshot uploads disabled")
            return
        
        mode = "MOCK" if config.IS_MOCK_ENVIRONMENT else "REAL"
        logger.info(f"S3 snapshot loop started ({mode} mode)")
        
        while self.is_running:
            try:
                frame, _ = self.vision_processor.capture_and_process_frame()
                if frame is not None:
                    ret, buffer = cv2.imencode('.jpg', frame)
                    if ret:
                        frame_bytes = buffer.tobytes()
                        timestamp = int(time.time())
                        filename = f"snapshot_{timestamp}.jpg"
                        
                        if config.IS_MOCK_ENVIRONMENT:
                            logger.debug(f"[MOCK] Would upload '{filename}'")
                        else:
                            self.s3_client.put_object(
                                Bucket=config.S3_BUCKET_NAME,
                                Key=filename,
                                Body=frame_bytes
                            )
                            logger.info(f"Uploaded snapshot: {filename}")
                else:
                    logger.warning("Failed to capture frame for S3 snapshot")
            except Exception as e:
                logger.error(f"S3 snapshot loop error: {e}", exc_info=True)
            
            time.sleep(config.S3_SNAPSHOT_INTERVAL_SECONDS)

    def telemetry_loop(self) -> None:
        """
        Main telemetry collection and publishing loop.
        
        Continuously reads all enabled sensors and publishes data to AWS IoT Core
        via MQTT. Also persists data to DynamoDB for historical analysis.
        
        Note:
            Runs in background thread. Respects sensor enable/disable states.
        """
        logger.info("Telemetry loop started")
        
        while self.is_running:
            # Wait for at least one sensor to be enabled
            while (self.is_running and not any([
                self.sensor_events["temperature"].is_set(),
                self.sensor_events["humidity"].is_set(),
                self.sensor_events["vibration"].is_set(),
                self.sensor_events["sound"].is_set()
            ])):
                time.sleep(1)
            
            if not self.is_running:
                break
            
            try:
                payload = {"timestamp": int(time.time())}
                
                # Read BME280 (temperature and humidity)
                if ((self.sensor_events["temperature"].is_set() or 
                     self.sensor_events["humidity"].is_set()) and 
                    self.temp_humidity_sensor is not None):
                    temp, humidity = self.temp_humidity_sensor.get_temp_humidity()
                    
                    if self.sensor_events["temperature"].is_set():
                        payload["temperature"] = temp
                    
                    if self.sensor_events["humidity"].is_set():
                        payload["humidity"] = humidity
                
                # Read vibration sensor
                if (self.sensor_events["vibration"].is_set() and 
                    self.vibration_sensor is not None):
                    payload["vibration_rms"] = (
                        self.vibration_sensor.get_rms_acceleration()
                    )

                # Read sound sensor
                if (self.sensor_events["sound"].is_set() and 
                    self.sound_sensor is not None):
                    payload["sound_db"] = self.sound_sensor.get_db_level()
                    payload["sound_freq"] = (
                        self.sound_sensor.get_dominant_frequency()
                    )
                
                # Publish if we have data
                if len(payload) > 1:
                    self.mqtt_client.publish(
                        config.TOPIC_TELEMETRY,
                        json.dumps(payload),
                        qos=1
                    )
                    logger.info(f"Published telemetry: {payload}")
                    
                    # Store in DynamoDB
                    self.write_to_dynamodb(payload)
                    
            except Exception as e:
                logger.error(f"Telemetry loop error: {e}", exc_info=True)
            
            time.sleep(config.TELEMETRY_INTERVAL_SECONDS)

    def vision_loop(self) -> None:
        """
        AI vision detection loop for queen bee identification.
        
        Continuously processes video frames for queen detection using TensorFlow Lite.
        Supports two modes:
        - continuous: Real-time detection with smart cooldown
        - interval: Legacy periodic detection mode
        
        Detection events are published to MQTT and snapshots uploaded to S3.
        
        Note:
            Runs in background thread. Respects vision sensor enable/disable state.
        """
        if (self.vision_processor is None or 
            self.vision_processor.camera is None):
            logger.warning("Vision processor unavailable. Vision loop not started.")
            return
        
        logger.info(f"Vision loop started (mode: {config.VISION_DETECTION_MODE})")
        
        last_detection_time = 0
        last_detection_box = None
        frame_counter = 0
        
        while self.is_running:
            try:
                self.sensor_events["vision"].wait()
                
                if not self.is_running:
                    break
                
                if config.VISION_DETECTION_MODE == "continuous":
                    frame_counter += 1
                    should_process = (
                        frame_counter % config.VISION_PROCESS_EVERY_N_FRAMES == 0
                    )
                    
                    frame, (box, confidence) = (
                        self.vision_processor.capture_and_process_frame(
                            run_inference=should_process
                        )
                    )
                    
                    if box is not None and confidence is not None:
                        current_time = time.time()
                        time_since_last = current_time - last_detection_time
                        should_publish = False
                        
                        if last_detection_time == 0:
                            should_publish = True
                            logger.info("First queen detection")
                        elif (time_since_last >= 
                              config.VISION_DETECTION_COOLDOWN_SECONDS):
                            should_publish = True
                            logger.info(f"Queen detected (cooldown expired: "
                                      f"{int(time_since_last)}s)")
                        elif (last_detection_box is not None and 
                              self._is_different_queen(box, last_detection_box)):
                            should_publish = True
                            logger.info("Different queen detected (new position)")
                        
                        if should_publish:
                            payload = {
                                "timestamp": int(current_time),
                                "queen_detected": True,
                                "confidence": float(confidence),
                                "box": (box if isinstance(box, list) 
                                       else box.tolist())
                            }
                            self.mqtt_client.publish(
                                config.TOPIC_VISION,
                                json.dumps(payload),
                                qos=1
                            )
                            
                            self.upload_detection_snapshot(frame, confidence)
                            
                            last_detection_time = current_time
                            last_detection_box = box
                    
                    time.sleep(0.01)
                
                else:  # interval mode
                    frame, (box, confidence) = (
                        self.vision_processor.capture_and_process_frame(
                            run_inference=True
                        )
                    )
                    
                    if box is not None and confidence is not None:
                        payload = {
                            "timestamp": int(time.time()),
                            "queen_detected": True,
                            "confidence": float(confidence),
                            "box": (box if isinstance(box, list) 
                                   else box.tolist())
                        }
                        self.mqtt_client.publish(
                            config.TOPIC_VISION,
                            json.dumps(payload),
                            qos=1
                        )
                        self.upload_detection_snapshot(frame, confidence)
                    
                    time.sleep(config.VISION_LOOP_INTERVAL_SECONDS)

            except Exception as e:
                logger.error(f"Vision loop error: {e}", exc_info=True)
                time.sleep(1)
    
    def _is_different_queen(self, box1: np.ndarray, box2: np.ndarray, 
                           threshold: float = 0.3) -> bool:
        """
        Determine if two bounding boxes represent different queens.
        
        Uses Intersection over Union (IoU) metric. Boxes with low IoU
        likely represent different queens or significantly different positions.
        
        Args:
            box1: First bounding box [y_min, x_min, y_max, x_max] (normalized)
            box2: Second bounding box [y_min, x_min, y_max, x_max] (normalized)
            threshold: IoU threshold (lower = more sensitive to position changes)
        
        Returns:
            True if boxes are significantly different (likely different queen)
        """
        b1 = np.array(box1)
        b2 = np.array(box2)
        
        # Calculate intersection
        y_min_inter = max(b1[0], b2[0])
        x_min_inter = max(b1[1], b2[1])
        y_max_inter = min(b1[2], b2[2])
        x_max_inter = min(b1[3], b2[3])
        
        # Check for overlap
        if y_max_inter <= y_min_inter or x_max_inter <= x_min_inter:
            return True
        
        # Calculate areas
        intersection_area = (y_max_inter - y_min_inter) * (x_max_inter - x_min_inter)
        box1_area = (b1[2] - b1[0]) * (b1[3] - b1[1])
        box2_area = (b2[2] - b2[0]) * (b2[3] - b2[1])
        union_area = box1_area + box2_area - intersection_area
        
        # Calculate IoU
        iou = intersection_area / union_area if union_area > 0 else 0
        
        return iou < threshold

    def run(self) -> None:
        """
        Start all system threads and run the main event loop.
        
        Initializes and starts:
        - Video streaming server
        - S3 snapshot upload loop
        - Telemetry collection loop
        - AI vision detection loop
        
        Blocks until KeyboardInterrupt or system shutdown.
        """
        logger.info("Starting all system threads")
        
        all_threads = []
        
        try:
            task_map = {
                self.start_video_server: (),
                self.s3_snapshot_loop: (),
                self.telemetry_loop: (),
                self.vision_loop: (),
            }
            
            for target_func, args in task_map.items():
                thread = threading.Thread(
                    target=target_func,
                    args=args,
                    daemon=True
                )
                thread.start()
                all_threads.append(thread)

            logger.info("All threads started. System is operational.")
            
            # Keep main thread alive
            while self.is_running:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        finally:
            self.is_running = False
            logger.info("Stopping MQTT loop and disconnecting")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            logger.info("Application stopped")


def main():
    """
    Application entry point.
    
    Initializes the Smart Hive system and starts the main event loop.
    Provides comprehensive error handling and troubleshooting guidance.
    """
    try:
        system = SmartHiveSystem()
        if system.is_running:
            system.run()
        else:
            logger.error("System failed to initialize. Check error messages above.")
            logger.info("Common issues:")
            logger.info("  - Camera not accessible (/dev/video0)")
            logger.info("  - TFLite model file missing (queen_bee.tflite)")
            logger.info("  - I2C sensors not detected")
            logger.info("  - AWS credentials not configured")
            time.sleep(5)
    except Exception as e:
        logger.critical(f"FATAL ERROR during initialization: {e}", exc_info=True)
        logger.info("\nTroubleshooting:")
        logger.info("  1. Check camera: ls -l /dev/video*")
        logger.info("  2. Verify TFLite model: ls -l queen_bee.tflite")
        logger.info("  3. Check I2C devices: sudo i2cdetect -y 1")
        logger.info("  4. Verify AWS credentials: aws sts get-caller-identity")
        time.sleep(30)


if __name__ == "__main__":
    main()
