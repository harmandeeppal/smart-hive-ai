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
    from mock_components import MockSHT31, MockMPU6050, MockINMP441, MockVisionProcessor
else:
    from real_components import RealSHT31, RealMPU6050, RealVisionProcessor
    from mock_components import MockINMP441 as RealINMP441 # Placeholder

class SmartHiveSystem:
    def __init__(self):
        print("Initializing Smart Hive System...")
        self.is_running = True
        self.initialize_components()
        self.initialize_aws_clients()

        self.sensor_events = {
            "temperature": threading.Event(),
            "vibration": threading.Event(),
            "sound": threading.Event(),
            "vision": threading.Event() # Added for consistency
        }
        for event in self.sensor_events.values():
            event.set()

        self.flask_app = Flask(__name__)
        self.setup_routes()

    def initialize_components(self):
        """Initializes all hardware or mock components."""
        if config.IS_MOCK_ENVIRONMENT:
            print("INITIALIZING MOCK ENVIRONMENT...")
            self.temp_humidity_sensor = MockSHT31()
            self.vibration_sensor = MockMPU6050()
            self.sound_sensor = MockINMP441()
            self.vision_processor = MockVisionProcessor(model_path="queen_bee.tflite")
        else:
            # This block is for the real Raspberry Pi
            print("INITIALIZING REAL HARDWARE...")
            self.temp_humidity_sensor = RealSHT31()
            self.vibration_sensor = RealMPU6050()
            self.sound_sensor = RealINMP441() # Still using mock as a placeholder
            self.vision_processor = RealVisionProcessor(model_path="queen_bee.tflite")

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

        if not config.IS_MOCK_ENVIRONMENT:
            self.s3_client = boto3.client('s3')
        else:
            self.s3_client = None
        print("AWS clients initialized.")

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
        from the vision processor.
        """
        while self.is_running:
            # Wait until the vision processing loop has a frame ready
            if self.vision_processor.frame is not None:
                # Encode the frame as a JPEG
                ret, buffer = cv2.imencode('.jpg', self.vision_processor.frame)
                if ret:
                    # Convert the buffer to bytes
                    frame_bytes = buffer.tobytes()
                    # Yield the frame in the multipart format
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Control the frame rate to be gentle on the CPU
            time.sleep(0.05)

    def start_video_server(self):
        """
        Starts the Flask video server in a separate thread.
        NOTE: The port must be different from the main dashboard's port.
        """
        print("Starting video streaming server on port 5001...")
        self.flask_app.run(host='0.0.0.0', port=5001, debug=False)

    # --- Individual Task Loops ---
    def s3_snapshot_loop(self):
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
        """Uploads a snapshot of a queen detection to S3."""
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
    
    def telemetry_loop(self):
        """--- ENHANCEMENT: Unified loop for all telemetry sensors ---"""
        while self.is_running:
            try:
                payload = {"timestamp": int(time.time())}
                
                if self.sensor_events["temperature"].is_set():
                    temp, humidity = self.temp_humidity_sensor.get_temp_humidity()
                    payload["temperature"] = temp
                    payload["humidity"] = humidity
                
                if self.sensor_events["vibration"].is_set():
                    payload["vibration_rms"] = self.vibration_sensor.get_rms_acceleration()

                if self.sensor_events["sound"].is_set():
                    payload["sound_db"] = self.sound_sensor.get_db_level()
                
                if len(payload) > 1: # Only publish if there's data
                    self.mqtt_client.publish(config.TOPIC_TELEMETRY, json.dumps(payload), qos=1)
                    print(f"Published Telemetry: {payload}")
                    
            except Exception as e:
                print(f"Error in telemetry loop: {e}")
            
            time.sleep(5) # Main telemetry interval

    def vision_loop(self):
        """Loop for performing AI vision detection and publishing results."""
        while self.is_running:
            try:
                self.sensor_events["vision"].wait() # Allow pausing the vision task
                frame, (box, confidence) = self.vision_processor.capture_and_process_frame()
                
                if box is not None and confidence is not None:
                    # 1. Publish detection event to dashboard
                    payload = {
                        "timestamp": int(time.time()),
                        "queen_detected": True,
                        "confidence": float(confidence),
                        "box": box if isinstance(box, list) else box.tolist() # Convert numpy array to list for JSON
                    }
                    self.mqtt_client.publish(config.TOPIC_VISION, json.dumps(payload), qos=1)

                    # 2. Upload a snapshot of the detection
                    self.upload_detection_snapshot(frame, confidence)

            except Exception as e:
                print(f"Error in vision loop: {e}")

            time.sleep(0.1) # Vision processing can be faster

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
    system = SmartHiveSystem()
    if system.is_running:
        system.run()

