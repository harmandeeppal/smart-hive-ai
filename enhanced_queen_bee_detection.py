#!/usr/bin/env python3
"""
Enhanced Queen Bee Detection - Windowed Inference Script

This script implements the proper windowed inference approach for queen bee
audio classification, matching the training methodology.

Architecture:
    1. Load audio file (or record from microphone)
    2. Split into 1-second windows with 0.5-second hop (50% overlap)
    3. Extract MFCC + Δ + Δ² features for each window
    4. Apply feature selection and scaling (from training pipeline)
    5. Predict per-window classification with confidence
    6. Aggregate predictions across all windows (mean_proba or max_proba)
    7. Return final classification with aggregated confidence

Usage:
    # Predict from audio file with max aggregation (recommended)
    python enhanced_queen_bee_detection.py recording.wav --model models/audio_model.pkl --agg max_proba
    
    # Predict from audio file with mean aggregation
    python enhanced_queen_bee_detection.py recording.wav --model models/audio_model.pkl --agg mean_proba
    
    # Record from microphone and predict
    python enhanced_queen_bee_detection.py --record 30 --model models/audio_model.pkl --agg max_proba
    
    # Verbose output showing per-window predictions
    python enhanced_queen_bee_detection.py recording.wav --model models/audio_model.pkl --agg max_proba --verbose

Dependencies:
    numpy>=1.26.4
    scipy>=1.11.4
    scikit-learn>=1.3.2
    librosa>=0.10.1
    joblib>=1.3.2
    soundfile>=0.12.1
    audioread>=3.0.1
    sounddevice (optional, for recording)

Author: Smart Hive AI Team
Created: October 2025
"""

import argparse
import sys
import warnings
import numpy as np
import joblib
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Suppress librosa warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# ============================================================================
# CONSTANTS - MUST MATCH TRAINING CONFIGURATION
# ============================================================================

# Sample rate (Hz) - MUST match training
SR = 22050

# Window parameters for sliding window inference
WINDOW_SECONDS = 1.0    # 1-second windows (MUST match training)
HOP_SECONDS = 0.5       # 0.5-second hop (50% overlap)

# MFCC parameters (MUST match training)
N_MFCC = 13             # Number of MFCC coefficients
N_FFT = 2048            # FFT window size
HOP_LENGTH = 512        # Hop length for MFCC

# Classification thresholds
CONFIDENCE_THRESHOLD = 0.6  # Minimum confidence for positive classification


# ============================================================================
# AUDIO LOADING AND PREPROCESSING
# ============================================================================

def load_audio(audio_path: str, sr: int = SR) -> Tuple[np.ndarray, int]:
    """
    Load audio file and resample to target sample rate.
    
    Args:
        audio_path: Path to audio file (.wav, .mp3, etc.)
        sr: Target sample rate (default 22050 Hz)
    
    Returns:
        Tuple of (audio_data, sample_rate)
    
    Raises:
        FileNotFoundError: If audio file doesn't exist
        Exception: If audio loading fails
    """
    try:
        import librosa
        print(f"📂 Loading audio: {audio_path}")
        
        # Load and resample to target SR
        audio_data, sample_rate = librosa.load(audio_path, sr=sr, mono=True)
        
        duration = len(audio_data) / sample_rate
        print(f"✅ Loaded: {duration:.2f}s @ {sample_rate} Hz ({len(audio_data)} samples)")
        
        return audio_data, sample_rate
    
    except FileNotFoundError:
        print(f"❌ Error: Audio file not found: {audio_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading audio: {e}")
        sys.exit(1)


def record_audio(duration_sec: int, sr: int = SR) -> np.ndarray:
    """
    Record audio from microphone.
    
    Args:
        duration_sec: Recording duration in seconds
        sr: Sample rate (default 22050 Hz)
    
    Returns:
        Audio data as numpy array
    
    Raises:
        ImportError: If sounddevice not installed
        Exception: If recording fails
    """
    try:
        import sounddevice as sd
        
        print(f"🎤 Recording for {duration_sec} seconds...")
        print("   (Speak clearly near microphone)")
        
        audio_data = sd.rec(
            int(duration_sec * sr),
            samplerate=sr,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        
        audio_data = audio_data.flatten()
        print(f"✅ Recording complete ({len(audio_data)} samples)")
        
        return audio_data
    
    except ImportError:
        print("❌ Error: sounddevice not installed")
        print("   Install with: pip install sounddevice")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        sys.exit(1)


# ============================================================================
# WINDOWING AND FEATURE EXTRACTION
# ============================================================================

def create_windows(audio_data: np.ndarray, sr: int, window_sec: float, hop_sec: float) -> List[np.ndarray]:
    """
    Split audio into overlapping windows.
    
    Args:
        audio_data: Audio time series
        sr: Sample rate
        window_sec: Window length in seconds
        hop_sec: Hop size in seconds (overlap = window_sec - hop_sec)
    
    Returns:
        List of audio windows (each as numpy array)
    """
    window_samples = int(window_sec * sr)
    hop_samples = int(hop_sec * sr)
    
    windows = []
    start = 0
    
    while start + window_samples <= len(audio_data):
        window = audio_data[start:start + window_samples]
        windows.append(window)
        start += hop_samples
    
    # Handle last partial window if it exists and is >50% of window size
    if start < len(audio_data):
        remaining = len(audio_data) - start
        if remaining >= window_samples * 0.5:
            # Pad the last window to full size
            window = audio_data[start:]
            window = np.pad(window, (0, window_samples - len(window)), mode='constant')
            windows.append(window)
    
    return windows


def extract_window_features(window: np.ndarray, sr: int) -> np.ndarray:
    """
    Extract MFCC + Δ + Δ² features from a single audio window.
    
    This MUST match the exact feature extraction used during training.
    
    Features extracted:
        - 13 MFCC coefficients (mean + std)
        - 13 Delta coefficients (mean + std)
        - 13 Delta-Delta coefficients (mean + std)
        Total: 13*2 + 13*2 + 13*2 = 78 features
    
    Args:
        window: Audio window (1-second at 22050 Hz)
        sr: Sample rate
    
    Returns:
        Feature vector (1D numpy array, length 78)
    """
    import librosa
    
    # Extract MFCC (13 coefficients)
    mfcc = librosa.feature.mfcc(
        y=window,
        sr=sr,
        n_mfcc=N_MFCC,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH
    )
    
    # Compute statistics: mean and std for each coefficient
    mfcc_mean = np.mean(mfcc, axis=1)  # Shape: (13,)
    mfcc_std = np.std(mfcc, axis=1)    # Shape: (13,)
    
    # Extract Delta (first derivative)
    delta = librosa.feature.delta(mfcc)
    delta_mean = np.mean(delta, axis=1)
    delta_std = np.std(delta, axis=1)
    
    # Extract Delta-Delta (second derivative)
    delta_delta = librosa.feature.delta(mfcc, order=2)
    delta_delta_mean = np.mean(delta_delta, axis=1)
    delta_delta_std = np.std(delta_delta, axis=1)
    
    # Combine all features: [MFCC_mean, MFCC_std, Δ_mean, Δ_std, Δ²_mean, Δ²_std]
    features = np.concatenate([
        mfcc_mean, mfcc_std,
        delta_mean, delta_std,
        delta_delta_mean, delta_delta_std
    ])
    
    return features


def extract_all_window_features(windows: List[np.ndarray], sr: int, verbose: bool = False) -> np.ndarray:
    """
    Extract features from all windows.
    
    Args:
        windows: List of audio windows
        sr: Sample rate
        verbose: Print per-window extraction progress
    
    Returns:
        Feature matrix (n_windows, 78)
    """
    n_windows = len(windows)
    print(f"🔧 Extracting features from {n_windows} windows...")
    
    features_list = []
    for i, window in enumerate(windows):
        features = extract_window_features(window, sr)
        features_list.append(features)
        
        if verbose:
            print(f"   Window {i+1}/{n_windows}: {len(features)} features extracted")
    
    # Stack into matrix (n_windows, n_features)
    features_matrix = np.vstack(features_list)
    print(f"✅ Feature matrix shape: {features_matrix.shape}")
    
    return features_matrix


# ============================================================================
# MODEL LOADING AND PREDICTION
# ============================================================================

def load_model(model_path: str) -> Dict:
    """
    Load the pre-trained audio classification model.
    
    Expected model structure (dict):
        {
            'model': SVC classifier (main model),
            'scaler': StandardScaler (feature scaling),
            'label_encoder': LabelEncoder (label encoding),
            'feature_selector': SelectFromModel (feature selection)
        }
    
    Args:
        model_path: Path to .pkl model file
    
    Returns:
        Model dictionary
    
    Raises:
        FileNotFoundError: If model file doesn't exist
        Exception: If model loading fails
    """
    try:
        print(f"📦 Loading model: {model_path}")
        model_dict = joblib.load(model_path)
        
        # Verify required components
        required_keys = ['model', 'scaler', 'label_encoder', 'feature_selector']
        for key in required_keys:
            if key not in model_dict:
                print(f"⚠️  Warning: Model missing component '{key}'")
        
        print(f"✅ Model loaded successfully")
        print(f"   Components: {list(model_dict.keys())}")
        
        return model_dict
    
    except FileNotFoundError:
        print(f"❌ Error: Model file not found: {model_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def predict_windows(features_matrix: np.ndarray, model_dict: Dict, verbose: bool = False) -> Tuple[np.ndarray, np.ndarray]:
    """
    Predict classification for each window using the full model pipeline.
    
    Pipeline:
        1. Feature selection (SelectFromModel)
        2. Feature scaling (StandardScaler)
        3. Classification (SVC with probability)
    
    Args:
        features_matrix: Feature matrix (n_windows, n_features)
        model_dict: Loaded model dictionary
        verbose: Print per-window predictions
    
    Returns:
        Tuple of (predictions, probabilities)
            predictions: Array of class labels (0 or 1)
            probabilities: Array of confidence scores (n_windows, 2)
    """
    print(f"🔮 Running inference on {len(features_matrix)} windows...")
    
    # Extract pipeline components
    feature_selector = model_dict.get('feature_selector')
    scaler = model_dict.get('scaler')
    model = model_dict['model']
    
    # Apply pipeline
    X = features_matrix
    
    # Step 1: Feature selection
    if feature_selector is not None:
        X = feature_selector.transform(X)
        if verbose:
            print(f"   After feature selection: {X.shape}")
    
    # Step 2: Scaling
    if scaler is not None:
        X = scaler.transform(X)
        if verbose:
            print(f"   After scaling: {X.shape}")
    
    # Step 3: Prediction
    predictions = model.predict(X)
    
    # Get probabilities if supported
    try:
        probabilities = model.predict_proba(X)
    except AttributeError:
        # Model doesn't support probability, create dummy probabilities
        probabilities = np.zeros((len(predictions), 2))
        probabilities[np.arange(len(predictions)), predictions] = 1.0
    
    if verbose:
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            confidence = prob[pred]
            label = "queen_present" if pred == 1 else "queen_absent"
            print(f"   Window {i+1}: {label} (confidence: {confidence:.3f})")
    
    return predictions, probabilities


# ============================================================================
# AGGREGATION
# ============================================================================

def aggregate_predictions(predictions: np.ndarray, probabilities: np.ndarray, 
                         method: str = 'max_proba', label_encoder = None) -> Dict:
    """
    Aggregate per-window predictions into final classification.
    
    Aggregation methods:
        - 'max_proba': Use maximum confidence across all windows (conservative)
        - 'mean_proba': Use average confidence across all windows (balanced)
        - 'majority_vote': Use majority class (simple voting)
    
    Args:
        predictions: Array of predicted class labels (0 or 1)
        probabilities: Array of prediction probabilities (n_windows, 2)
        method: Aggregation method ('max_proba', 'mean_proba', or 'majority_vote')
        label_encoder: LabelEncoder to decode class labels
    
    Returns:
        Dictionary with:
            - classification: 'queen_present' or 'queen_absent'
            - confidence: Aggregated confidence score (0.0-1.0)
            - method: Aggregation method used
            - n_windows: Number of windows processed
            - window_predictions: List of per-window results
    """
    n_windows = len(predictions)
    
    # Get confidence scores for positive class (queen_present = 1)
    positive_probabilities = probabilities[:, 1]
    
    if method == 'max_proba':
        # Use maximum confidence across all windows
        final_confidence = np.max(positive_probabilities)
        final_prediction = 1 if final_confidence >= CONFIDENCE_THRESHOLD else 0
    
    elif method == 'mean_proba':
        # Use average confidence across all windows
        final_confidence = np.mean(positive_probabilities)
        final_prediction = 1 if final_confidence >= CONFIDENCE_THRESHOLD else 0
    
    elif method == 'majority_vote':
        # Use majority class
        final_prediction = 1 if np.sum(predictions) > len(predictions) / 2 else 0
        final_confidence = np.mean(positive_probabilities)
    
    else:
        raise ValueError(f"Unknown aggregation method: {method}")
    
    # Decode label
    if label_encoder is not None:
        try:
            final_label = label_encoder.inverse_transform([final_prediction])[0]
        except:
            final_label = "queen_present" if final_prediction == 1 else "queen_absent"
    else:
        final_label = "queen_present" if final_prediction == 1 else "queen_absent"
    
    # Compile per-window results
    window_predictions = []
    for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
        window_predictions.append({
            'window': i + 1,
            'prediction': int(pred),
            'confidence': float(prob[pred]),
            'queen_proba': float(prob[1])
        })
    
    return {
        'classification': final_label,
        'confidence': float(final_confidence),
        'method': method,
        'n_windows': n_windows,
        'window_predictions': window_predictions
    }


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def predict_audio(audio_path: Optional[str], model_path: str, aggregation_method: str = 'max_proba',
                 record_duration: Optional[int] = None, verbose: bool = False) -> Dict:
    """
    Complete prediction pipeline: load audio → window → extract → predict → aggregate.
    
    Args:
        audio_path: Path to audio file (or None if recording)
        model_path: Path to model .pkl file
        aggregation_method: 'max_proba', 'mean_proba', or 'majority_vote'
        record_duration: Duration to record if audio_path is None
        verbose: Print detailed per-window information
    
    Returns:
        Dictionary with final classification results
    """
    print("=" * 70)
    print("Enhanced Queen Bee Detection - Windowed Inference")
    print("=" * 70)
    
    # Step 1: Load or record audio
    if audio_path:
        audio_data, sr = load_audio(audio_path, SR)
    elif record_duration:
        audio_data = record_audio(record_duration, SR)
        sr = SR
    else:
        print("❌ Error: Must provide --audio or --record")
        sys.exit(1)
    
    # Step 2: Load model
    model_dict = load_model(model_path)
    
    # Step 3: Create windows
    print(f"🪟  Creating windows (window={WINDOW_SECONDS}s, hop={HOP_SECONDS}s)...")
    windows = create_windows(audio_data, sr, WINDOW_SECONDS, HOP_SECONDS)
    print(f"✅ Created {len(windows)} windows")
    
    # Step 4: Extract features from all windows
    features_matrix = extract_all_window_features(windows, sr, verbose)
    
    # Step 5: Predict for each window
    predictions, probabilities = predict_windows(features_matrix, model_dict, verbose)
    
    # Step 6: Aggregate predictions
    print(f"📊 Aggregating predictions (method: {aggregation_method})...")
    result = aggregate_predictions(
        predictions, 
        probabilities, 
        method=aggregation_method,
        label_encoder=model_dict.get('label_encoder')
    )
    
    return result


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for enhanced queen bee detection."""
    parser = argparse.ArgumentParser(
        description='Enhanced Queen Bee Detection - Windowed Inference',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Predict from file with max aggregation (recommended)
  python enhanced_queen_bee_detection.py recording.wav --model models/audio_model.pkl --agg max_proba
  
  # Predict from file with mean aggregation
  python enhanced_queen_bee_detection.py recording.wav --model models/audio_model.pkl --agg mean_proba
  
  # Record 30 seconds and predict
  python enhanced_queen_bee_detection.py --record 30 --model models/audio_model.pkl --agg max_proba
  
  # Verbose output (show per-window predictions)
  python enhanced_queen_bee_detection.py recording.wav --model models/audio_model.pkl --agg max_proba --verbose
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('audio_file', nargs='?', help='Path to audio file (.wav, .mp3, etc.)')
    input_group.add_argument('--record', type=int, metavar='SECONDS', help='Record audio for N seconds')
    
    # Model options
    parser.add_argument('--model', required=True, help='Path to trained model (.pkl file)')
    
    # Aggregation options
    parser.add_argument('--agg', choices=['max_proba', 'mean_proba', 'majority_vote'], 
                       default='max_proba', help='Aggregation method (default: max_proba)')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true', help='Show per-window predictions')
    
    args = parser.parse_args()
    
    # Run prediction
    try:
        result = predict_audio(
            audio_path=args.audio_file,
            model_path=args.model,
            aggregation_method=args.agg,
            record_duration=args.record,
            verbose=args.verbose
        )
        
        # Print final result
        print("\n" + "=" * 70)
        print("FINAL RESULT")
        print("=" * 70)
        print(f"Prediction: {result['classification']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Method: {result['method']}")
        print(f"Windows analyzed: {result['n_windows']}")
        print("=" * 70)
        
        # Exit with appropriate code
        if result['classification'] == 'queen_present':
            sys.exit(0)  # Success - queen detected
        else:
            sys.exit(1)  # No queen detected
    
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
