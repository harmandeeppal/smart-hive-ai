# app.py (Corrected and Enhanced)
import time
import json
import ssl
import threading
import cv2
from flask import Flask, Response
import paho.mqtt.client as mqtt
import boto3
from botocore.exceptions import ClientError
import config
from paho.mqtt import client as mqtt_client

# --- Component Imports ---
if config.IS_MOCK_ENVIRONMENT:
    from mock_components import MockBME280, MockLIS3DH, MockINMP441, MockVisionProcessor
else:
    from real_components import RealBME280, RealLIS3DH, RealVisionProcessor, RealINMP441

class SmartHiveSystem:
    def __init__(self):
        print("Initializing Smart Hive System...")
        self.is_running = True
        
        try:
            self.initialize_components()
        except Exception as e:
            print(f"❌ CRITICAL: Failed to initialize hardware components: {e}")
            import traceback
            traceback.print_exc()
            self.is_running = False
            return
        
        try:
            self.initialize_aws_clients()
        except Exception as e:
            print(f"❌ CRITICAL: Failed to initialize AWS clients: {e}")
            import traceback
            traceback.print_exc()
            self.is_running = False
            return

        self.sensor_events = {
            "temperature": threading.Event(),
            "humidity": threading.Event(),  # ✨ NEW: Separate toggle for humidity
            "vibration": threading.Event(),
            "sound": threading.Event(),
            "vision": threading.Event() # Added for consistency
        }
        for event in self.sensor_events.values():
            event.set()

        self.flask_app = Flask(__name__)
        self.setup_routes()
        print("✅ Smart Hive System initialized successfully!")

    def initialize_components(self):
        """Initializes all hardware or mock components."""
        if config.IS_MOCK_ENVIRONMENT:
            print("INITIALIZING MOCK ENVIRONMENT...")
            self.temp_humidity_sensor = MockBME280()
            self.vibration_sensor = MockLIS3DH()
            self.sound_sensor = MockINMP441()
            self.vision_processor = MockVisionProcessor(model_path="queen_bee.tflite")
        else:
            # This block is for the real Raspberry Pi
            print("INITIALIZING REAL HARDWARE...")
            try:
                self.temp_humidity_sensor = RealBME280()
                print("  ✅ BME280 Temperature/Humidity sensor initialized")
            except Exception as e:
                print(f"  ⚠️  BME280 initialization failed: {e}")
                self.temp_humidity_sensor = None
            
            try:
                self.vibration_sensor = RealLIS3DH()
                print("  ✅ LIS3DH Vibration sensor initialized")
            except Exception as e:
                print(f"  ⚠️  LIS3DH initialization failed: {e}")
                self.vibration_sensor = None
            
            try:
                self.sound_sensor = RealINMP441()
                print("  ✅ INMP441 Sound sensor initialized")
            except Exception as e:
                print(f"  ⚠️  INMP441 initialization failed: {e}")
                self.sound_sensor = None
            
            try:
                self.vision_processor = RealVisionProcessor(model_path="queen_bee.tflite")
                print("  ✅ Vision Processor initialized")
            except Exception as e:
                print(f"  ❌ CRITICAL: Vision Processor initialization failed: {e}")
                import traceback
                traceback.print_exc()
                raise  # Re-raise because vision is critical

    def initialize_aws_clients(self):
        self.mqtt_client = mqtt_client.Client(callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1,client_id=config.THING_NAME)
        # --- ENHANCEMENT: Add auto-reconnect logic ---
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_control_message

        self.mqtt_client.tls_set(ca_certs=config.CA_PATH, certfile=config.CERT_PATH, keyfile=config.KEY_PATH,
                                 cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
        try:
            self.mqtt_client.connect(config.AWS_ENDPOINT, 8883, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            print(f"FATAL: Error connecting to AWS IoT Core: {e}")
            self.is_running = False

        # Initialize S3 client (only if enabled and not in mock environment)
        if config.ENABLE_S3 and not config.IS_MOCK_ENVIRONMENT:
            try:
                self.s3_client = boto3.client('s3')
                # Verify bucket exists
                self.s3_client.head_bucket(Bucket=config.S3_BUCKET_NAME)
                print(f"✅ S3 bucket '{config.S3_BUCKET_NAME}' connected successfully.")
            except Exception as e:
                print(f"⚠️  S3 bucket error: {e}")
                print(f"   S3 uploads will be disabled. Check bucket name in .env file.")
                self.s3_client = None
        else:
            self.s3_client = None
            if not config.ENABLE_S3:
                print("⚠️  S3 disabled (ENABLE_S3 = False)")
        
        print("AWS clients initialized.")

        # Initialize DynamoDB client
        # ✨ FIXED: Removed mock environment check to allow testing on laptop
        if config.ENABLE_DYNAMODB:
           try:
               self.dynamodb = boto3.resource('dynamodb', region_name=config.AWS_REGION)
               self.table = self.dynamodb.Table(config.DYNAMODB_TABLE)
               print(f"✅ DynamoDB table '{config.DYNAMODB_TABLE}' initialized successfully.")
           except Exception as e:
               print(f"❌ Error initializing DynamoDB: {e}")
               print(f"   Make sure AWS credentials are configured (see troubleshooting guide)")
               self.table = None
        else:
           self.table = None
           print("⚠️  DynamoDB disabled (ENABLE_DYNAMODB = False)")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for when the MQTT client connects."""
        if rc == 0:
            print("Successfully connected to AWS IoT Core.")
            client.subscribe(config.TOPIC_CONTROL)
            print(f"Subscribed to control topic: {config.TOPIC_CONTROL}")
        else:
            print(f"Failed to connect to AWS IoT Core, return code {rc}\n. Retrying...")

    def on_control_message(self, client, userdata, msg):
        """Callback for handling commands from the dashboard."""
        try:
            payload = json.loads(msg.payload.decode())
            sensor = payload.get("sensor")
            state = payload.get("state")

            if sensor in self.sensor_events:
                if state == "on":
                    self.sensor_events[sensor].set() # Resume task
                    print(f"Resumed sensor: {sensor}")
                elif state == "off":
                    self.sensor_events[sensor].clear() # Pause task
                    print(f"Paused sensor: {sensor}")
                else:
                    print(f"Invalid state '{state}' for sensor '{sensor}'")
            else:
                print(f"Unknown sensor in control message: {sensor}")
        except json.JSONDecodeError:
            print(f"Could not decode JSON payload from control topic: {msg.payload}")
        except Exception as e:
            print(f"Error in on_control_message: {e}")

    # --- Video Streaming Methods ---
    def setup_routes(self):
        """Sets up the video streaming route for the Flask app."""
        @self.flask_app.route('/video_feed')
        def video_feed():
            # Returns a multipart response, which is the standard for MJPEG streams.
            return Response(self.generate_video_frames(),
                            mimetype='multipart/x-mixed-replace; boundary=frame')

    def generate_video_frames(self):
        """
        A generator function that continuously yields JPEG-encoded frames
        from the vision processor. Captures frames directly for live streaming.
        """
        # Calculate delay based on configured FPS
        frame_delay = 1.0 / config.VIDEO_STREAM_FPS
        
        while self.is_running:
            # Capture a fresh frame directly from camera for live streaming
            # This is separate from AI detection which runs at slower intervals
            if self.vision_processor.camera and self.vision_processor.camera.isOpened():
                ret, frame = self.vision_processor.camera.read()
                if ret and frame is not None:
                    # Use the stored annotated frame from vision loop if available and recent
                    # Otherwise use the raw frame
                    display_frame = self.vision_processor.frame if self.vision_processor.frame is not None else frame
                    
                    # Encode the frame as a JPEG
                    ret, buffer = cv2.imencode('.jpg', display_frame)
                    if ret:
                        # Convert the buffer to bytes
                        frame_bytes = buffer.tobytes()
                        # Yield the frame in the multipart format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Control the frame rate based on config (default: 20 FPS)
            time.sleep(frame_delay)

    def start_video_server(self):
        """
        Starts the Flask video server in a separate thread.
        NOTE: The port must be different from the main dashboard's port.
        """
        print("Starting video streaming server on port 5001...")
        self.flask_app.run(host='0.0.0.0', port=5001, debug=False)

    # --- Individual Task Loops ---
    def s3_snapshot_loop(self):
        """Periodically uploads camera snapshots to S3 (if enabled)."""
        if not config.ENABLE_S3:
            print("⚠️  S3 snapshot uploads disabled (ENABLE_S3 = False)")
            return
        
        if config.IS_MOCK_ENVIRONMENT:
            print("📸 S3 snapshot loop started (MOCK MODE)")
        else:
            print(f"📸 S3 snapshot loop started (bucket: {config.S3_BUCKET_NAME})")
        
        while self.is_running:
            try:
                # --- CORRECTION: Use the newly created method ---
                frame, _ = self.vision_processor.capture_and_process_frame()
                if frame is not None:
                    ret, buffer = cv2.imencode('.jpg', frame)
                    if ret:
                        frame_bytes = buffer.tobytes()
                        timestamp = int(time.time())
                        filename = f"snapshot_{timestamp}.jpg"
                        
                        if config.IS_MOCK_ENVIRONMENT:
                            print(f"[S3 MOCK] Would upload '{filename}' to bucket '{config.S3_BUCKET_NAME}'.")
                        else:
                            self.s3_client.put_object(Bucket=config.S3_BUCKET_NAME, Key=filename, Body=frame_bytes)
                            print(f"Successfully uploaded {filename} to S3.")
                else:
                    print("Failed to capture frame for S3 snapshot.")
            except Exception as e:
                print(f"An error occurred in the S3 snapshot loop: {e}")
            
            time.sleep(config.S3_SNAPSHOT_INTERVAL_SECONDS)

    def upload_detection_snapshot(self, frame, confidence):
        """Uploads a snapshot of a queen detection to S3 (if enabled)."""
        if not config.ENABLE_S3:
            return  # Skip upload if S3 is disabled
        
        try:
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_bytes = buffer.tobytes()
                timestamp = int(time.time())
                filename = f"detection_{timestamp}_conf_{int(confidence*100)}.jpg"
                
                if config.IS_MOCK_ENVIRONMENT:
                    print(f"[S3 MOCK] Queen detected! Would upload '{filename}' to bucket '{config.S3_BUCKET_NAME}'.")
                else:
                    self.s3_client.put_object(Bucket=config.S3_BUCKET_NAME, Key=filename, Body=frame_bytes)
                    print(f"QUEEN DETECTED! Successfully uploaded {filename} to S3.")
        except Exception as e:
            print(f"An error occurred in the detection snapshot upload: {e}")

    def write_to_dynamodb(self, telemetry_data):
       """Writes telemetry data to AWS DynamoDB table.
       
       Args:
           telemetry_data (dict): Dictionary containing sensor readings and timestamp
       
       Data Format:
           {
               'timestamp': 1697123456,
               'temperature': 34.5,
               'humidity': 58.2,
               'vibration_rms': 0.0521,
               'sound_db': 52.3,
               'sound_freq': 265.0
           }
       """
       if not self.table:
           return
       
       try:
           # Import Decimal for DynamoDB compatibility
           from decimal import Decimal
           
           # Prepare item for DynamoDB
           item = {
               'device_id': config.THING_NAME,  # Partition key (String)
               'timestamp': int(telemetry_data.get('timestamp', time.time()))  # Sort key (Number)
           }
           
           # Add human-readable NZ timestamp for easy viewing in AWS Console
           from datetime import datetime
           try:
               from zoneinfo import ZoneInfo
               nz_time = datetime.fromtimestamp(item['timestamp'], tz=ZoneInfo('Pacific/Auckland'))
           except (ImportError, Exception):
               # Fallback to pytz for compatibility (Windows, Python <3.9)
               import pytz
               nz_tz = pytz.timezone('Pacific/Auckland')
               utc_time = datetime.utcfromtimestamp(item['timestamp']).replace(tzinfo=pytz.UTC)
               nz_time = utc_time.astimezone(nz_tz)
           
           item['timestamp_nz'] = nz_time.strftime('%Y-%m-%d %H:%M:%S %Z')  # e.g., "2025-10-15 18:25:40 NZDT"
           print(f"📅 Added timestamp_nz: {item['timestamp_nz']}")  # Debug log
           
           # Add all sensor readings that are present
           # ✨ FIX: Convert float to Decimal for DynamoDB
           if 'temperature' in telemetry_data:
               item['temperature'] = Decimal(str(round(float(telemetry_data['temperature']), 2)))
           
           if 'humidity' in telemetry_data:
               item['humidity'] = Decimal(str(round(float(telemetry_data['humidity']), 2)))
           
           if 'vibration_rms' in telemetry_data:
               item['vibration_rms'] = Decimal(str(round(float(telemetry_data['vibration_rms']), 4)))
           
           if 'sound_db' in telemetry_data:
               item['sound_db'] = Decimal(str(round(float(telemetry_data['sound_db']), 1)))
           
           if 'sound_freq' in telemetry_data:
               item['sound_freq'] = Decimal(str(round(float(telemetry_data['sound_freq']), 1)))
           
           # Write to DynamoDB
           response = self.table.put_item(Item=item)
           
           # Log success with timestamp in NZ time
           from datetime import datetime
           try:
               from zoneinfo import ZoneInfo
               nz_time_log = datetime.fromtimestamp(item['timestamp'], tz=ZoneInfo('Pacific/Auckland'))
           except (ImportError, Exception):
               import pytz
               nz_tz = pytz.timezone('Pacific/Auckland')
               utc_time = datetime.utcfromtimestamp(item['timestamp']).replace(tzinfo=pytz.UTC)
               nz_time_log = utc_time.astimezone(nz_tz)
           
           readable_time = nz_time_log.strftime('%Y-%m-%d %H:%M:%S %Z')
           print(f"✅ DynamoDB: Wrote record at {readable_time} ({len(item)-3} sensors)")
           
       except Exception as e:
           print(f"❌ DynamoDB write error: {e}")
           import traceback
           traceback.print_exc()
           # Don't crash the whole system if database write fails
    
    def telemetry_loop(self):
        """--- ENHANCEMENT: Unified loop for all telemetry sensors ---"""
        while self.is_running:
            # Wait until at least one sensor is enabled before continuing
            while self.is_running and not any([
                self.sensor_events["temperature"].is_set(),
                self.sensor_events["humidity"].is_set(),  # ✨ Added humidity check
                self.sensor_events["vibration"].is_set(),
                self.sensor_events["sound"].is_set()
            ]):
                time.sleep(1)  # Sleep while all sensors are toggled off
            
            if not self.is_running:
                break
                
            try:
                payload = {"timestamp": int(time.time())}
                
                # ✨ FIX: Read BME280 sensor if EITHER temperature OR humidity is enabled
                # BME280 returns both values in one call, but we publish them independently
                if (self.sensor_events["temperature"].is_set() or self.sensor_events["humidity"].is_set()) and self.temp_humidity_sensor is not None:
                    temp, humidity = self.temp_humidity_sensor.get_temp_humidity()
                    
                    # Only add to payload if that specific sensor is enabled
                    if self.sensor_events["temperature"].is_set():
                        payload["temperature"] = temp
                    
                    if self.sensor_events["humidity"].is_set():
                        payload["humidity"] = humidity
                
                if self.sensor_events["vibration"].is_set() and self.vibration_sensor is not None:
                    payload["vibration_rms"] = self.vibration_sensor.get_rms_acceleration()

                if self.sensor_events["sound"].is_set() and self.sound_sensor is not None:
                    payload["sound_db"] = self.sound_sensor.get_db_level()
                    payload["sound_freq"] = self.sound_sensor.get_dominant_frequency()
                
                if len(payload) > 1: # Only publish if there's data
                    self.mqtt_client.publish(config.TOPIC_TELEMETRY, json.dumps(payload), qos=1)
                    print(f"Published Telemetry: {payload}")
                    
                    # Write to DynamoDB (for historical data)
                    self.write_to_dynamodb(payload)
                    
            except Exception as e:
                print(f"Error in telemetry loop: {e}")
            
            time.sleep(config.TELEMETRY_INTERVAL_SECONDS) # Main telemetry interval

    def vision_loop(self):
        """
        AI Vision detection loop with continuous monitoring and smart cooldown.
        
        Two modes:
        1. "continuous": Runs AI on every Nth frame (real-time detection with cooldown)
        2. "interval": Legacy mode - runs AI at fixed intervals
        """
        # Safety check: Ensure vision processor is initialized
        if self.vision_processor is None or self.vision_processor.camera is None:
            print("⚠️  Vision processor not available. Vision loop will not start.")
            return
        
        last_detection_time = 0  # Timestamp of last published detection
        last_detection_box = None  # Bounding box of last detection (to detect different queens)
        frame_counter = 0  # Counter for processing every Nth frame
        
        while self.is_running:
            try:
                # Wait until vision is enabled (blocks when toggled off)
                self.sensor_events["vision"].wait()
                
                if not self.is_running:
                    break
                
                # --- CONTINUOUS MODE: Real-time detection with smart cooldown ---
                if config.VISION_DETECTION_MODE == "continuous":
                    frame_counter += 1
                    
                    # Process every Nth frame to balance CPU usage
                    should_process = (frame_counter % config.VISION_PROCESS_EVERY_N_FRAMES) == 0
                    
                    # Capture frame and run inference
                    frame, (box, confidence) = self.vision_processor.capture_and_process_frame(run_inference=should_process)
                    
                    if box is not None and confidence is not None:
                        current_time = time.time()
                        time_since_last_detection = current_time - last_detection_time
                        
                        # Check if we should publish this detection
                        should_publish = False
                        
                        # Case 1: First detection ever
                        if last_detection_time == 0:
                            should_publish = True
                            print("🐝 First queen detection!")
                        
                        # Case 2: Cooldown expired
                        elif time_since_last_detection >= config.VISION_DETECTION_COOLDOWN_SECONDS:
                            should_publish = True
                            print(f"🐝 Queen detected (cooldown expired after {int(time_since_last_detection)}s)")
                        
                        # Case 3: Different queen detected (bounding box significantly different)
                        elif last_detection_box is not None and self._is_different_queen(box, last_detection_box):
                            should_publish = True
                            print("🐝 Different queen detected (new position)!")
                        
                        # Case 4: During cooldown - don't spam
                        else:
                            # Don't publish, but keep showing bounding box on video
                            pass
                        
                        # Publish detection if criteria met
                        if should_publish:
                            payload = {
                                "timestamp": int(current_time),
                                "queen_detected": True,
                                "confidence": float(confidence),
                                "box": box if isinstance(box, list) else box.tolist()
                            }
                            self.mqtt_client.publish(config.TOPIC_VISION, json.dumps(payload), qos=1)
                            
                            # Upload snapshot
                            self.upload_detection_snapshot(frame, confidence)
                            
                            # Update tracking variables
                            last_detection_time = current_time
                            last_detection_box = box
                    
                    # Small sleep to prevent excessive CPU usage
                    time.sleep(0.01)  # 10ms delay
                
                # --- LEGACY INTERVAL MODE: Periodic detection ---
                else:
                    frame, (box, confidence) = self.vision_processor.capture_and_process_frame(run_inference=True)
                    
                    if box is not None and confidence is not None:
                        # 1. Publish detection event to dashboard
                        payload = {
                            "timestamp": int(time.time()),
                            "queen_detected": True,
                            "confidence": float(confidence),
                            "box": box if isinstance(box, list) else box.tolist()
                        }
                        self.mqtt_client.publish(config.TOPIC_VISION, json.dumps(payload), qos=1)

                        # 2. Upload a snapshot of the detection
                        self.upload_detection_snapshot(frame, confidence)
                    
                    time.sleep(config.VISION_LOOP_INTERVAL_SECONDS)  # Legacy interval

            except Exception as e:
                print(f"Error in vision loop: {e}")
                time.sleep(1)  # Brief sleep on error
    
    def _is_different_queen(self, box1, box2, threshold=0.3):
        """
        Determine if two bounding boxes represent different queens.
        Uses IoU (Intersection over Union) - if boxes don't overlap much, likely different queens.
        
        Args:
            box1: First bounding box [y_min, x_min, y_max, x_max] (normalized 0-1)
            box2: Second bounding box [y_min, x_min, y_max, x_max] (normalized 0-1)
            threshold: IoU threshold (lower = more sensitive to position changes)
        
        Returns:
            bool: True if boxes are significantly different (different queen)
        """
        import numpy as np
        
        # Convert to numpy arrays
        b1 = np.array(box1)
        b2 = np.array(box2)
        
        # Calculate intersection
        y_min_inter = max(b1[0], b2[0])
        x_min_inter = max(b1[1], b2[1])
        y_max_inter = min(b1[2], b2[2])
        x_max_inter = min(b1[3], b2[3])
        
        # Check if boxes intersect
        if y_max_inter <= y_min_inter or x_max_inter <= x_min_inter:
            return True  # No overlap = definitely different queen
        
        # Calculate intersection area
        intersection_area = (y_max_inter - y_min_inter) * (x_max_inter - x_min_inter)
        
        # Calculate areas of both boxes
        box1_area = (b1[2] - b1[0]) * (b1[3] - b1[1])
        box2_area = (b2[2] - b2[0]) * (b2[3] - b2[1])
        
        # Calculate union area
        union_area = box1_area + box2_area - intersection_area
        
        # Calculate IoU
        iou = intersection_area / union_area if union_area > 0 else 0
        
        # If IoU is below threshold, consider them different queens
        return iou < threshold

    def run(self):
        """--- CORRECTION: Cleaned up run method to only manage threads ---"""
        print("Starting all system threads...")
        all_threads = []
        try:
            # Create and start all threads
            task_map = {
                self.start_video_server: (),
                self.s3_snapshot_loop: (),
                self.telemetry_loop: (),
                self.vision_loop: (),
            }
            
            for target_func, args in task_map.items():
                thread = threading.Thread(target=target_func, args=args, daemon=True)
                thread.start()
                all_threads.append(thread)

            print("All threads started. System is running.")
            # Keep the main thread alive to listen for KeyboardInterrupt
            while self.is_running:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\nShutdown signal received. Exiting...")
        finally:
            self.is_running = False
            print("Stopping MQTT loop and disconnecting...")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            print("Application stopped.")

if __name__ == "__main__":
    try:
        system = SmartHiveSystem()
        if system.is_running:
            system.run()
        else:
            print("❌ System failed to initialize. Check error messages above.")
            print("   Common issues:")
            print("   - Camera not accessible (/dev/video0)")
            print("   - TFLite model file missing (queen_bee.tflite)")
            print("   - I2C sensors not detected")
            print("   - AWS credentials not configured")
            time.sleep(5)  # Keep container alive for debugging
    except Exception as e:
        print(f"❌ FATAL ERROR during initialization: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔍 Troubleshooting:")
        print("   1. Check if camera is connected: ls -l /dev/video*")
        print("   2. Verify TFLite model exists: ls -l queen_bee.tflite")
        print("   3. Check I2C devices: sudo i2cdetect -y 1")
        print("   4. Verify AWS credentials: aws sts get-caller-identity")
        time.sleep(30)  # Keep container alive for 30 seconds to see error

