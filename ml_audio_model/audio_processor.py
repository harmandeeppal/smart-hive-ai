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
import logging
import time
import os
import joblib
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
        self.model = None
        
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
            logger.warning("Audio model will be disabled. System will continue without audio analysis.")
            self.enabled = False
        except ImportError:
            logger.error("❌ Required packages not installed. Install with: pip install librosa scikit-learn sounddevice")
            logger.warning("Audio model will be disabled. System will continue without audio analysis.")
            self.enabled = False
        except Exception as e:
            logger.error(f"❌ Failed to load audio model: {e}")
            logger.warning("Audio model will be disabled. System will continue without audio analysis.")
            self.enabled = False
    
    def record_audio(self, duration_sec: int) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        Record audio from microphone.
        
        Args:
            duration_sec (int): Recording duration in seconds
        
        Returns:
            Tuple[np.ndarray, int]: Audio data and sample rate, or (None, None) on error
        """
        try:
            import sounddevice as sd
            
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
        
        except ImportError:
            logger.error("❌ sounddevice package not installed. Install with: pip install sounddevice")
            return None, None
        except Exception as e:
            logger.error(f"❌ Recording failed: {e}")
            return None, None
    
    def extract_features(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract MFCC features from audio.
        
        Extracts:
        - 13 MFCC coefficients
        - Delta (first derivative)
        - Delta-Delta (second derivative)
        
        Args:
            audio_data (np.ndarray): Audio time series
        
        Returns:
            np.ndarray: Feature matrix (1, n_features) or None on error
        """
        try:
            import librosa
            
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
        
        except ImportError:
            logger.error("❌ librosa package not installed. Install with: pip install librosa")
            return None
        except Exception as e:
            logger.error(f"❌ Feature extraction failed: {e}")
            return None
    
    def classify(self, features: np.ndarray) -> Dict:
        """
        Classify features using pre-trained model.
        
        Args:
            features (np.ndarray): Feature matrix from extract_features()
        
        Returns:
            Dict with keys:
                - classification: "queen_present" or "queen_absent"
                - confidence: Confidence score (0.0-1.0)
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
            return {"classification": "error", "confidence": 0.0}
    
    def record_and_classify(self, duration_sec: int = 30) -> Dict:
        """
        Record audio and classify in one operation.
        
        Args:
            duration_sec (int): Recording duration (default 30s)
        
        Returns:
            Dict with keys:
                - classification: "queen_present" / "queen_absent" / "error"
                - confidence: Confidence score
                - duration: Actual recording duration
                - timestamp: Recording timestamp
                - saved_path: Path to saved audio (if saved)
                - status: "complete" / "failed"
        """
        if not self.enabled or self.model is None:
            return {"error": "Audio processor disabled", "status": "failed"}
        
        try:
            # Record
            audio_data, sr = self.record_audio(duration_sec)
            if audio_data is None:
                return {"error": "Recording failed", "status": "failed"}
            
            # Extract features
            features = self.extract_features(audio_data)
            if features is None:
                return {"error": "Feature extraction failed", "status": "failed"}
            
            # Classify
            classification = self.classify(features)
            if classification["classification"] == "error":
                return {"error": "Classification failed", "status": "failed"}
            
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
            return {"error": str(e), "status": "failed"}
    
    def enable(self):
        """Enable audio processing."""
        if self.model is not None:
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
            "model_loaded": self.model is not None,
            "last_result": self.last_result,
            "sample_rate": self.sample_rate
        }
