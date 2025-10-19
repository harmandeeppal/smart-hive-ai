"""
Smart Hive AI - Real Hardware Components

Description:
    Production implementations of hardware sensor interfaces for Raspberry Pi.
    Provides real BME280 (temperature/humidity), LIS3DH (vibration), INMP441 (sound),
    and TensorFlow Lite vision processing components.

Author: Smart Hive AI Team
Created: 2024
Last Modified: October 2025

Dependencies:
    - adafruit-circuitpython-bme280: BME280 sensor library
    - adafruit-circuitpython-lis3dh: LIS3DH accelerometer library
    - tflite-runtime: TensorFlow Lite inference engine
    - opencv-python: Computer vision operations
    - sounddevice: Audio capture from USB microphone
    - scipy: Signal processing and FFT analysis

Hardware Requirements:
    - BME280 sensor connected via I2C (address 0x76)
    - LIS3DH sensor connected via I2C (address 0x19)
    - USB microphone (Samson or compatible)
    - USB webcam (Logitech C270 or compatible)

Usage:
    from real_components import RealBME280, RealLIS3DH, RealINMP441, RealVisionProcessor
    
    temp_sensor = RealBME280()
    temperature, humidity = temp_sensor.get_temp_humidity()
"""

import board
import busio
import adafruit_bme280.advanced as adafruit_bme280
import adafruit_lis3dh
import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
import sounddevice as sd
from scipy.fft import fft, fftfreq
import config


class RealINMP441:
    """
    Real INMP441 I2S microphone interface using USB audio capture.
    
    Captures audio data from USB microphone and performs sound level (dB)
    and frequency analysis for beehive acoustic monitoring.
    
    Attributes:
        sample_rate (int): Audio sampling rate in Hz
        duration_ms (int): Recording duration for dB analysis in milliseconds
        freq_duration_sec (float): Recording duration for frequency analysis in seconds
        is_working (bool): Sensor operational status
    
    Example:
        >>> sensor = RealINMP441()
        >>> db_level = sensor.get_db_level()
        >>> frequency = sensor.get_dominant_frequency()
    """
    
    def __init__(self, sample_rate=None, duration_ms=None):
        """
        Initialize microphone interface.
        
        Args:
            sample_rate (int, optional): Sampling rate in Hz. Defaults to config value.
            duration_ms (int, optional): Recording duration in ms. Defaults to config value.
        """
        self.sample_rate = sample_rate or config.MICROPHONE_SAMPLE_RATE
        self.duration_ms = duration_ms or config.MICROPHONE_DURATION_MS
        self.freq_duration_sec = config.MICROPHONE_FREQ_DURATION_SEC
        self.is_working = True
        try:
            # Check if any microphone is available
            if len(sd.query_devices(kind='input')) == 0:
                raise RuntimeError("No microphone found.")
            print(f"Successfully initialized Real INMP441 (Microphone) at {self.sample_rate} Hz.")
        except Exception as e:
            print(f"Error initializing Real INMP441: {e}")
            self.is_working = False

    def get_db_level(self):
        """
        Measure sound level in decibels.
        
        Records a short audio sample and calculates RMS (Root Mean Square)
        to determine sound pressure level in decibels.
        
        Returns:
            float: Sound level in dB (range: 40-70 dB for normal hive)
                  Returns -100.0 if microphone is not working
        """
        if not self.is_working:
            return -100.0  # Return a very low dB value on error

        try:
            # Record audio for a short duration
            recording = sd.rec(int(self.duration_ms / 1000 * self.sample_rate), 
                             samplerate=self.sample_rate, channels=1, dtype='float32')
            sd.wait()  # Wait for recording to complete

            # Calculate RMS (Root Mean Square) of the audio signal
            rms = np.sqrt(np.mean(recording**2))

            # Convert RMS to dB. Add a small epsilon to avoid log(0).
            db = 20 * np.log10(rms + 1e-12)
            
            # Scale to typical range (40-70 dB for normal hive sounds)
            # Adjust offset based on your microphone's sensitivity
            db = max(40.0, min(70.0, db + 80))  # Offset adjustment
            
            return float(db)
        except Exception as e:
            print(f"Error reading from microphone: {e}")
            return -100.0

    def get_dominant_frequency(self):
        """Get the dominant frequency in Hz using FFT analysis."""
        if not self.is_working:
            return 0.0

        try:
            # Record audio for frequency analysis (need longer duration for better resolution)
            recording = sd.rec(int(self.freq_duration_sec * self.sample_rate), samplerate=self.sample_rate, channels=1, dtype='float32')
            sd.wait()

            # Flatten the recording to 1D array
            audio_data = recording.flatten()

            # Apply FFT (Fast Fourier Transform)
            fft_values = fft(audio_data)
            fft_freqs = fftfreq(len(audio_data), 1 / self.sample_rate)

            # Get positive frequencies only
            positive_freqs = fft_freqs[:len(fft_freqs)//2]
            fft_magnitudes = np.abs(fft_values[:len(fft_values)//2])

            # Find the dominant frequency (highest magnitude)
            # Focus on bee-relevant range: 100-1000 Hz
            relevant_range = (positive_freqs >= 100) & (positive_freqs <= 1000)
            if np.any(relevant_range):
                relevant_freqs = positive_freqs[relevant_range]
                relevant_mags = fft_magnitudes[relevant_range]
                dominant_idx = np.argmax(relevant_mags)
                dominant_freq = relevant_freqs[dominant_idx]
            else:
                dominant_freq = 0.0

            return float(dominant_freq)
        except Exception as e:
            print(f"Error analyzing frequency: {e}")
            return 0.0

class RealBME280:
    """Interface for the real BME280 sensor."""
    def __init__(self, address=None):
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            address = address or config.BME280_ADDRESS
            self.sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=address)
            print(f"Successfully initialized Real BME280 Sensor at address 0x{address:02X}.")
        except Exception as e:
            print(f"Error initializing Real BME280: {e}")
            self.sensor = None
    
    def get_temp_humidity(self):
        if self.sensor:
            return (self.sensor.temperature, self.sensor.humidity)
        return (0.0, 0.0) # Return default values on error

class RealLIS3DH:
    """Interface for the real LIS3DH sensor."""
    def __init__(self, address=None):
        try:
            i2c = board.I2C()
            address = address or config.LIS3DH_ADDRESS
            self.sensor = adafruit_lis3dh.LIS3DH_I2C(i2c, address=address)
            print(f"Successfully initialized Real LIS3DH Sensor at address 0x{address:02X}.")
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
        """
        Initialize vision processor with USB camera and TFLite model.
        Includes robust camera detection with multiple backends and retry logic.
        """
        self.camera = None
        self.interpreter = None
        self.frame = None
        self.latest_detection = None
        self.frame_counter = 0
        
        # Try to initialize camera with multiple strategies
        camera_index = config.CAMERA_DEVICE_INDEX if config.CAMERA_TYPE == "USB" else 0
        self.camera = self._initialize_camera_with_retry(camera_index)
        
        # Initialize ML model (independent of camera)
        try:
            self.interpreter = tflite.Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            self.input_height = self.input_details[0]['shape'][1]
            self.input_width = self.input_details[0]['shape'][2]
            print(f"✅ TFLite model loaded: {model_path}")
        except Exception as e:
            print(f"⚠️  Failed to load TFLite model: {e}")
            print(f"   AI vision features will be disabled")
            self.interpreter = None
            # Set default values for attributes used elsewhere
            self.input_details = None
            self.output_details = None
            self.input_height = 224  # Default input size
            self.input_width = 224
    
    def _initialize_camera_with_retry(self, camera_index):
        """
        Try multiple camera backends and strategies to initialize camera.
        
        Args:
            camera_index (int): Camera device index (usually 0 for USB camera)
        
        Returns:
            cv2.VideoCapture or None: Initialized camera or None if all attempts fail
        """
        import time
        
        # Strategy 1: Try V4L2 backend (best for Linux/Raspberry Pi)
        print(f"📷 Attempting camera initialization (index {camera_index})...")
        backends = [
            (cv2.CAP_V4L2, "V4L2 (Video4Linux)"),
            (cv2.CAP_ANY, "ANY (auto-detect)"),
        ]
        
        for backend, backend_name in backends:
            print(f"   Trying backend: {backend_name}")
            try:
                cap = cv2.VideoCapture(camera_index, backend)
                
                if not cap.isOpened():
                    print(f"   ❌ Failed to open with {backend_name}")
                    cap.release()
                    continue
                
                # Configure camera settings
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer for lower latency
                
                # Verify actual settings
                actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                
                # Give camera time to warm up (important for USB cameras)
                print(f"   ⏳ Waiting for camera warmup (2 seconds)...")
                time.sleep(2)
                
                # Try reading test frame multiple times (first few frames often fail)
                for attempt in range(5):
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        self.frame = test_frame  # Store initial frame
                        print(f"   ✅ Camera initialized successfully!")
                        print(f"      Backend: {backend_name}")
                        print(f"      Resolution: {actual_width}x{actual_height}")
                        print(f"      Frame shape: {test_frame.shape}")
                        return cap
                    print(f"   ⏳ Test frame attempt {attempt+1}/5 failed, retrying...")
                    time.sleep(0.5)
                
                print(f"   ❌ Camera opened but failed to capture frames with {backend_name}")
                cap.release()
                
            except Exception as e:
                print(f"   ❌ Exception with {backend_name}: {e}")
                continue
        
        # All strategies failed
        print(f"❌ Camera initialization FAILED after trying all backends")
        print(f"   Troubleshooting steps:")
        print(f"   1. Check if camera is connected: ls -l /dev/video*")
        print(f"   2. Check camera permissions: sudo usermod -aG video $USER")
        print(f"   3. Test camera outside Docker: v4l2-ctl --list-devices")
        print(f"   4. Try different camera index in config.py: CAMERA_DEVICE_INDEX")
        return None

    def capture_and_process_frame(self, run_inference=True):
        """
        Capture a frame and optionally run AI inference.
        
        Args:
            run_inference (bool): If True, runs AI detection. If False, just captures frame.
        
        Returns:
            tuple: (frame, detection_result)
                - frame: The captured (and possibly annotated) frame
                - detection_result: (box, confidence) or (None, None)
        """
        if not self.camera or not self.camera.isOpened():
            return np.zeros((480, 640, 3), dtype=np.uint8), (None, None)

        ret, frame = self.camera.read()
        if not ret:
            print("Warning: Failed to read frame from camera")
            return np.zeros((480, 640, 3), dtype=np.uint8), (None, None)
        
        # If inference not requested or model not loaded, return raw frame
        if not run_inference or not self.interpreter:
            self.frame = frame
            return frame, (None, None)
        
        try:
            # --- Full Inference Pipeline ---
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

            # Check if we have valid detections
            if len(scores) == 0 or len(boxes) == 0:
                # No detections found
                self.frame = frame
                return frame, (None, None)

            # (Assuming Queen Bee is class 0, and you'll need a labels file)
            for i in range(len(scores)):
                if scores[i] > config.VISION_CONFIDENCE_THRESHOLD:
                    # Ensure boxes[i] has the expected shape
                    if len(boxes[i]) < 4:
                        continue  # Skip malformed detection
                    
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
            self.latest_detection = detection_result  # Store latest detection
            return self.frame, detection_result
            
        except Exception as e:
            print(f"Error in AI inference: {e}")
            # Return raw frame on error
            self.frame = frame
            return frame, (None, None)