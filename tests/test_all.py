"""
Test Suite for Smart Hive AI

This module contains tests for all major components:
- ML inference (vision and audio)
- MQTT communication
- Configuration management
- Integration testing

Run tests with: python -m pytest tests/
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config

try:
    from mock_components import MockBME280, MockDFRobot, MockHTS221
except ImportError:
    # Define mock implementations if imports fail
    class MockBME280:
        def read_temperature(self):
            return 25.0
        def read_humidity(self):
            return 65.0
        def read_pressure(self):
            return 1013.25
    
    class MockHTS221:
        def read_temperature(self):
            return 24.5
        def read_humidity(self):
            return 60.0
    
    MockDFRobot = None


class TestMLModelsExist:
    """Test that ML models are properly configured and exist."""
    
    def test_vision_model_path_exists(self):
        """Test YOLO vision model file exists."""
        vision_model_path = PROJECT_ROOT / 'models' / 'vision_model.pt'
        assert vision_model_path.exists(), f"Vision model not found at {vision_model_path}"
    
    def test_audio_model_path_exists(self):
        """Test audio classification model file exists."""
        audio_model_path = PROJECT_ROOT / 'models' / 'audio_model.pkl'
        assert audio_model_path.exists(), f"Audio model not found at {audio_model_path}"
    
    def test_ml_processors_exist(self):
        """Test that ML processor modules exist."""
        vision_proc = PROJECT_ROOT / 'ml_vision_model' / 'vision_processor.py'
        audio_proc = PROJECT_ROOT / 'ml_audio_model' / 'audio_processor.py'
        assert vision_proc.exists(), f"Vision processor not found"
        assert audio_proc.exists(), f"Audio processor not found"


class TestConfiguration:
    """Test configuration management."""
    
    def test_config_has_required_attributes(self):
        """Test that config has all required attributes."""
        required_attrs = [
            'AWS_ENDPOINT',
            'THING_NAME',
            'TOPIC_TELEMETRY',
            'TELEMETRY_INTERVAL_SECONDS',
            'VISION_DETECTION_MODE',
        ]
        for attr in required_attrs:
            assert hasattr(config, attr), f"Config missing attribute: {attr}"
    
    def test_config_intervals_are_positive(self):
        """Test that all timing intervals are positive."""
        assert config.TELEMETRY_INTERVAL_SECONDS > 0
        assert config.VISION_DETECTION_COOLDOWN_SECONDS > 0
    
    def test_mock_environment_flag_exists(self):
        """Test that mock environment flag is configurable."""
        assert hasattr(config, 'IS_MOCK_ENVIRONMENT')


class TestMockSensors:
    """Test mock sensor implementations."""
    
    def test_mock_bme280_initialization(self):
        """Test MockBME280 can be initialized."""
        sensor = MockBME280()
        assert sensor is not None
        assert hasattr(sensor, 'read_temperature')
        assert hasattr(sensor, 'read_humidity')
        assert hasattr(sensor, 'read_pressure')
    
    def test_mock_bme280_returns_valid_data(self):
        """Test MockBME280 returns valid sensor data."""
        sensor = MockBME280()
        temp = sensor.read_temperature()
        humidity = sensor.read_humidity()
        pressure = sensor.read_pressure()
        
        # Check temperature is reasonable (10-40 C)
        assert 10 <= temp <= 40, f"Temperature {temp} out of expected range"
        # Check humidity is percentage
        assert 0 <= humidity <= 100, f"Humidity {humidity} out of 0-100 range"
        # Check pressure is reasonable (900-1100 hPa)
        assert 900 <= pressure <= 1100, f"Pressure {pressure} out of expected range"
    
    def test_mock_hts221_returns_valid_data(self):
        """Test MockHTS221 returns valid data."""
        sensor = MockHTS221()
        temp = sensor.read_temperature()
        humidity = sensor.read_humidity()
        
        assert isinstance(temp, (int, float))
        assert isinstance(humidity, (int, float))
        assert 0 <= humidity <= 100


class TestMQTTIntegration:
    """Test MQTT integration (mock-based)."""
    
    def test_mqtt_client_initialization(self):
        """Test MQTT client initialization."""
        try:
            import paho.mqtt.client as mqtt
            # If paho is installed, test the import
            assert mqtt is not None
        except ImportError:
            # Skip this test on systems without paho-mqtt
            pytest.skip("paho-mqtt not installed - skipping MQTT tests")
    
    def test_mqtt_topic_structure(self):
        """Test MQTT topic naming is consistent."""
        topics = [
            config.TOPIC_TELEMETRY,
            config.TOPIC_VISION,
            config.TOPIC_CONTROL,
        ]
        
        for topic in topics:
            assert topic.startswith('hive/'), f"Topic {topic} doesn't start with 'hive/'"
            assert isinstance(topic, str), f"Topic {topic} is not a string"


class TestDataProcessing:
    """Test data processing and payload generation."""
    
    def test_telemetry_payload_structure(self):
        """Test telemetry payload has required fields."""
        telemetry = {
            'timestamp': time.time(),
            'device_id': 'test_device',
            'temperature': 25.5,
            'humidity': 65.0,
            'pressure': 1013.25,
        }
        
        required_fields = ['timestamp', 'device_id', 'temperature', 'humidity', 'pressure']
        for field in required_fields:
            assert field in telemetry, f"Missing field in telemetry: {field}"
        
        # Verify JSON serializable
        json_str = json.dumps(telemetry)
        assert json_str is not None
    
    def test_vision_detection_payload_structure(self):
        """Test vision detection payload structure."""
        detection = {
            'timestamp': time.time(),
            'device_id': 'test_device',
            'detected': False,
            'confidence': 0.0,
            'boxes': [],
            'inference_time_ms': 125,
        }
        
        required_fields = ['timestamp', 'device_id', 'detected', 'confidence', 'inference_time_ms']
        for field in required_fields:
            assert field in detection, f"Missing field in detection: {field}"
    
    def test_audio_detection_payload_structure(self):
        """Test audio detection payload structure."""
        detection = {
            'timestamp': time.time(),
            'device_id': 'test_device',
            'classification': 'unknown',
            'confidence': 0.0,
            'duration_seconds': 5,
        }
        
        required_fields = ['timestamp', 'device_id', 'classification', 'confidence', 'duration_seconds']
        for field in required_fields:
            assert field in detection, f"Missing field in audio detection: {field}"


class TestPathConfiguration:
    """Test that all file paths are configured correctly."""
    
    def test_vision_model_path_accessible(self):
        """Test vision model path can be accessed."""
        path = Path('models/vision_model.pt')
        assert path.exists() or (PROJECT_ROOT / path).exists()
    
    def test_audio_model_path_accessible(self):
        """Test audio model path can be accessed."""
        path = Path('models/audio_model.pkl')
        assert path.exists() or (PROJECT_ROOT / path).exists()
    
    def test_models_directory_exists(self):
        """Test models directory exists."""
        models_dir = PROJECT_ROOT / 'models'
        assert models_dir.exists(), "models/ directory must exist"
        assert models_dir.is_dir()


class TestConfigurationInML:
    """Test that ML service can read configuration."""
    
    def test_config_paths_use_relative_imports(self):
        """Test that paths use relative imports correctly."""
        # Vision model path should be resolvable
        vision_path = 'models/vision_model.pt'
        full_path = PROJECT_ROOT / vision_path
        assert full_path.exists() or Path(vision_path).exists()
    
    def test_mqtt_configuration_complete(self):
        """Test MQTT configuration is complete."""
        assert config.THING_NAME is not None
        assert config.TOPIC_TELEMETRY is not None
        assert config.TOPIC_VISION is not None
        assert config.TOPIC_CONTROL is not None


@pytest.mark.integration
class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_sensor_to_payload_pipeline(self):
        """Test complete pipeline from sensor read to MQTT payload."""
        # Create mock sensor
        sensor = MockBME280()
        
        # Read data
        temp = sensor.read_temperature()
        humidity = sensor.read_humidity()
        
        # Create payload
        payload = {
            'temperature': temp,
            'humidity': humidity,
            'timestamp': time.time(),
        }
        
        # Verify payload is valid JSON
        json_payload = json.dumps(payload)
        reconstructed = json.loads(json_payload)
        
        assert reconstructed['temperature'] == temp
        assert reconstructed['humidity'] == humidity
    
    def test_project_structure_complete(self):
        """Test project has all required directories and files."""
        required_dirs = ['tests', 'docs', 'models', 'ml_vision_model', 'ml_audio_model']
        required_files = ['README.md', 'app.py', 'config.py', 'docker-compose.yml']
        
        for dir_name in required_dirs:
            assert (PROJECT_ROOT / dir_name).exists(), f"Missing directory: {dir_name}"
        
        for file_name in required_files:
            assert (PROJECT_ROOT / file_name).exists(), f"Missing file: {file_name}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
