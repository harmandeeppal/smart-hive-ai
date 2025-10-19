"""
Smart Hive AI - Audio Inference Service
Separated microservice for audio classification
"""

import threading
import ssl
import sys
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from paho.mqtt import client as mqtt_client

try:
    from ml_audio_model.audio_processor import AudioProcessor
    AUDIO_AVAILABLE = True
    logger.info("✅ AudioProcessor imported successfully")
except Exception as e:
    logger.warning(f"⚠️  AudioProcessor import failed: {e}")
    AUDIO_AVAILABLE = False


class AudioInferenceService:
    """Microservice for audio-only inference (classification)"""
    
    def __init__(self):
        print("=" * 70)
        print("Smart Hive AI - Audio Inference Microservice")
        print("=" * 70)
        
        self.is_running = True
        self.mqtt_client = None
        self.audio_processor = None
        self.recording_requested = False
        self.recording_duration = 60  # Default 60 seconds
        
        # Load configuration
        self.mqtt_broker = config.MQTT_BROKER
        self.mqtt_port = config.MQTT_PORT
        self.client_id = f"audio-service-{os.getenv('HOSTNAME', 'pi')}"
        
        # Initialize audio processor if available
        if AUDIO_AVAILABLE:
            try:
                # Use configured audio model path and windowing settings
                audio_model_path = getattr(config, 'AUDIO_MODEL_PATH', 'models/audio_model.pkl')
                window_seconds = getattr(config, 'AUDIO_WINDOW_SECONDS', 1.0)
                hop_seconds = getattr(config, 'AUDIO_HOP_SECONDS', 0.5)
                aggregation_method = getattr(config, 'AUDIO_AGGREGATION_METHOD', 'max_proba')
                confidence_threshold = getattr(config, 'AUDIO_CONFIDENCE_THRESHOLD', 0.6)
                
                self.audio_processor = AudioProcessor(
                    model_path=audio_model_path,
                    window_seconds=window_seconds,
                    hop_seconds=hop_seconds,
                    aggregation_method=aggregation_method,
                    confidence_threshold=confidence_threshold
                )
                logger.info("✅ Audio processor initialized with windowed inference")
                logger.info(f"   Window: {window_seconds}s, Hop: {hop_seconds}s, Aggregation: {aggregation_method}")
                logger.info(f"   Confidence threshold: {confidence_threshold} ({confidence_threshold*100:.0f}%)")
            except Exception as e:
                logger.warning(f"⚠️  Audio processor init failed: {e}")
                self.audio_processor = None
        
        self.setup_mqtt()
    
    def setup_mqtt(self):
        """Setup MQTT client connection"""
        self.mqtt_client = mqtt_client.Client(self.client_id)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Connect to local mosquitto broker (no TLS)
        try:
            logger.info(f"Connecting to local MQTT broker: {self.mqtt_broker}:{self.mqtt_port}")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()
            logger.info(f"✅ MQTT connected to {self.mqtt_broker}:{self.mqtt_port}")
        except Exception as e:
            logger.error(f"❌ MQTT connection failed: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ MQTT connected successfully")
            client.subscribe("hive/ml/control")
            client.subscribe("hive/audio/enable")
            client.subscribe("hive/audio/control")  # Subscribe to recording triggers
        else:
            logger.error(f"❌ MQTT connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle control messages and recording triggers"""
        try:
            payload = msg.payload.decode()
            logger.info(f"📨 Control message: {msg.topic} = {payload}")
            
            # Handle recording trigger from dashboard
            if msg.topic == "hive/audio/control":
                try:
                    import json
                    command_data = json.loads(payload)
                    if command_data.get('command') == 'record_and_classify':
                        self.recording_requested = True
                        self.recording_duration = command_data.get('duration_sec', 60)
                        logger.info(f"🎤 Recording requested: {self.recording_duration} seconds")
                except Exception as e:
                    logger.error(f"Error parsing recording command: {e}")
                    
        except Exception as e:
            logger.error(f"Message parse error: {e}")
    
    def run_audio_inference(self):
        """Run audio inference on-demand (triggered by dashboard)"""
        if not self.audio_processor:
            logger.warning("⚠️  Audio processor not available")
            return
        
        logger.info("🎤 Audio service ready (on-demand recording mode)")
        
        while self.is_running:
            try:
                # Wait for recording trigger from dashboard
                if self.recording_requested:
                    self.recording_requested = False
                    
                    logger.info(f"🎙️  Starting {self.recording_duration}s recording...")
                    
                    # Audio processor handles microphone input
                    results = self.audio_processor.record_and_classify(
                        duration_sec=self.recording_duration
                    )
                    
                    if results:
                        # Publish results to MQTT (config.TOPIC_AUDIO_RESULTS)
                        message = {
                            "timestamp": datetime.now().isoformat(),
                            "model_type": "audio_ml_classifier",
                            "results": results
                        }
                        
                        import json
                        self.mqtt_client.publish(
                            config.TOPIC_AUDIO_RESULTS,
                            json.dumps(message),
                            qos=1
                        )
                        logger.info(f"✅ Audio results published: {results.get('classification', 'unknown')}")
                    else:
                        logger.warning("⚠️  No audio results to publish")
                
            except Exception as e:
                logger.error(f"Audio inference error: {e}")
            
            # Small delay to prevent CPU maxing
            import time
            time.sleep(0.5)
    
    def run(self):
        """Main service loop"""
        logger.info("🚀 Audio Service starting...")
        
        try:
            self.run_audio_inference()
        except KeyboardInterrupt:
            logger.info("⏹️  Audio service stopped")
        except Exception as e:
            logger.error(f"❌ Audio service error: {e}")
        finally:
            self.is_running = False
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()


if __name__ == "__main__":
    service = AudioInferenceService()
    service.run()
