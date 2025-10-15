"""
Smart Hive AI - Mock Hardware Components

Description:
    Provides mock implementations of hardware sensors for development and testing
    without requiring physical Raspberry Pi hardware. Simulates realistic sensor
    readings for BME280 (temperature/humidity), LIS3DH (vibration), INMP441 (sound),
    and vision processing components.

Author: Smart Hive AI Team
Created: 2024
Last Modified: October 2025

Dependencies:
    - numpy: For numerical simulations
    - opencv-python: For mock camera frames

Mock Components:
    - MockBME280: Temperature and humidity sensor
    - MockLIS3DH: Vibration/accelerometer sensor
    - MockINMP441: Sound level and frequency sensor
    - MockVisionProcessor: AI-powered queen bee detection

Usage:
    from mock_components import MockBME280, MockLIS3DH, MockINMP441, MockVisionProcessor
    
    sensor = MockBME280()
    temp, humidity = sensor.get_temp_humidity()
"""

import time
import random
import numpy as np
import cv2


class MockBME280:
    """
    Mock implementation of BME280 temperature and humidity sensor.
    
    Simulates realistic beehive brood chamber conditions with slight
    random variations to mimic real sensor readings.
    
    Attributes:
        temperature (float): Base temperature in Celsius (typical: 34.5C)
        humidity (float): Base humidity percentage (typical: 58%)
    
    Example:
        >>> sensor = MockBME280()
        >>> temp, humidity = sensor.get_temp_humidity()
        >>> print(f"Temperature: {temp}C, Humidity: {humidity}%")
    """
    
    def __init__(self):
        """Initialize mock BME280 sensor with typical hive conditions."""
        print("Initialized Mock BME280 Sensor.")
        self.temperature = 34.5  # Realistic brood temperature in Celsius
        self.humidity = 58.0     # Realistic humidity percentage

    def get_temp_humidity(self):
        """
        Get simulated temperature and humidity readings.
        
        Returns:
            tuple: (temperature, humidity) in (Celsius, percentage)
                  Temperature range: 34.3-34.7C
                  Humidity range: 57.0-59.0%
        """
        # Simulate slight variations in sensor readings
        temp = 34.5 + random.uniform(-0.2, 0.2)
        hum = 58.0 + random.uniform(-1.0, 1.0)

        return (round(temp, 2), round(hum, 2))


class MockLIS3DH:
    """
    Mock implementation of LIS3DH accelerometer/vibration sensor.
    
    Simulates beehive vibration patterns with baseline activity and
    occasional spikes to represent bee movement and wing fanning.
    
    Example:
        >>> sensor = MockLIS3DH()
        >>> vibration = sensor.get_rms_acceleration()
        >>> print(f"Vibration RMS: {vibration}")
    """
    
    def __init__(self):
        """Initialize mock LIS3DH sensor."""
        print("Initialized Mock LIS3DH Sensor.")

    def get_rms_acceleration(self):
        """
        Get simulated RMS (Root Mean Square) acceleration reading.
        
        Returns:
            float: RMS acceleration value
                  Baseline: 0.04-0.06
                  Spikes: 0.15-0.35 (5% probability)
        """
        # Simulate a baseline vibration level with occasional spikes
        base_vibration = 0.05
        if random.random() < 0.05:  # 5% chance of a spike
            return round(base_vibration + random.uniform(0.1, 0.3), 4)
        return round(base_vibration + random.uniform(-0.01, 0.01), 4)


class MockINMP441:
    """
    Mock implementation of INMP441 I2S microphone.
    
    Simulates beehive sound levels and frequency analysis for detecting
    hive activity patterns and potential issues.
    
    Example:
        >>> sensor = MockINMP441()
        >>> db_level = sensor.get_db_level()
        >>> frequency = sensor.get_dominant_frequency()
    """
    
    def __init__(self):
        """Initialize mock INMP441 sound sensor."""
        print("Initialized Mock INMP441 Sound Sensor.")
    
    def get_db_level(self):
        """
        Get simulated sound level in decibels.
        
        Returns:
            float: Sound level in dB (range: 49-55 dB)
                  Normal hive hum: 52 dB +/- 3 dB
        """
        # Simulate a baseline hive hum
        return round(52 + random.uniform(-3, 3), 1)
    
    def get_dominant_frequency(self):
        """
        Get simulated dominant frequency in Hz.
        
        Simulates different hive states based on frequency patterns:
        - Normal hive: 200-300 Hz (healthy hum)
        - Queenless roar: 350-450 Hz (high-pitched distress)
        - Swarming signals: 450-550 Hz (piping/quacking)
        
        Returns:
            float: Dominant frequency in Hz (range: 200-550 Hz)
        """
        # Most of the time, simulate normal frequency
        if random.random() < 0.8:  # 80% normal
            return round(random.uniform(200, 320), 1)
        elif random.random() < 0.9:  # 10% queenless roar
            return round(random.uniform(350, 450), 1)
        else:  # 10% swarming signals
            return round(random.uniform(450, 550), 1)


class MockCamera:
    """
    Mock implementation of Raspberry Pi Camera.
    
    Generates blank frames with timestamp overlay for testing without
    physical camera hardware.
    
    Example:
        >>> camera = MockCamera()
        >>> frame = camera.capture_frame()
    """
    
    def __init__(self):
        """Initialize mock camera."""
        print("Initialized Mock Camera.")
    
    def capture_frame(self):
        """
        Capture a mock camera frame.
        
        Returns:
            numpy.ndarray: 640x480 BGR image with timestamp overlay
        """
        # Create a blank image with a timestamp
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        text = f"MOCK CAMERA FEED: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        cv2.putText(frame, text, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame


class MockVisionProcessor:
    """
    Mock implementation of TensorFlow Lite vision processor.
    
    Simulates AI-powered queen bee detection with configurable detection
    probability for testing without real TFLite model inference.
    
    Attributes:
        model_path (str): Path to TFLite model file (not actually loaded in mock)
        last_detection_time (float): Timestamp of last queen detection
    
    Example:
        >>> processor = MockVisionProcessor(model_path="models/queen_bee.tflite")
        >>> frame, detected, confidence = processor.process_frame()
    """
    def __init__(self, model_path):
        print(f"Initialized Mock Vision Processor with model: {model_path}")
        self.frame = None

    def detect_queen(self, frame):
        """Simulates queen bee detection on a given frame."""
        # Simulate a 20% chance of 'detecting' a queen
        if random.random() < 0.2:
            # Define a bounding box in normalized coordinates [ymin, xmin, ymax, xmax]
            box = [0.45, 0.45, 0.55, 0.55]
            confidence = round(random.uniform(0.85, 0.99), 2)
            
            # Draw a green box on the frame to visualize the detection
            h, w, _ = frame.shape
            x_min, y_min = int(box[1] * w), int(box[0] * h)
            x_max, y_max = int(box[3] * w), int(box[2] * h)
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
            
            print(f"Mock Detection: Queen found with confidence {confidence}")
            return (box, confidence)
        else:
            return (None, None)

    def capture_and_process_frame(self):
        """
        Simulates capturing a frame, running detection, and returning the annotated frame.
        """
        # Create a blank black image
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Run mock detection and draw box if a queen is 'found'
        detection_result = self.detect_queen(self.frame)

        # Put timestamp on the image
        cv2.putText(self.frame, f"MOCK FEED: {timestamp}", (20, 460), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return self.frame, detection_result
