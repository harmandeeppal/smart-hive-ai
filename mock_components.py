# mock_components.py
# This file simulates the hardware sensors for development on a laptop.

import time
import random
import numpy as np
import cv2

class MockBME280:
    """A mock BME280 temperature and humidity sensor."""
    def __init__(self):
        print("Initialized Mock BME280 Sensor.")
        self.temperature = 34.5  # Realistic brood temperature in °C
        self.humidity = 58.0     # Realistic humidity in %

    def get_temp_humidity(self):
        # To test different dashboard statuses, you can modify these values.
        # Example:
        # temp = 38.5 # Too Hot
        # temp = 29.0 # Too Cold
        temp = 34.5 + random.uniform(-0.2, 0.2)
        hum = 58.0 + random.uniform(-1.0, 1.0)

        return (round(temp, 2), round(hum, 2))

class MockLIS3DH:
    """A mock LIS3DH vibration sensor."""
    def __init__(self):
        print("Initialized Mock LIS3DH Sensor.")

    def get_rms_acceleration(self):
        # Simulate a baseline vibration level with occasional spikes
        base_vibration = 0.05
        if random.random() < 0.05: # 5% chance of a spike
            return round(base_vibration + random.uniform(0.1, 0.3), 4)
        return round(base_vibration + random.uniform(-0.01, 0.01), 4)

class MockINMP441:
    """A mock INMP441 I2S microphone."""
    def __init__(self):
        print("Initialized Mock INMP441 Sound Sensor.")
    
    def get_db_level(self):
        """Simulate volume level in decibels (40-70 dB range for normal hive)."""
        # Simulate a baseline hive hum
        return round(52 + random.uniform(-3, 3), 1)
    
    def get_dominant_frequency(self):
        """Simulate dominant frequency in Hz.
        
        Normal hive: 200-300 Hz (healthy hum)
        Queenless roar: 350-450 Hz (high-pitched distress)
        Swarming signals: 450-550 Hz (piping/quacking)
        """
        # Most of the time, simulate normal frequency
        if random.random() < 0.8:  # 80% normal
            return round(random.uniform(200, 320), 1)
        elif random.random() < 0.9:  # 10% queenless roar
            return round(random.uniform(350, 450), 1)
        else:  # 10% swarming signals
            return round(random.uniform(450, 550), 1)

class MockCamera:
    """A mock Raspberry Pi Camera."""
    def __init__(self):
        print("Initialized Mock Camera.")
    
    def capture_frame(self):
        # In a real scenario, this would return an OpenCV image (NumPy array).
        # For simulation, we create a blank image with a timestamp.
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        text = f"MOCK CAMERA FEED: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        cv2.putText(frame, text, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame

class MockVisionProcessor:
    """
    A mock Vision Processor that simulates TFLite inference
    and generates a mock video frame.
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
