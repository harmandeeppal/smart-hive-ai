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
        recordings_dir: str = "audio_recordings",
        window_seconds: float = 1.0,
        hop_seconds: float = 0.5,
        aggregation_method: str = 'max_proba'
    ):
        """
        Initialize audio processor with pre-trained model.
        
        Args:
            model_path (str): Path to scikit-learn model (.pkl)
            sample_rate (int): Sample rate for recording (Hz)
            confidence_threshold (float): Min confidence for classification (0.5-0.95)
            save_recordings (bool): Whether to save recorded audio files
            recordings_dir (str): Directory to save audio files
            window_seconds (float): Window size for windowed inference (default 1.0s)
            hop_seconds (float): Hop size for windowed inference (default 0.5s)
            aggregation_method (str): Aggregation method ('max_proba', 'mean_proba', 'majority_vote')
        
        Raises:
            FileNotFoundError: If model file not found
        """
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.confidence_threshold = confidence_threshold
        self.save_recordings = save_recordings
        self.recordings_dir = recordings_dir
        self.window_seconds = window_seconds
        self.hop_seconds = hop_seconds
        self.aggregation_method = aggregation_method
        self.enabled = True
        self.last_result = {
            "classification": "unknown",
            "confidence": 0.0,
            "status": "idle"
        }
        self.model = None
        self.model_dict = None  # Store full model pipeline
        
        # Create recordings directory if needed
        if save_recordings:
            os.makedirs(recordings_dir, exist_ok=True)
        
        # Load model
        try:
            logger.info(f"Loading audio model from {model_path}")
            self.model_dict = joblib.load(model_path)
            
            # Check if it's a dictionary with pipeline components or just a model
            if isinstance(self.model_dict, dict):
                self.model = self.model_dict.get('model')
                logger.info("✅ Audio model pipeline loaded successfully")
                logger.info(f"   Components: {list(self.model_dict.keys())}")
            else:
                # Old format: just the model
                self.model = self.model_dict
                self.model_dict = {'model': self.model}
                logger.info("✅ Audio model loaded successfully (legacy format)")
            
            logger.info(f"   Windowing: {self.window_seconds}s windows, {self.hop_seconds}s hop")
            logger.info(f"   Aggregation: {self.aggregation_method}")
            
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
            import librosa
            
            # Try to find the correct microphone (Samson Meteorite or C270 webcam)
            devices = sd.query_devices()
            mic_device = None
            device_info = None
            
            # Look for Samson Meteorite Mic (preferred)
            for idx, device in enumerate(devices):
                device_name = device['name'].lower()
                if 'samson' in device_name or 'meteorite' in device_name:
                    if device['max_input_channels'] > 0:
                        mic_device = idx
                        device_info = device
                        logger.info(f"📱 Using microphone: {device['name']} (device {idx})")
                        break
            
            # Fallback to C270 webcam mic if Samson not found
            if mic_device is None:
                for idx, device in enumerate(devices):
                    device_name = device['name'].lower()
                    if 'c270' in device_name or 'webcam' in device_name:
                        if device['max_input_channels'] > 0:
                            mic_device = idx
                            device_info = device
                            logger.info(f"📱 Using microphone: {device['name']} (device {idx})")
                            break
            
            # Use default device if no specific mic found
            if mic_device is None:
                device_info = sd.query_devices(kind='input')
                logger.info(f"📱 Using default microphone")
            
            # Determine recording sample rate
            # Most USB mics support 44100 or 48000 Hz, not 22050
            recording_sr = self.sample_rate
            if device_info:
                default_sr = int(device_info.get('default_samplerate', 44100))
                # Try common sample rates in order of preference
                supported_rates = [22050, 44100, 48000, 16000]
                for rate in supported_rates:
                    try:
                        # Test if this sample rate is supported
                        sd.check_input_settings(device=mic_device, samplerate=rate, channels=1)
                        recording_sr = rate
                        if rate != self.sample_rate:
                            logger.info(f"⚙️  Device doesn't support {self.sample_rate}Hz, using {rate}Hz (will resample)")
                        break
                    except sd.PortAudioError:
                        continue
            
            logger.info(f"⏺ Recording for {duration_sec} seconds at {recording_sr}Hz...")
            
            # Record audio with specific device and sample rate
            audio_data = sd.rec(
                int(duration_sec * recording_sr),
                samplerate=recording_sr,
                channels=1,
                dtype='float32',
                device=mic_device  # Use detected device
            )
            sd.wait()  # Wait for recording to complete
            
            # Flatten to 1D array
            audio_data = audio_data.flatten()
            
            logger.info(f"✅ Recording complete ({len(audio_data)} samples at {recording_sr}Hz)")
            
            # Resample to target sample rate if different
            if recording_sr != self.sample_rate:
                logger.info(f"🔄 Resampling from {recording_sr}Hz to {self.sample_rate}Hz...")
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=recording_sr, 
                    target_sr=self.sample_rate
                )
                logger.info(f"✅ Resampled to {len(audio_data)} samples at {self.sample_rate}Hz")
            
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
    
    def create_windows(self, audio_data: np.ndarray) -> list:
        """
        Split audio into overlapping windows for windowed inference.
        
        Args:
            audio_data (np.ndarray): Audio time series
        
        Returns:
            List[np.ndarray]: List of audio windows
        """
        window_samples = int(self.window_seconds * self.sample_rate)
        hop_samples = int(self.hop_seconds * self.sample_rate)
        
        windows = []
        start = 0
        
        while start + window_samples <= len(audio_data):
            window = audio_data[start:start + window_samples]
            windows.append(window)
            start += hop_samples
        
        # Handle last partial window if >50% of window size
        if start < len(audio_data):
            remaining = len(audio_data) - start
            if remaining >= window_samples * 0.5:
                # Pad the last window to full size
                window = audio_data[start:]
                window = np.pad(window, (0, window_samples - len(window)), mode='constant')
                windows.append(window)
        
        logger.debug(f"Created {len(windows)} windows from {len(audio_data)} samples")
        return windows
    
    def classify_windows(self, audio_data: np.ndarray) -> Dict:
        """
        Classify audio using windowed inference with aggregation.
        
        This is the recommended method that matches the training approach:
        1. Split audio into 1s windows with 0.5s hop
        2. Extract features from each window
        3. Predict for each window
        4. Aggregate predictions (mean_proba or max_proba)
        
        Args:
            audio_data (np.ndarray): Audio time series
        
        Returns:
            Dict with keys:
                - classification: "queen_present" or "queen_absent"
                - confidence: Aggregated confidence score (0.0-1.0)
                - method: Aggregation method used
                - n_windows: Number of windows processed
                - window_results: List of per-window predictions
        """
        try:
            # Step 1: Create windows
            windows = self.create_windows(audio_data)
            logger.info(f"Processing {len(windows)} windows ({self.window_seconds}s each, {self.hop_seconds}s hop)")
            
            # Step 2: Extract features from each window
            window_features = []
            for i, window in enumerate(windows):
                features = self.extract_features(window)
                if features is None:
                    logger.warning(f"Failed to extract features from window {i+1}")
                    continue
                window_features.append(features)
            
            if not window_features:
                logger.error("No valid features extracted from any window")
                return {"classification": "error", "confidence": 0.0, "error": "feature_extraction_failed"}
            
            # Stack into matrix (n_windows, n_features)
            features_matrix = np.vstack(window_features)
            logger.debug(f"Feature matrix shape: {features_matrix.shape}")
            
            # Step 3: Apply model pipeline (feature selection, scaling, prediction)
            X = features_matrix
            
            # Apply feature selector if present
            if 'feature_selector' in self.model_dict and self.model_dict['feature_selector'] is not None:
                X = self.model_dict['feature_selector'].transform(X)
                logger.debug(f"After feature selection: {X.shape}")
            
            # Apply scaler if present
            if 'scaler' in self.model_dict and self.model_dict['scaler'] is not None:
                X = self.model_dict['scaler'].transform(X)
                logger.debug(f"After scaling: {X.shape}")
            
            # Step 4: Predict for each window
            predictions = self.model.predict(X)
            
            # Get probabilities
            try:
                probabilities = self.model.predict_proba(X)
            except AttributeError:
                # Model doesn't support predict_proba
                probabilities = np.zeros((len(predictions), 2))
                probabilities[np.arange(len(predictions)), predictions.astype(int)] = 1.0
            
            # Step 5: Aggregate predictions
            result = self._aggregate_predictions(predictions, probabilities)
            
            logger.info(f"Windowed classification: {result['classification']} (confidence: {result['confidence']:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ Windowed classification failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"classification": "error", "confidence": 0.0, "error": str(e)}
    
    def _aggregate_predictions(self, predictions: np.ndarray, probabilities: np.ndarray) -> Dict:
        """
        Aggregate per-window predictions into final classification.
        
        Args:
            predictions (np.ndarray): Array of predicted class labels
            probabilities (np.ndarray): Array of prediction probabilities (n_windows, 2)
        
        Returns:
            Dict with aggregated results
        """
        n_windows = len(predictions)
        
        # Get confidence scores for positive class (queen_present = 1)
        positive_probabilities = probabilities[:, 1]
        
        if self.aggregation_method == 'max_proba':
            # Use maximum confidence across all windows (conservative)
            final_confidence = np.max(positive_probabilities)
            final_prediction = 1 if final_confidence >= self.confidence_threshold else 0
        
        elif self.aggregation_method == 'mean_proba':
            # Use average confidence across all windows (balanced)
            final_confidence = np.mean(positive_probabilities)
            final_prediction = 1 if final_confidence >= self.confidence_threshold else 0
        
        elif self.aggregation_method == 'majority_vote':
            # Use majority class
            final_prediction = 1 if np.sum(predictions) > len(predictions) / 2 else 0
            final_confidence = np.mean(positive_probabilities)
        
        else:
            logger.warning(f"Unknown aggregation method: {self.aggregation_method}, using max_proba")
            final_confidence = np.max(positive_probabilities)
            final_prediction = 1 if final_confidence >= self.confidence_threshold else 0
        
        # Decode label
        if 'label_encoder' in self.model_dict and self.model_dict['label_encoder'] is not None:
            try:
                final_label = self.model_dict['label_encoder'].inverse_transform([final_prediction])[0]
            except:
                final_label = "queen_present" if final_prediction == 1 else "queen_absent"
        else:
            final_label = "queen_present" if final_prediction == 1 else "queen_absent"
        
        # Compile per-window results
        window_results = []
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            window_results.append({
                'window': i + 1,
                'prediction': int(pred),
                'confidence': float(prob[int(pred)]),
                'queen_proba': float(prob[1])
            })
        
        return {
            'classification': final_label,
            'confidence': float(final_confidence),
            'method': self.aggregation_method,
            'n_windows': n_windows,
            'window_results': window_results
        }
    
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
    
    def record_and_classify(self, duration_sec: int = 30, use_windowing: bool = True) -> Dict:
        """
        Record audio and classify in one operation.
        
        Args:
            duration_sec (int): Recording duration (default 30s)
            use_windowing (bool): Use windowed inference (recommended, default True)
        
        Returns:
            Dict with keys:
                - classification: "queen_present" / "queen_absent" / "error"
                - confidence: Confidence score
                - duration: Actual recording duration
                - timestamp: Recording timestamp
                - saved_path: Path to saved audio (if saved)
                - status: "complete" / "failed"
                - method: Aggregation method (if windowing used)
                - n_windows: Number of windows (if windowing used)
        """
        if not self.enabled or self.model is None:
            return {"error": "Audio processor disabled", "status": "failed"}
        
        try:
            # Record
            audio_data, sr = self.record_audio(duration_sec)
            if audio_data is None:
                return {"error": "Recording failed", "status": "failed"}
            
            # Classify using windowed inference (recommended)
            if use_windowing:
                logger.info("Using windowed inference (recommended)")
                classification = self.classify_windows(audio_data)
                if classification.get("classification") == "error":
                    return {"error": "Classification failed", "status": "failed"}
            else:
                # Legacy: Extract features from entire audio and classify
                logger.warning("Using legacy whole-file inference (not recommended)")
                features = self.extract_features(audio_data)
                if features is None:
                    return {"error": "Feature extraction failed", "status": "failed"}
                
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
