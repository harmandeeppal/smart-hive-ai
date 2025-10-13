# mock_sensors.py
# This file simulates the hardware sensors for development on a laptop.

import time
import random
import numpy as np
import cv2

class MockVisionProcessor:
    # ... (keep the __init__ and detect_queen methods) ...

    def capture_frame(self):
        """Simulates capturing a frame by creating a blank image."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        text = f"MOCK CAMERA FEED: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        cv2.putText(frame, text, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame



class MockSHT31:
    """A mock SHT31 temperature and humidity sensor."""
    def __init__(self):
        print("Initialized Mock SHT31 Sensor.")
        self.temperature = 34.5  # Realistic brood temperature in °C
        self.humidity = 58.0     # Realistic humidity in %

    def get_temp_humidity(self):
        # Return slightly varied data to simulate real readings
        temp = self.temperature + random.uniform(-0.2, 0.2)
        hum = self.humidity + random.uniform(-1.0, 1.0)
        return (round(temp, 2), round(hum, 2))

class MockMPU6050:
    """A mock MPU-6050 vibration sensor."""
    def __init__(self):
        print("Initialized Mock MPU-6050 Sensor.")

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
        # Simulate a baseline hive hum
        return round(52 + random.uniform(-3, 3), 1)

class MockCamera:
    """A mock Raspberry Pi Camera."""
    def __init__(self):
        print("Initialized Mock Camera.")
    
    def capture_frame(self):
        # In a real scenario, this would return an OpenCV image (NumPy array).
        # For simulation, we can just return a placeholder.
        print("Mock frame captured.")
        return "dummy_image_frame_data"

# In mock_components.py, add this class:
class MockVisionProcessor:
    """
    A mock Vision Processor that simulates YOLOv5 TFLite inference
    and generates a mock video frame.
    """
    def __init__(self, model_path):
        print(f"Initialized Mock Vision Processor with model: {model_path}")
        self.frame = None

    def detect_queen(self, frame):
        """Simulates queen bee detection on a given frame."""
        if random.random() < 0.2:
            box = [0.45, 0.45, 0.55, 0.55]
            confidence = round(random.uniform(0.85, 0.99), 2)
            # Draw a green box on the frame to simulate detection
            h, w, _ = frame.shape
            x_min, y_min = int(box[0] * w), int(box[1] * h)
            x_max, y_max = int(box[2] * w), int(box[3] * h)
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
        
        # Run detection and draw box if found
        detection_result = self.detect_queen(self.frame)

        # Put timestamp on the image
        cv2.putText(self.frame, f"MOCK FEED: {timestamp}", (20, 460), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return self.frame, detection_result

        return self.frame