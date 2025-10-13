# real_components.py
import board
import adafruit_sht31d
import adafruit_mpu6050
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite

class RealSHT31:
    """Interface for the real SHT31 sensor."""
    def __init__(self):
        try:
            i2c = board.I2C()
            self.sensor = adafruit_sht31d.SHT31D(i2c)
            print("Successfully initialized Real SHT31 Sensor.")
        except Exception as e:
            print(f"Error initializing Real SHT31: {e}")
            self.sensor = None
    
    def get_temp_humidity(self):
        if self.sensor:
            return (self.sensor.temperature, self.sensor.relative_humidity)
        return (0.0, 0.0) # Return default values on error

class RealMPU6050:
    """Interface for the real MPU-6050 sensor."""
    def __init__(self):
        try:
            i2c = board.I2C()
            self.sensor = adafruit_mpu6050.MPU6050(i2c)
            print("Successfully initialized Real MPU-6050 Sensor.")
        except Exception as e:
            print(f"Error initializing Real MPU-6050: {e}")
            self.sensor = None

    def get_rms_acceleration(self):
        if self.sensor:
            x, y, z = self.sensor.acceleration
            rms = np.sqrt((x**2 + y**2 + z**2) / 3)
            return rms
        return 0.0

class RealVisionProcessor:
    def __init__(self, model_path):
        try:
            self.camera = cv2.VideoCapture(0)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            self.interpreter = tflite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            # --- NEW: Get model input size ---
            self.input_height = self.input_details[0]['shape'][1]
            self.input_width = self.input_details[0]['shape'][2]

            self.frame = None # To store the latest frame
            print("Successfully initialized Real Vision Processor.")
        except Exception as e:
            # ... (error handling) ...

    def capture_and_process_frame(self):
        if not self.camera or not self.camera.isOpened():
            return np.zeros((480, 640, 3), dtype=np.uint8)

        ret, frame = self.camera.read()
        if not ret:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        # --- NEW: Full Inference Pipeline ---
        # 1. Pre-process the frame
        input_data = cv2.resize(frame, (self.input_width, self.input_height))
        input_data = np.expand_dims(input_data, axis=0) # Add batch dimension

        # 2. Set the tensor
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)

        # 3. Run inference
        self.interpreter.invoke()

        # 4. Get results and post-process
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]
        
        detection_result = (None, None)

        # (Assuming Queen Bee is class 0, and you'll need a labels file)
        for i in range(len(scores)):
            if scores[i] > 0.5: # Confidence threshold
                detection_result = (boxes[i], scores[i])
                y_min, x_min, y_max, x_max = boxes[i]
                
                # Convert from normalized to pixel coordinates
                (left, right, top, bottom) = (x_min * 640, x_max * 640, 
                                              y_min * 480, y_max * 480)
                
                # Draw bounding box and label
                cv2.rectangle(frame, (int(left), int(top)), (int(right), int(bottom)), (0, 255, 0), 2)
                label = f"Queen: {int(scores[i]*100)}%"
                cv2.putText(frame, label, (int(left), int(top) - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                break # Assume only one queen, take the highest score

        self.frame = frame # Store the annotated frame
        return self.frame, detection_result