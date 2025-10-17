"""
Smart Hive AI - ML Inference Microservice

Description:
    Independent microservice for ML-based queen bee detection.
    Uses existing ml_vision_model and ml_audio_model implementations.
    Subscribes to MQTT for control commands and publishes detection results.
    
    Runs as separate Docker container from edge application for:
    - Resource isolation (independent CPU cores)
    - Better monitoring (separate process)
    - Scalability (can run multiple instances)
    - Maintainability (ML separate from sensors)

Architecture:
    Input:
    - Camera device: /dev/video0 (for YOLO inference)
    - Audio device: /dev/snd (for audio classification)
    - MQTT control topic: hive/ml/control
      Commands: {"model": "vision", "enable": true/false}
              {"model": "audio", "enable": true/false}
    
    Output:
    - MQTT results topic: hive/ml/vision/results
      Detection results: {timestamp, model_type, detected, confidence, ...}
    
    - MQTT results topic: hive/ml/audio/results
      Classification results: {timestamp, model_type, classification, confidence}
    
    - MQTT health topic: hive/ml/health
      Service health: {timestamp, service, status, vision_enabled, audio_enabled, ...}

Author: Smart Hive AI Team
Created: October 2025
Updated: December 2024 - Using existing ml_vision_model and ml_audio_model
"""

import json
import time
import threading
import ssl
import sys
import os
import cv2
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from paho.mqtt import client as mqtt_client

# Import existing ML processors from the project
try:
    from ml_vision_model.vision_processor import VisionProcessor
    VISION_AVAILABLE = True
    logger.info("✅ VisionProcessor imported successfully")
except Exception as e:
    logger.warning(f"⚠️  VisionProcessor import failed: {e}")
    VISION_AVAILABLE = False

try:
    from ml_audio_model.audio_processor import AudioProcessor
    AUDIO_AVAILABLE = True
    logger.info("✅ AudioProcessor imported successfully")
except Exception as e:
    logger.warning(f"⚠️  AudioProcessor import failed: {e}")
    AUDIO_AVAILABLE = False


class MLInferenceService:
    """
    Microservice for running ML inference tasks independently.
    
    Uses existing implementations:
    - VisionProcessor: YOLO v8-based queen bee detection from ml_vision_model/
    - AudioProcessor: MFCC + ML classification from ml_audio_model/
    
    Handles:
    - Continuous YOLO vision detection on camera frames
    - Periodic audio classification from microphone
    - MQTT communication for commands and results
    - Graceful degradation if models unavailable
    - Health checks and monitoring
    """
    
    def __init__(self):
        """Initialize ML inference service using existing processors."""
        print("=" * 70)
        print("Smart Hive AI - ML Inference Microservice")
        print("=" * 70)
        print("Using existing ml_vision_model and ml_audio_model implementations")
        print("=" * 70)
        
        self.is_running = True
        self.ml_enabled = {
            "vision": getattr(config, 'ENABLE_VISION_MODEL', True),
            "audio": getattr(config, 'ENABLE_AUDIO_MODEL', True)
        }
        
        # Initialize MQTT client
        self.mqtt_client = None
        self.initialize_mqtt()
        
        # Initialize ML processors using existing code
        self.vision_processor = None
        self.audio_processor = None
        self.initialize_ml_processors()
        
        # Control events for enabling/disabling models
        self.vision_event = threading.Event()
        self.audio_event = threading.Event()
        
        if self.ml_enabled["vision"] and self.vision_processor and self.vision_processor.enabled:
            self.vision_event.set()
        if self.ml_enabled["audio"] and self.audio_processor and self.audio_processor.enabled:
            self.audio_event.set()
        
        # Tracking for last inference time
        self.last_vision_inference = 0
        self.last_audio_inference = 0
    
    def initialize_mqtt(self):
        """Initialize MQTT client for AWS IoT Core connection."""
        logger.info("🔌 Initializing MQTT client...")
        
        try:
            self.mqtt_client = mqtt_client.Client(
                callback_api_version=mqtt_client.CallbackAPIVersion.VERSION1,
                client_id="SmartHive_MLService"
            )
            
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            # Configure TLS
            self.mqtt_client.tls_set(
                ca_certs=getattr(config, 'CA_PATH', '/app/certs/AmazonRootCA1.pem'),
                certfile=getattr(config, 'CERT_PATH', '/app/certs/certificate.pem.crt'),
                keyfile=getattr(config, 'KEY_PATH', '/app/certs/private.pem.key'),
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS
            )
            
            # Connect to AWS IoT Core
            endpoint = getattr(config, 'AWS_ENDPOINT', os.environ.get('MQTT_BROKER', 'localhost'))
            self.mqtt_client.connect(endpoint, 8883, 60)
            self.mqtt_client.loop_start()
            
            logger.info("✅ MQTT client initialized")
            
        except Exception as e:
            logger.error(f"❌ MQTT initialization failed: {e}")
            self.is_running = False
    
    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection."""
        if rc == 0:
            logger.info("✅ Connected to AWS IoT Core (ML Service)")
            
            # Subscribe to ML control topic
            client.subscribe("hive/ml/control")
            logger.info("📡 Subscribed to hive/ml/control")
        else:
            logger.error(f"❌ MQTT connection failed with code {rc}")
    
    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection."""
        if rc != 0:
            logger.warning(f"⚠️  Unexpected MQTT disconnection: {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages for ML control."""
        try:
            payload = json.loads(msg.payload.decode())
            
            # Handle ML control commands
            if msg.topic == "hive/ml/control":
                model = payload.get("module", payload.get("model"))  # Support both names
                enabled = payload.get("enable", payload.get("command") == "enable")
                
                if model == "vision":
                    if enabled and self.vision_processor and self.vision_processor.enabled:
                        self.vision_event.set()
                        self.vision_processor.enable()
                        logger.info("🐝 Vision model enabled")
                    else:
                        self.vision_event.clear()
                        if self.vision_processor:
                            self.vision_processor.disable()
                        logger.info("🐝 Vision model disabled")
                
                elif model == "audio":
                    if enabled and self.audio_processor and self.audio_processor.enabled:
                        self.audio_event.set()
                        self.audio_processor.enable()
                        logger.info("🔊 Audio model enabled")
                    else:
                        self.audio_event.clear()
                        if self.audio_processor:
                            self.audio_processor.disable()
                        logger.info("🔊 Audio model disabled")
                
                elif model == "all":
                    if enabled:
                        self.vision_event.set()
                        self.audio_event.set()
                        if self.vision_processor:
                            self.vision_processor.enable()
                        if self.audio_processor:
                            self.audio_processor.enable()
                        logger.info("� All models enabled")
                    else:
                        self.vision_event.clear()
                        self.audio_event.clear()
                        if self.vision_processor:
                            self.vision_processor.disable()
                        if self.audio_processor:
                            self.audio_processor.disable()
                        logger.info("🔴 All models disabled")
                
                # Publish status
                status = {
                    "timestamp": int(time.time()),
                    "model": model,
                    "enabled": enabled
                }
                self.mqtt_client.publish("hive/ml/status", json.dumps(status), qos=1)
        
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def initialize_ml_processors(self):
        """
        Initialize ML processors using existing ml_vision_model and ml_audio_model.
        
        Uses:
        - ml_vision_model/vision_processor.py: VisionProcessor class
        - ml_audio_model/audio_processor.py: AudioProcessor class
        
        Models:
        - Vision: ml_vision_model/vision_model.pt (YOLO v8, pre-trained)
        - Audio: ml_audio_model/audio_model.pkl (scikit-learn classifier, pre-trained)
        """
        logger.info("🤖 Initializing ML processors...")
        
        # Vision processor initialization
        if VISION_AVAILABLE and self.ml_enabled["vision"]:
            try:
                vision_model_path = getattr(
                    config, 
                    'VISION_MODEL_PATH', 
                    'models/vision_model.pt'
                )
                confidence_threshold = getattr(
                    config,
                    'VISION_CONFIDENCE_THRESHOLD',
                    0.7
                )
                
                logger.info(f"Loading vision model from: {vision_model_path}")
                self.vision_processor = VisionProcessor(
                    model_path=vision_model_path,
                    confidence_threshold=confidence_threshold
                )
                
                if self.vision_processor.enabled:
                    logger.info("✅ Vision processor initialized (YOLO v8)")
                else:
                    logger.warning("⚠️  Vision processor disabled (model not loaded)")
            except Exception as e:
                logger.error(f"❌ Vision processor init failed: {e}")
        else:
            if not VISION_AVAILABLE:
                logger.warning("⚠️  VisionProcessor not available (import failed)")
            if not self.ml_enabled["vision"]:
                logger.info("ℹ️  Vision model disabled in config")
        
        # Audio processor initialization
        if AUDIO_AVAILABLE and self.ml_enabled["audio"]:
            try:
                audio_model_path = getattr(
                    config,
                    'AUDIO_MODEL_PATH',
                    'models/audio_model.pkl'
                )
                sample_rate = getattr(config, 'AUDIO_SAMPLE_RATE', 22050)
                confidence_threshold = getattr(
                    config,
                    'AUDIO_CONFIDENCE_THRESHOLD',
                    0.6
                )
                
                logger.info(f"Loading audio model from: {audio_model_path}")
                self.audio_processor = AudioProcessor(
                    model_path=audio_model_path,
                    sample_rate=sample_rate,
                    confidence_threshold=confidence_threshold,
                    save_recordings=False  # Don't save recordings in production
                )
                
                if self.audio_processor.enabled:
                    logger.info("✅ Audio processor initialized (MFCC + ML)")
                else:
                    logger.warning("⚠️  Audio processor disabled (model not loaded)")
            except Exception as e:
                logger.error(f"❌ Audio processor init failed: {e}")
        else:
            if not AUDIO_AVAILABLE:
                logger.warning("⚠️  AudioProcessor not available (import failed)")
            if not self.ml_enabled["audio"]:
                logger.info("ℹ️  Audio model disabled in config")
    
    def vision_inference_loop(self):
        """
        Run continuous YOLO inference on camera frames.
        
        Uses VisionProcessor.process_frame() from ml_vision_model/vision_processor.py
        which handles:
        - YOLO v8 model inference
        - Queen detection filtering
        - Confidence thresholding
        - Bounding box extraction
        """
        if self.vision_processor is None or not self.vision_processor.enabled:
            logger.warning("⚠️  Vision processor not available")
            return
        
        logger.info("🐝 Vision inference loop started (YOLO v8 - using VisionProcessor)")
        last_detection_time = 0
        frame_counter = 0
        
        try:
            # Initialize camera for frame capture
            cap = cv2.VideoCapture(0)  # USB camera at /dev/video0
            if not cap.isOpened():
                logger.error("❌ Cannot open camera at /dev/video0")
                return
            
            # Set camera resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            while self.is_running:
                try:
                    # Wait until vision is enabled
                    if not self.vision_event.is_set():
                        time.sleep(0.1)
                        continue
                    
                    frame_counter += 1
                    
                    # Capture frame
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        time.sleep(0.01)
                        continue
                    
                    # Process only every Nth frame for efficiency (config-based)
                    vision_skip_frames = getattr(config, 'VISION_PROCESS_EVERY_N_FRAMES', 4)
                    if frame_counter % vision_skip_frames != 0:
                        time.sleep(0.01)
                        continue
                    
                    # Run YOLO inference using VisionProcessor.process_frame()
                    result = self.vision_processor.process_frame(frame)
                    self.last_vision_inference = time.time()
                    
                    if result and result.get('detected'):
                        current_time = time.time()
                        cooldown = getattr(config, 'VISION_DETECTION_COOLDOWN_SECONDS', 5)
                        time_since_last = current_time - last_detection_time
                        
                        # Publish if enough time has passed to avoid MQTT spam
                        if time_since_last >= cooldown:
                            payload = {
                                "timestamp": int(current_time),
                                "model_type": "yolov8",
                                "detected": True,
                                "confidence": result.get('confidence'),
                                "inference_time_ms": result.get('inference_time_ms'),
                                "boxes": result.get('boxes', [])
                            }
                            self.mqtt_client.publish(
                                getattr(config, 'TOPIC_VISION_RESULTS', 'hive/ml/vision/results'),
                                json.dumps(payload),
                                qos=1
                            )
                            logger.info(f"� Queen detected (confidence: {result.get('confidence'):.2f}, "
                                      f"inference: {result.get('inference_time_ms', 0):.0f}ms)")
                            last_detection_time = current_time
                    
                    time.sleep(0.01)
                
                except Exception as e:
                    logger.error(f"Error in vision inference: {e}")
                    time.sleep(0.5)
        
        finally:
            cap.release()
            logger.info("Vision inference loop stopped")
    
    def audio_inference_loop(self):
        """
        Run periodic audio classification.
        
        Uses AudioProcessor.record_and_classify() from ml_audio_model/audio_processor.py
        which handles:
        - Microphone recording at configured sample rate
        - MFCC feature extraction (13 coefficients + delta + delta-delta)
        - scikit-learn model inference
        - Confidence scoring
        """
        if self.audio_processor is None or not self.audio_processor.enabled:
            logger.warning("⚠️  Audio processor not available")
            return
        
        logger.info("🔊 Audio inference loop started (MFCC + ML - using AudioProcessor)")
        
        while self.is_running:
            try:
                # Wait until audio is enabled
                if not self.audio_event.is_set():
                    time.sleep(1)
                    continue
                
                # Record and classify audio using AudioProcessor.record_and_classify()
                audio_duration = getattr(config, 'AUDIO_RECORD_DURATION_SEC', 10)
                result = self.audio_processor.record_and_classify(duration_sec=audio_duration)
                self.last_audio_inference = time.time()
                
                if result and result.get('status') == 'complete':
                    payload = {
                        "timestamp": int(time.time()),
                        "model_type": "mfcc_classifier",
                        "classification": result.get('classification'),
                        "confidence": result.get('confidence'),
                        "duration_sec": result.get('duration')
                    }
                    self.mqtt_client.publish(
                        getattr(config, 'TOPIC_AUDIO_RESULTS', 'hive/ml/audio/results'),
                        json.dumps(payload),
                        qos=1
                    )
                    logger.info(f"🎤 Audio classification: {result.get('classification')} "
                              f"(confidence: {result.get('confidence'):.2f})")
                elif result and 'error' in result:
                    logger.warning(f"⚠️  Audio recording error: {result.get('error')}")
                
                # Wait before next recording session
                time.sleep(audio_duration + 5)  # 5s buffer
            
            except Exception as e:
                logger.error(f"Error in audio inference loop: {e}")
                time.sleep(5)
    
    
    def health_check_loop(self):
        """
        Periodically publish health status and monitoring information.
        
        Reports on:
        - Service status (running/stopped)
        - Vision model status (enabled/disabled, last inference time)
        - Audio model status (enabled/disabled, last inference time)
        - Processor status (loaded/not loaded)
        - Service uptime
        """
        logger.info("📊 Health check loop started")
        self.start_time = time.time()
        
        while self.is_running:
            try:
                current_time = time.time()
                health = {
                    "timestamp": int(current_time),
                    "service": "ml_inference",
                    "status": "healthy" if self.is_running else "stopping",
                    
                    # Vision status
                    "vision_loaded": self.vision_processor is not None and self.vision_processor.enabled,
                    "vision_enabled": self.vision_event.is_set(),
                    "last_vision_inference": int(self.last_vision_inference) if self.last_vision_inference > 0 else None,
                    
                    # Audio status
                    "audio_loaded": self.audio_processor is not None and self.audio_processor.enabled,
                    "audio_enabled": self.audio_event.is_set(),
                    "last_audio_inference": int(self.last_audio_inference) if self.last_audio_inference > 0 else None,
                    
                    # Service metrics
                    "uptime_seconds": int(current_time - self.start_time),
                }
                
                self.mqtt_client.publish(
                    getattr(config, 'TOPIC_ML_HEALTH', 'hive/ml/health'),
                    json.dumps(health),
                    qos=1
                )
                
                # Health check every 60 seconds
                time.sleep(60)
            
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                time.sleep(60)
    
    def run(self):
        """
        Start all ML inference loops as separate threads.
        
        Threads:
        1. vision_inference_loop - Continuous YOLO inference on camera frames
        2. audio_inference_loop - Periodic audio recording and classification
        3. health_check_loop - Monitor service health every 60 seconds
        
        All threads are daemon threads and will stop when main process exits.
        """
        logger.info("\n" + "=" * 70)
        logger.info("🚀 Starting ML Inference Microservice")
        logger.info("Using existing ml_vision_model and ml_audio_model implementations")
        logger.info("=" * 70)
        
        self.start_time = time.time()
        all_threads = []
        
        try:
            # Create and start all inference threads
            threads = [
                (self.vision_inference_loop, "Vision Inference (YOLO v8)"),
                (self.audio_inference_loop, "Audio Inference (MFCC + ML)"),
                (self.health_check_loop, "Health Check Monitor"),
            ]
            
            for target_func, name in threads:
                thread = threading.Thread(target=target_func, name=name, daemon=True)
                thread.start()
                all_threads.append(thread)
                logger.info(f"✅ Started: {name}")
            
            logger.info("\n" + "=" * 70)
            logger.info("� ML Microservice is running")
            logger.info("Press Ctrl+C to gracefully stop")
            logger.info("=" * 70 + "\n")
            
            # Keep service alive and respond to interrupt
            while self.is_running:
                time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("\n\n⏹️  Shutdown signal received (Ctrl+C)")
        
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """
        Clean shutdown of the ML inference service.
        
        Performs:
        - Stop all inference loops
        - Disable ML processors gracefully
        - Disconnect from MQTT
        - Final status message
        """
        logger.info("\n" + "=" * 70)
        logger.info("🛑 Shutting down ML Inference Microservice...")
        logger.info("=" * 70)
        
        self.is_running = False
        
        # Disable processors
        if self.vision_processor:
            try:
                self.vision_processor.disable()
                logger.info("✅ Vision processor disabled")
            except Exception as e:
                logger.warning(f"⚠️  Error disabling vision: {e}")
        
        if self.audio_processor:
            try:
                self.audio_processor.disable()
                logger.info("✅ Audio processor disabled")
            except Exception as e:
                logger.warning(f"⚠️  Error disabling audio: {e}")
        
        # Stop MQTT
        if self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
                logger.info("✅ MQTT disconnected")
            except Exception as e:
                logger.warning(f"⚠️  Error stopping MQTT: {e}")
        
        logger.info("=" * 70)
        logger.info("✅ ML Microservice stopped successfully")
        logger.info("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        service = MLInferenceService()
        if service.is_running and (service.vision_processor or service.audio_processor):
            service.run()
        else:
            if not service.is_running:
                logger.error("❌ Service failed to initialize - MQTT connection issue")
            if not service.vision_processor and not service.audio_processor:
                logger.error("❌ No ML models available (both vision and audio missing)")
                logger.error("Ensure models exist:")
                logger.error("  - models/vision_model.pt (YOLO v8)")
                logger.error("  - models/audio_model.pkl (scikit-learn classifier)")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

