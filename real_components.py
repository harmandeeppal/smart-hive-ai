# real_components.py
import board
import adafruit_bme280
import adafruit_lis3dh
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import sounddevice as sd

class RealINMP441:
    """Interface for a real microphone using sounddevice."""
    def __init__(self, sample_rate=44100, duration_ms=100):
        self.sample_rate = sample_rate
        self.duration_ms = duration_ms
        self.is_working = True
        try:
            # Check if any microphone is available
            if len(sd.query_devices(kind='input')) == 0:
                raise RuntimeError("No microphone found.")
            print("Successfully initialized Real INMP441 (Microphone).")
        except Exception as e:
            print(f"Error initializing Real INMP441: {e}")
            self.is_working = False

    def get_db_level(self):
        if not self.is_working:
            return -100.0 # Return a very low dB value on error

        try:
            # Record audio for a short duration
            recording = sd.rec(int(self.duration_ms / 1000 * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32')
            sd.wait()  # Wait for recording to complete

            # Calculate RMS (Root Mean Square) of the audio signal
            rms = np.sqrt(np.mean(recording**2))

            # Convert RMS to dB. Add a small epsilon to avoid log(0).
            db = 20 * np.log10(rms + 1e-12)
            
            return db
        except Exception as e:
            print(f"Error reading from microphone: {e}")
            return -100.0

class RealBME280:
    """Interface for the real BME280 sensor."""
    def __init__(self):
        try:
            i2c = board.I2C()
            self.sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c)
            print("Successfully initialized Real BME280 Sensor.")
        except Exception as e:
            print(f"Error initializing Real BME280: {e}")
            self.sensor = None
    
    def get_temp_humidity(self):
        if self.sensor:
            return (self.sensor.temperature, self.sensor.humidity)
        return (0.0, 0.0) # Return default values on error

class RealLIS3DH:
    """Interface for the real LIS3DH sensor."""
    def __init__(self):
        try:
            i2c = board.I2C()
            self.sensor = adafruit_lis3dh.LIS3DH_I2C(i2c)
            print("Successfully initialized Real LIS3DH Sensor.")
        except Exception as e:
            print(f"Error initializing Real LIS3DH: {e}")
            self.sensor = None

    def get_rms_acceleration(self):
        if self.sensor:
            x, y, z = self.sensor.acceleration
            rms = np.sqrt(x**2 + y**2 + z**2)
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