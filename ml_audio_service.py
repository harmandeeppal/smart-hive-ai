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
        self.demo_enabled = True   # toggled by hive/control {"sensor":"audio"}
        self.mqtt_client = None
        self.audio_processor = None
        self.recording_requested = False
        self.recording_duration = 30
        
        # Load configuration
        self.mqtt_broker = config.MQTT_BROKER
        self.mqtt_port = config.MQTT_PORT
        self.client_id = f"audio-service-{os.getenv('HOSTNAME', 'pi')}"
        
        # Initialize audio processor if available
        if AUDIO_AVAILABLE:
            try:
                # Use configured audio model path
                audio_model_path = getattr(config, 'AUDIO_MODEL_PATH', 'models/audio_model.pkl')
                self.audio_processor = AudioProcessor(audio_model_path)
                logger.info("✅ Audio processor initialized")
            except Exception as e:
                logger.warning(f"⚠️  Audio processor init failed: {e}")
                self.audio_processor = None
        
        self.setup_mqtt()
    
    def setup_mqtt(self):
        """Setup MQTT client connection"""
        self.mqtt_client = mqtt_client.Client(
            mqtt_client.CallbackAPIVersion.VERSION1, self.client_id
        )
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
            client.subscribe("hive/audio/control")
            client.subscribe("hive/control")   # dashboard sensor toggles
        else:
            logger.error(f"❌ MQTT connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle control messages and recording triggers"""
        try:
            payload = msg.payload.decode()
            logger.info(f"📨 Control message: {msg.topic} = {payload}")
            
            import json
            # Audio on/off toggle from dashboard
            if msg.topic == "hive/control":
                try:
                    cmd = json.loads(payload)
                    if cmd.get('sensor') == 'audio':
                        self.demo_enabled = cmd.get('state', 'on') == 'on'
                        logger.info(f"🎤 Audio demo {'enabled' if self.demo_enabled else 'paused'} via toggle")
                except Exception as e:
                    logger.error(f"Error parsing control command: {e}")

            # Recording trigger from dashboard
            if msg.topic == "hive/audio/control":
                try:
                    command_data = json.loads(payload)
                    if command_data.get('command') == 'record_and_classify':
                        self.recording_requested = True
                        self.recording_duration = command_data.get('duration_sec', 30)
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
    
    def _load_sample_audio(self):
        """Load bee colony WAV from demo/sample_audio/ if available."""
        import soundfile as sf
        from pathlib import Path
        sample_dir = Path(__file__).resolve().parent / "demo" / "sample_audio"
        if not sample_dir.exists():
            return None, None
        for ext in ("*.wav", "*.flac", "*.ogg"):
            paths = sorted(sample_dir.glob(ext))
            if paths:
                try:
                    audio, sr = sf.read(str(paths[0]), dtype="float32")
                    if audio.ndim > 1:
                        audio = audio[:, 0]
                    logger.info(f"🎵 Loaded sample audio: {paths[0].name} "
                                f"({len(audio)/sr:.0f}s at {sr} Hz)")
                    return audio, sr
                except Exception as e:
                    logger.warning(f"Could not load sample audio: {e}")
        return None, None

    def _synthetic_audio(self, duration: float, sr: int):
        """Fallback: generate synthetic bee-colony audio."""
        import math
        import numpy as np
        t = np.linspace(0, duration, int(sr * duration))
        hour = datetime.now().hour + datetime.now().minute / 60
        activity = max(0.1, math.sin((hour - 6) * math.pi / 12))
        freq = 250 + activity * 150
        audio = (
            0.4 * np.sin(2 * math.pi * freq * t)
            + 0.2 * np.sin(2 * math.pi * freq * 2 * t)
            + 0.1 * np.sin(2 * math.pi * freq * 3 * t)
            + 0.1 * np.random.normal(0, 0.1, len(t))
        ).astype(np.float32)
        audio /= np.max(np.abs(audio))
        return audio

    def _start_waveform_stream(self, playback: dict) -> None:
        """Background thread: publish 50-point real waveform packets every 0.5 s."""
        import threading, time, json
        import numpy as np

        INTERVAL   = 0.5        # seconds between packets
        N_POINTS   = 60         # samples per packet (scrolling window width)

        def _stream():
            while self.is_running:
                try:
                    audio = playback.get("audio")
                    sr    = playback.get("sr", 22050)
                    if self.demo_enabled and audio is not None:
                        offset      = playback["offset"]
                        win_samples = int(sr * INTERVAL)
                        total       = len(audio)
                        start       = offset % total
                        end         = start + win_samples
                        chunk = audio[start:end] if end <= total else np.concatenate([audio[start:], audio[:end - total]])

                        # Decimate: pick every k-th sample to get N_POINTS values
                        k = max(1, len(chunk) // N_POINTS)
                        samples = [round(float(chunk[i * k]), 4) for i in range(N_POINTS) if i * k < len(chunk)]

                        self.mqtt_client.publish(
                            config.TOPIC_AUDIO_WAVEFORM,
                            json.dumps({"samples": samples}),
                            qos=0,
                        )
                except Exception as e:
                    logger.debug(f"Waveform stream error: {e}")
                time.sleep(INTERVAL)

        t = threading.Thread(target=_stream, daemon=True)
        t.start()

    def run_demo_mode(self):
        """Run continuous audio classification without a microphone.

        Plays back demo/sample_audio/bee_colony_demo.wav in 30-second chunks.
        Falls back to synthetic sine-wave audio if no file is found.
        """
        import json
        import time
        import numpy as np

        logger.info("🎭 Audio service running in DEMO MODE (no microphone required)")

        CHUNK_DURATION = 30  # seconds per classification window
        sample_audio, file_sr = self._load_sample_audio()

        # Resample to model's sample rate if needed
        if sample_audio is not None and self.audio_processor:
            target_sr = self.audio_processor.sample_rate
            if file_sr != target_sr:
                import librosa
                sample_audio = librosa.resample(sample_audio, orig_sr=file_sr, target_sr=target_sr)
                logger.info(f"Resampled audio to {target_sr} Hz")

        audio_offset = 0

        # Share playback position with waveform thread via mutable container
        playback = {"offset": 0, "audio": sample_audio, "sr": self.audio_processor.sample_rate if self.audio_processor else 22050}
        self._start_waveform_stream(playback)

        while self.is_running:
            if not self.demo_enabled:
                import time as _t; _t.sleep(1)
                continue
            try:
                if self.audio_processor and self.audio_processor.model:
                    sr = self.audio_processor.sample_rate
                    chunk_samples = int(sr * CHUNK_DURATION)

                    if sample_audio is not None:
                        total = len(sample_audio)
                        start = audio_offset % total
                        end = start + chunk_samples
                        if end <= total:
                            chunk = sample_audio[start:end]
                        else:
                            chunk = np.concatenate([sample_audio[start:], sample_audio[:end - total]])
                        audio_offset = (audio_offset + chunk_samples) % total
                        playback["offset"] = audio_offset
                        source = "demo_audio_file"
                    else:
                        chunk = self._synthetic_audio(CHUNK_DURATION, sr)
                        source = "demo_synthetic"

                    features = self.audio_processor.extract_features(chunk)
                    if features is not None:
                        result = self.audio_processor.classify(features)
                        message = {
                            "timestamp": datetime.now().isoformat(),
                            "model_type": "audio_ml_classifier",
                            "source": source,
                            "results": result,
                        }
                        self.mqtt_client.publish(
                            config.TOPIC_AUDIO_RESULTS,
                            json.dumps(message),
                            qos=1,
                        )
                        logger.info(
                            f"🎭 Demo audio ({source}): {result.get('classification')} "
                            f"(conf {result.get('confidence', 0):.2f})"
                        )
            except Exception as e:
                logger.error(f"Demo mode audio error: {e}")

            time.sleep(CHUNK_DURATION)

    def run(self):
        """Main service loop"""
        logger.info("🚀 Audio Service starting...")

        try:
            if os.getenv('DEMO_MODE', 'false').lower() == 'true':
                self.run_demo_mode()
            else:
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
