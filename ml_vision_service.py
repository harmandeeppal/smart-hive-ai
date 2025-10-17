"""
Smart Hive AI - Vision Inference Service (Option A - MQTT Frame Consumption)
Separated microservice for YOLO-based queen bee detection

Architecture:
- Subscribes to camera frames from edge-app via MQTT (hive/telemetry/camera/frame)
- Processes frames with YOLO v8 model
- Publishes detections to hive/vision/results
- NO direct camera access - consumes frames via MQTT
"""

import threading
import ssl
import sys
import os
import cv2
import logging
import numpy as np
import json
from datetime import datetime
from queue import Queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from paho.mqtt import client as mqtt_client

try:
    from ml_vision_model.vision_processor import VisionProcessor
    VISION_AVAILABLE = True
    logger.info("✅ VisionProcessor imported successfully")
except Exception as e:
    logger.warning(f"⚠️  VisionProcessor import failed: {e}")
    VISION_AVAILABLE = False


class VisionInferenceService:
    """
    Microservice for vision-only inference (YOLO detection)
    
    Option A Implementation:
    - Subscribes to MQTT frames from edge-app
    - Processes frames externally provided
    - NO camera device access needed
    """
    
    def __init__(self):
        print("=" * 70)
        print("Smart Hive AI - Vision Inference Microservice (Option A - MQTT)")
        print("=" * 70)
        
        self.is_running = True
        self.mqtt_client = None
        self.vision_processor = None
        self.frame_queue = Queue(maxsize=2)  # Keep only latest 2 frames
        self.frame_counter = 0
        self.last_inference_time = 0
        
        # Load configuration
        self.mqtt_broker = config.MQTT_BROKER
        self.mqtt_port = config.MQTT_PORT
        self.client_id = f"vision-service-{os.getenv('HOSTNAME', 'pi')}"
        self.vision_enabled = True
        
        # Initialize vision processor if available
        if VISION_AVAILABLE:
            try:
                self.vision_processor = VisionProcessor(use_camera=False)  # NO camera needed
                logger.info("✅ Vision processor initialized (MQTT frame mode)")
            except Exception as e:
                logger.warning(f"⚠️  Vision processor init failed: {e}")
                self.vision_processor = None
        
        self.setup_mqtt()
    
    def setup_mqtt(self):
        """Setup MQTT client connection"""
        # Use VERSION1 for compatibility with older paho-mqtt versions
        try:
            self.mqtt_client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, client_id=self.client_id)
        except AttributeError:
            # Fallback for older paho-mqtt that doesn't have CallbackAPIVersion
            self.mqtt_client = mqtt_client.Client(client_id=self.client_id)
        
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect
        
        # Setup connection (local mosquitto, no TLS)
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()
            logger.info(f"✅ MQTT connecting to {self.mqtt_broker}:{self.mqtt_port}")
        except Exception as e:
            logger.error(f"❌ MQTT connection failed: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info("✅ MQTT connected successfully")
            # Subscribe to camera frames and control messages
            client.subscribe(config.TOPIC_CAMERA_FRAME)
            logger.info(f"📨 Subscribed to: {config.TOPIC_CAMERA_FRAME}")
            client.subscribe("hive/ml/control")
            client.subscribe("hive/vision/enable")
        else:
            logger.error(f"❌ MQTT connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """MQTT disconnect callback"""
        if rc != 0:
            logger.warning(f"⚠️  Unexpected disconnection {rc}")
    
    def on_message(self, client, userdata, msg):
        """
        Handle incoming MQTT messages
        - Frame data: Add to queue for processing (binary JPEG)
        - Control messages: Handle enable/disable
        """
        try:
            if msg.topic == config.TOPIC_CAMERA_FRAME:
                # Receive frame data (binary JPEG from edge-app)
                self.frame_counter += 1
                try:
                    # Decompress JPEG binary data to numpy array
                    nparr = np.frombuffer(msg.payload, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # Add to queue (will overwrite old frame if queue full)
                        try:
                            self.frame_queue.put_nowait(frame)
                        except:
                            # Queue full, try to remove old frame and add new one
                            try:
                                self.frame_queue.get_nowait()
                                self.frame_queue.put_nowait(frame)
                            except:
                                pass
                except Exception as e:
                    logger.debug(f"Frame decode error: {e}")
            
            elif msg.topic in ["hive/ml/control", "hive/vision/enable"]:
                # Handle control messages
                try:
                    payload = msg.payload.decode()
                    if "enable" in payload.lower():
                        self.vision_enabled = True
                        logger.info("🟢 Vision enabled")
                    elif "disable" in payload.lower():
                        self.vision_enabled = False
                        logger.info("🔴 Vision disabled")
                except Exception as e:
                    logger.debug(f"Control message parse error: {e}")
        
        except Exception as e:
            logger.error(f"❌ Message handling error: {e}")
    
    def run_vision_inference(self):
        """
        Run continuous vision inference on frames from MQTT queue
        
        Process:
        1. Get frame from queue (if available)
        2. Run YOLO inference
        3. Publish results to MQTT
        """
        if not self.vision_processor:
            logger.warning("⚠️  Vision processor not available")
            return
        
        logger.info("🎥 Starting vision inference loop (MQTT frames)...")
        inference_errors = 0
        max_errors = 10
        
        while self.is_running:
            try:
                # Get frame from queue
                if self.frame_queue.empty():
                    # No frame available yet
                    import time
                    time.sleep(0.05)
                    continue
                
                # Skip if vision disabled
                if not self.vision_enabled:
                    import time
                    time.sleep(0.1)
                    continue
                
                # Get latest frame from queue
                frame = self.frame_queue.get(timeout=1)
                
                # Run YOLO inference on external frame (NO camera needed)
                results = self.vision_processor.process_frame(frame)
                
                if results and results.get('detected'):
                    # Publish detections
                    message = {
                        "timestamp": datetime.now().isoformat(),
                        "model_type": "vision_yolo_v8",
                        "detected": True,
                        "confidence": float(results.get('confidence', 0)),
                        "boxes": results.get('boxes', []),
                        "frame_number": self.frame_counter
                    }
                    
                    self.mqtt_client.publish(
                        "hive/vision/results",
                        json.dumps(message),
                        qos=1
                    )
                    logger.info(f"✅ Detection published (conf: {message['confidence']:.2f})")
                    inference_errors = 0
                
            except Exception as e:
                inference_errors += 1
                logger.error(f"❌ Vision inference error: {e}")
                if inference_errors >= max_errors:
                    logger.error(f"Too many errors ({max_errors}), stopping...")
                    self.is_running = False
                import time
                time.sleep(0.1)
    
    def run(self):
        """Main service loop"""
        logger.info("🚀 Vision Service (Option A - MQTT) starting...")
        
        try:
            self.run_vision_inference()
        except KeyboardInterrupt:
            logger.info("⏹️  Vision service stopped by user")
        except Exception as e:
            logger.error(f"❌ Vision service error: {e}")
        finally:
            self.is_running = False
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            logger.info("Vision service stopped")


if __name__ == "__main__":
    service = VisionInferenceService()
    service.run()
