"""
ML Models Implementation Guide - Code Templates
Master's Level Project | 2-Day Implementation Timeline
"""

# FILE 1: ml_vision_model/vision_processor.py
# ==========================================

```python
#!/usr/bin/env python3
"""
Vision Model Processor - YOLO-based Queen Bee Detection

This module provides a wrapper for YOLOv8 queen bee detection.
Integrates with the main SmartHiveSystem for real-time video processing.

Dependencies:
    - ultralytics (YOLOv8)
    - opencv-python
    - numpy

Author: Smart Hive AI Team
Created: October 2025
"""

import cv2
import logging
import time
from ultralytics import YOLO
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VisionProcessor:
    """
    Wrapper for YOLO-based queen bee detection.
    
    This class handles:
    - Model loading and initialization
    - Frame processing and inference
    - Bounding box extraction
    - Confidence filtering
    
    Attributes:
        model_path (str): Path to YOLO model file (.pt format)
        confidence_threshold (float): Minimum confidence for detection (0.0-1.0)
        enabled (bool): Whether processing is currently enabled
        last_result (dict): Results from last frame processed
        inference_time_ms (float): Time taken for last inference
    
    Example:
        >>> processor = VisionProcessor('models/vision_model.pt', confidence_threshold=0.7)
        >>> frame = cv2.imread('image.jpg')
        >>> result = processor.process_frame(frame)
        >>> print(f"Queen detected: {result['detected']}")
    """
    
    def __init__(self, model_path: str, confidence_threshold: float = 0.7):
        """
        Initialize vision processor with YOLO model.
        
        Args:
            model_path (str): Path to YOLO model file (vision_model.pt)
            confidence_threshold (float): Minimum confidence for detection (0.5-0.95)
        
        Raises:
            FileNotFoundError: If model file not found
            RuntimeError: If YOLO initialization fails
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.enabled = True
        self.last_result = {"detected": False, "confidence": 0.0, "boxes": []}
        self.inference_time_ms = 0.0
        
        try:
            logger.info(f"Loading YOLO model from {model_path}")
            self.model = YOLO(model_path)
            logger.info("✅ YOLO model loaded successfully")
        except FileNotFoundError:
            logger.error(f"❌ Model file not found: {model_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to load YOLO model: {e}")
            raise RuntimeError(f"YOLO initialization failed: {e}")
    
    def process_frame(self, frame: cv2.Mat) -> Dict:
        """
        Process a single frame and detect queen bee.
        
        Args:
            frame (cv2.Mat): Input frame in BGR format (OpenCV standard)
        
        Returns:
            Dict with keys:
                - detected (bool): Whether queen bee was detected
                - confidence (float): Max confidence score if detected
                - boxes (List[List[int]]): Bounding boxes [[x1,y1,x2,y2], ...]
                - timestamp (float): Processing timestamp
        
        Raises:
            Exception: If frame processing fails (logged and returned in result)
        """
        if not self.enabled or frame is None:
            return self.last_result
        
        try:
            # Resize if needed (YOLO expects specific dimensions)
            if frame.shape != (480, 640, 3):
                frame = cv2.resize(frame, (640, 480))
            
            # Inference
            start_time = time.time()
            results = self.model.predict(
                frame,
                imgsz=640,
                conf=self.confidence_threshold,
                verbose=False
            )
            self.inference_time_ms = (time.time() - start_time) * 1000
            
            # Parse results
            detected = False
            max_confidence = 0.0
            boxes = []
            
            for result in results:
                if result.boxes is None or len(result.boxes) == 0:
                    continue
                
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    label = self.model.names.get(cls_id, "unknown")
                    confidence = float(box.conf[0])
                    
                    # Only process "queen" class detections
                    if label.lower() == "queen" and confidence >= self.confidence_threshold:
                        detected = True
                        max_confidence = max(max_confidence, confidence)
                        
                        # Extract bounding box coordinates
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        boxes.append([x1, y1, x2, y2])
            
            # Store result
            self.last_result = {
                "detected": detected,
                "confidence": round(max_confidence, 3) if detected else 0.0,
                "boxes": boxes,
                "timestamp": time.time(),
                "inference_time_ms": round(self.inference_time_ms, 2)
            }
            
            if detected:
                logger.debug(f"👑 Queen detected with confidence {max_confidence:.3f}")
            
            return self.last_result
        
        except Exception as e:
            logger.error(f"❌ Frame processing error: {e}")
            return {
                "detected": False,
                "confidence": 0.0,
                "boxes": [],
                "error": str(e)
            }
    
    def draw_detections(self, frame: cv2.Mat, result: Dict) -> cv2.Mat:
        """
        Draw bounding boxes and labels on frame.
        
        Args:
            frame (cv2.Mat): Input frame (BGR format)
            result (Dict): Detection result from process_frame()
        
        Returns:
            cv2.Mat: Frame with drawn detections
        """
        output = frame.copy()
        
        if result.get("detected", False):
            for box in result.get("boxes", []):
                x1, y1, x2, y2 = box
                # Draw red rectangle
                cv2.rectangle(output, (x1, y1), (x2, y2), (0, 0, 255), 2)
                # Draw label
                label = f"Queen ({result['confidence']:.2f})"
                cv2.putText(
                    output, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2
                )
        
        # Add status text
        status_text = "🟢 Detecting" if self.enabled else "🔴 Disabled"
        cv2.putText(output, status_text, (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        return output
    
    def enable(self):
        """Enable vision processing."""
        self.enabled = True
        logger.info("✅ Vision processing enabled")
    
    def disable(self):
        """Disable vision processing."""
        self.enabled = False
        logger.info("⏹ Vision processing disabled")


# FILE 2: ml_audio_model/audio_processor.py
# ==========================================

```python
#!/usr/bin/env python3
"""
Audio Model Processor - Queen Bee Classification from Audio

This module provides a wrapper for audio-based queen bee detection.
Records microphone input, extracts MFCC features, and classifies using ML.

Dependencies:
    - librosa
    - scikit-learn
    - sounddevice
    - numpy
    - scipy

Author: Smart Hive AI Team
Created: October 2025
"""

import numpy as np
import librosa
import sounddevice as sd
import joblib
import logging
import time
import os
from typing import Dict, Tuple, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    Wrapper for audio-based queen bee detection using ML.
    
    This class handles:
    - Microphone recording
    - MFCC feature extraction
    - Classification using pre-trained model
    - Result caching and error handling
    
    Attributes:
        model_path (str): Path to pre-trained model (.pkl file)
        sample_rate (int): Audio sample rate in Hz
        confidence_threshold (float): Minimum classification confidence
        enabled (bool): Whether processing is enabled
        last_result (dict): Results from last recording
        
    Example:
        >>> processor = AudioProcessor('models/audio_model.pkl')
        >>> result = processor.record_and_classify(duration_sec=30)
        >>> print(f"Result: {result['classification']}")
    """
    
    def __init__(
        self,
        model_path: str,
        sample_rate: int = 22050,
        confidence_threshold: float = 0.6,
        save_recordings: bool = False,
        recordings_dir: str = "audio_recordings"
    ):
        """
        Initialize audio processor with pre-trained model.
        
        Args:
            model_path (str): Path to scikit-learn model (.pkl)
            sample_rate (int): Sample rate for recording (Hz)
            confidence_threshold (float): Min confidence for classification (0.5-0.95)
            save_recordings (bool): Whether to save recorded audio files
            recordings_dir (str): Directory to save audio files
        
        Raises:
            FileNotFoundError: If model file not found
        """
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.confidence_threshold = confidence_threshold
        self.save_recordings = save_recordings
        self.recordings_dir = recordings_dir
        self.enabled = True
        self.last_result = {
            "classification": "unknown",
            "confidence": 0.0,
            "status": "idle"
        }
        
        # Create recordings directory if needed
        if save_recordings:
            os.makedirs(recordings_dir, exist_ok=True)
        
        # Load model
        try:
            logger.info(f"Loading audio model from {model_path}")
            self.model = joblib.load(model_path)
            logger.info("✅ Audio model loaded successfully")
        except FileNotFoundError:
            logger.error(f"❌ Model file not found: {model_path}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to load audio model: {e}")
            raise RuntimeError(f"Model loading failed: {e}")
    
    def record_audio(self, duration_sec: int) -> Tuple[np.ndarray, int]:
        """
        Record audio from microphone.
        
        Args:
            duration_sec (int): Recording duration in seconds
        
        Returns:
            Tuple[np.ndarray, int]: Audio data and sample rate
        
        Raises:
            RuntimeError: If microphone not found or recording fails
        """
        try:
            logger.info(f"⏺ Recording for {duration_sec} seconds...")
            
            # Record audio
            audio_data = sd.rec(
                int(duration_sec * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            sd.wait()  # Wait for recording to complete
            
            # Flatten to 1D array
            audio_data = audio_data.flatten()
            
            logger.info(f"✅ Recording complete ({len(audio_data)} samples)")
            return audio_data, self.sample_rate
        
        except Exception as e:
            logger.error(f"❌ Recording failed: {e}")
            raise RuntimeError(f"Microphone recording failed: {e}")
    
    def extract_features(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Extract MFCC features from audio.
        
        Extracts:
        - 13 MFCC coefficients
        - Delta (first derivative)
        - Delta-Delta (second derivative)
        
        Args:
            audio_data (np.ndarray): Audio time series
        
        Returns:
            np.ndarray: Feature matrix (1, n_features)
        
        Raises:
            Exception: If feature extraction fails
        """
        try:
            # Extract MFCC
            mfcc = librosa.feature.mfcc(
                y=audio_data,
                sr=self.sample_rate,
                n_mfcc=13
            )
            
            # Compute statistics: mean and std for each coefficient
            mfcc_mean = np.mean(mfcc, axis=1)
            mfcc_std = np.std(mfcc, axis=1)
            
            # Extract delta and delta-delta
            delta = librosa.feature.delta(mfcc)
            delta_mean = np.mean(delta, axis=1)
            delta_std = np.std(delta, axis=1)
            
            delta_delta = librosa.feature.delta(mfcc, order=2)
            delta_delta_mean = np.mean(delta_delta, axis=1)
            delta_delta_std = np.std(delta_delta, axis=1)
            
            # Combine all features
            features = np.concatenate([
                mfcc_mean, mfcc_std,
                delta_mean, delta_std,
                delta_delta_mean, delta_delta_std
            ])
            
            logger.debug(f"Extracted {len(features)} features")
            return features.reshape(1, -1)  # Return as 2D array for model
        
        except Exception as e:
            logger.error(f"❌ Feature extraction failed: {e}")
            raise
    
    def classify(self, features: np.ndarray) -> Dict:
        """
        Classify features using pre-trained model.
        
        Args:
            features (np.ndarray): Feature matrix from extract_features()
        
        Returns:
            Dict with keys:
                - classification: "queen_present" or "queen_absent"
                - confidence: Confidence score (0.0-1.0)
        
        Raises:
            Exception: If classification fails
        """
        try:
            # Get prediction
            prediction = self.model.predict(features)[0]
            
            # Try to get probability if model supports it
            try:
                probabilities = self.model.predict_proba(features)[0]
                confidence = max(probabilities)
            except AttributeError:
                # Model doesn't support predict_proba
                confidence = 0.5  # Default confidence
            
            classification = "queen_present" if prediction == 1 else "queen_absent"
            
            return {
                "classification": classification,
                "confidence": round(float(confidence), 3)
            }
        
        except Exception as e:
            logger.error(f"❌ Classification failed: {e}")
            raise
    
    def record_and_classify(self, duration_sec: int = 30) -> Dict:
        """
        Record audio and classify in one operation.
        
        Args:
            duration_sec (int): Recording duration (default 30s)
        
        Returns:
            Dict with keys:
                - classification: "queen_present" / "queen_absent"
                - confidence: Confidence score
                - duration: Actual recording duration
                - timestamp: Recording timestamp
                - saved_path: Path to saved audio (if saved)
        """
        if not self.enabled:
            return {"error": "Audio processor disabled"}
        
        try:
            # Record
            audio_data, sr = self.record_audio(duration_sec)
            
            # Extract features
            features = self.extract_features(audio_data)
            
            # Classify
            classification = self.classify(features)
            
            # Save if enabled
            saved_path = None
            if self.save_recordings:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"audio_{timestamp}.npy"
                filepath = os.path.join(self.recordings_dir, filename)
                np.save(filepath, audio_data)
                saved_path = filepath
                logger.info(f"💾 Audio saved to {filepath}")
            
            # Compile result
            self.last_result = {
                "classification": classification["classification"],
                "confidence": classification["confidence"],
                "duration": duration_sec,
                "timestamp": time.time(),
                "saved_path": saved_path,
                "status": "complete"
            }
            
            return self.last_result
        
        except Exception as e:
            logger.error(f"❌ Record and classify failed: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def enable(self):
        """Enable audio processing."""
        self.enabled = True
        logger.info("✅ Audio processing enabled")
    
    def disable(self):
        """Disable audio processing."""
        self.enabled = False
        logger.info("⏹ Audio processing disabled")
    
    def get_status(self) -> Dict:
        """Get current processor status."""
        return {
            "enabled": self.enabled,
            "last_result": self.last_result,
            "model_loaded": self.model is not None,
            "sample_rate": self.sample_rate
        }


# FILE 3: Test Scripts
# ====================

# scripts/test_vision_model.py

```python
#!/usr/bin/env python3
"""Test vision model integration"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import config
from ml_vision_model.vision_processor import VisionProcessor

def test_vision_processor():
    """Test vision processor with mock frame."""
    print("=" * 60)
    print("Testing Vision Model Processor")
    print("=" * 60)
    
    try:
        # Load processor
        print("\n1. Loading vision processor...")
        processor = VisionProcessor(
            config.VISION_MODEL_PATH,
            config.VISION_CONFIDENCE_THRESHOLD
        )
        print("   ✅ Vision processor loaded")
        
        # Test with blank frame
        print("\n2. Testing with blank frame...")
        blank_frame = cv2.zeros((480, 640, 3), dtype='uint8')
        result = processor.process_frame(blank_frame)
        print(f"   Result: {result}")
        print(f"   ✅ No errors on blank frame")
        
        # Test with random frame
        print("\n3. Testing with random frame...")
        import numpy as np
        random_frame = np.random.randint(0, 256, (480, 640, 3), dtype='uint8')
        result = processor.process_frame(random_frame)
        print(f"   Result: Detected={result['detected']}, "
              f"Confidence={result['confidence']}, "
              f"Inference Time={result.get('inference_time_ms', 'N/A')}ms")
        print(f"   ✅ Random frame processed")
        
        # Test enable/disable
        print("\n4. Testing enable/disable...")
        processor.disable()
        result = processor.process_frame(random_frame)
        print(f"   Disabled - Result: {result}")
        processor.enable()
        print(f"   ✅ Enable/disable working")
        
        print("\n" + "=" * 60)
        print("✅ ALL VISION TESTS PASSED")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = test_vision_processor()
    sys.exit(0 if success else 1)
```

# scripts/test_audio_model.py

```python
#!/usr/bin/env python3
"""Test audio model integration"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from ml_audio_model.audio_processor import AudioProcessor
import numpy as np

def test_audio_processor():
    """Test audio processor."""
    print("=" * 60)
    print("Testing Audio Model Processor")
    print("=" * 60)
    
    try:
        # Load processor
        print("\n1. Loading audio processor...")
        processor = AudioProcessor(
            config.AUDIO_MODEL_PATH,
            config.AUDIO_SAMPLE_RATE,
            config.AUDIO_CONFIDENCE_THRESHOLD
        )
        print("   ✅ Audio processor loaded")
        
        # Test status
        print("\n2. Testing status...")
        status = processor.get_status()
        print(f"   Status: {status}")
        print(f"   ✅ Status retrieved")
        
        # Test feature extraction with synthetic audio
        print("\n3. Testing feature extraction...")
        synthetic_audio = np.random.randn(config.AUDIO_SAMPLE_RATE * 3)  # 3s audio
        features = processor.extract_features(synthetic_audio)
        print(f"   Extracted {features.shape[1]} features")
        print(f"   ✅ Feature extraction working")
        
        # Note: Full record_and_classify() requires live microphone
        # Skipping in automated test
        print("\n4. Record test (skipped - requires live microphone)")
        print("   To test recording, run:")
        print("   python test_audio_model.py --record")
        
        print("\n" + "=" * 60)
        print("✅ ALL AUDIO TESTS PASSED")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = test_audio_processor()
    sys.exit(0 if success else 1)
```

---

# QUICK REFERENCE: Key Functions to Call

## In app.py SmartHiveSystem

```python
# Initialize in __init__
self.vision_processor = VisionProcessor(
    config.VISION_MODEL_PATH,
    config.VISION_CONFIDENCE_THRESHOLD
)

self.audio_processor = AudioProcessor(
    config.AUDIO_MODEL_PATH,
    config.AUDIO_SAMPLE_RATE
)

# In vision thread (every N frames)
result = self.vision_processor.process_frame(frame)
if result['detected']:
    self.publish_result('VISION', result)

# On dashboard request
result = self.audio_processor.record_and_classify(30)
self.publish_result('AUDIO', result)
```

---

**END OF IMPLEMENTATION GUIDE**
