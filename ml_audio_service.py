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
        
        # Load configuration
        self.mqtt_broker = config.MQTT_BROKER
        self.mqtt_port = config.MQTT_PORT
        self.client_id = f"audio-service-{os.getenv('HOSTNAME', 'pi')}"
        
        # Initialize audio processor if available
        if AUDIO_AVAILABLE:
            try:
                self.audio_processor = AudioProcessor()
                logger.info("✅ Audio processor initialized")
            except Exception as e:
                logger.warning(f"⚠️  Audio processor init failed: {e}")
                self.audio_processor = None
        
        self.setup_mqtt()
    
    def setup_mqtt(self):
        """Setup MQTT client connection"""
        self.mqtt_client = mqtt_client.Client(self.client_id)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        
        # Setup TLS
        try:
            self.mqtt_client.tls_set(
                ca_certs=config.CA_CERT,
                certfile=config.CERT_FILE,
                keyfile=config.KEY_FILE,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2,
                ciphers=None
            )
            self.mqtt_client.tls_insecure_set(False)
        except Exception as e:
            logger.warning(f"TLS setup failed: {e}")
        
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()
            logger.info(f"✅ MQTT connected to {self.mqtt_broker}")
        except Exception as e:
            logger.error(f"❌ MQTT connection failed: {e}")
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("✅ MQTT connected successfully")
            client.subscribe("hive/ml/control")
            client.subscribe("hive/audio/enable")
        else:
            logger.error(f"❌ MQTT connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle control messages"""
        try:
            payload = msg.payload.decode()
            logger.info(f"📨 Control message: {msg.topic} = {payload}")
        except Exception as e:
            logger.error(f"Message parse error: {e}")
    
    def run_audio_inference(self):
        """Run continuous audio inference"""
        if not self.audio_processor:
            logger.warning("⚠️  Audio processor not available")
            return
        
        logger.info("🎤 Starting audio inference loop...")
        
        while self.is_running:
            try:
                # Audio processor handles microphone input
                results = self.audio_processor.process_audio()
                
                if results:
                    # Publish results to MQTT
                    message = {
                        "timestamp": datetime.now().isoformat(),
                        "model_type": "audio",
                        "results": results
                    }
                    
                    import json
                    self.mqtt_client.publish(
                        "hive/audio/results",
                        json.dumps(message),
                        qos=1
                    )
                    logger.debug(f"✅ Audio results published")
                
            except Exception as e:
                logger.error(f"Audio inference error: {e}")
            
            # Small delay to prevent CPU maxing
            import time
            time.sleep(0.1)
    
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
