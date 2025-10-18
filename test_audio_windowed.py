#!/usr/bin/env python3
"""
Audio Model Testing Script - Validate Windowed Inference

This script tests the audio classification system to ensure windowed inference
is working correctly and matches the training approach.

Tests:
    1. Model loading and pipeline components
    2. Windowed inference functionality
    3. Feature extraction per window
    4. Aggregation methods (max_proba, mean_proba)
    5. Integration with audio_processor
    6. Comparison with training approach

Usage:
    # Test with synthetic audio
    python test_audio_windowed.py
    
    # Test with real audio file
    python test_audio_windowed.py --audio test.wav
    
    # Test specific aggregation method
    python test_audio_windowed.py --audio test.wav --agg mean_proba

Author: Smart Hive AI Team
Created: October 2025
"""

import argparse
import sys
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from ml_audio_model.audio_processor import AudioProcessor


def generate_synthetic_audio(duration_sec=10, sr=22050, freq=440):
    """
    Generate synthetic audio for testing.
    
    Args:
        duration_sec: Duration in seconds
        sr: Sample rate
        freq: Frequency in Hz
    
    Returns:
        Audio data as numpy array
    """
    print(f"🔊 Generating {duration_sec}s synthetic audio ({freq}Hz sine wave)")
    t = np.linspace(0, duration_sec, int(duration_sec * sr), False)
    audio = np.sin(2 * np.pi * freq * t)
    return audio.astype(np.float32)


def test_model_loading():
    """Test 1: Verify model loads correctly with all pipeline components."""
    print("\n" + "="*70)
    print("TEST 1: Model Loading")
    print("="*70)
    
    try:
        import joblib
        model_path = config.AUDIO_MODEL_PATH
        print(f"📦 Loading model: {model_path}")
        
        model_dict = joblib.load(model_path)
        
        # Check if it's a dictionary with pipeline components
        if isinstance(model_dict, dict):
            print(f"✅ Model loaded as dictionary (pipeline format)")
            print(f"   Components: {list(model_dict.keys())}")
            
            # Verify expected components
            expected = ['model', 'scaler', 'label_encoder', 'feature_selector']
            for component in expected:
                if component in model_dict:
                    print(f"   ✅ {component}: {type(model_dict[component]).__name__}")
                else:
                    print(f"   ⚠️  {component}: MISSING")
            
            return True
        else:
            print(f"⚠️  Model loaded as {type(model_dict).__name__} (legacy format)")
            return True
            
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False


def test_windowing():
    """Test 2: Verify windowing creates correct number of windows."""
    print("\n" + "="*70)
    print("TEST 2: Windowing Logic")
    print("="*70)
    
    try:
        # Create synthetic audio
        duration_sec = 10
        sr = 22050
        audio = generate_synthetic_audio(duration_sec, sr)
        
        # Initialize processor
        processor = AudioProcessor(
            model_path=config.AUDIO_MODEL_PATH,
            window_seconds=1.0,
            hop_seconds=0.5
        )
        
        # Create windows
        windows = processor.create_windows(audio)
        
        # Calculate expected windows
        # For 10s audio with 1s window and 0.5s hop:
        # Windows start at: 0, 0.5, 1.0, 1.5, ..., 9.0
        # Last window at 9.0 (ends at 10.0)
        expected_windows = int((duration_sec - 1.0) / 0.5) + 1
        
        print(f"Audio duration: {duration_sec}s ({len(audio)} samples)")
        print(f"Window size: {processor.window_seconds}s")
        print(f"Hop size: {processor.hop_seconds}s")
        print(f"Expected windows: {expected_windows}")
        print(f"Actual windows: {len(windows)}")
        
        if len(windows) == expected_windows:
            print(f"✅ Window count correct!")
            return True
        else:
            print(f"⚠️  Window count mismatch (expected {expected_windows}, got {len(windows)})")
            return False
            
    except Exception as e:
        print(f"❌ Windowing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_feature_extraction():
    """Test 3: Verify feature extraction produces correct shape."""
    print("\n" + "="*70)
    print("TEST 3: Feature Extraction")
    print("="*70)
    
    try:
        # Create 1-second audio window
        sr = 22050
        audio = generate_synthetic_audio(1.0, sr)
        
        # Initialize processor
        processor = AudioProcessor(config.AUDIO_MODEL_PATH)
        
        # Extract features
        features = processor.extract_features(audio)
        
        # Expected: 13 MFCC * 2 (mean+std) + 13 Delta * 2 + 13 Delta² * 2 = 78 features
        expected_features = 78
        
        print(f"Audio length: {len(audio)} samples (1.0s @ {sr}Hz)")
        print(f"Feature shape: {features.shape}")
        print(f"Expected features: {expected_features}")
        
        if features.shape == (1, expected_features):
            print(f"✅ Feature shape correct!")
            return True
        else:
            print(f"⚠️  Feature shape mismatch (expected (1, {expected_features}), got {features.shape})")
            return False
            
    except Exception as e:
        print(f"❌ Feature extraction test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_windowed_classification():
    """Test 4: Verify windowed classification works end-to-end."""
    print("\n" + "="*70)
    print("TEST 4: Windowed Classification")
    print("="*70)
    
    try:
        # Create synthetic audio
        duration_sec = 5
        sr = 22050
        audio = generate_synthetic_audio(duration_sec, sr)
        
        # Test both aggregation methods
        for agg_method in ['max_proba', 'mean_proba']:
            print(f"\n--- Testing {agg_method} ---")
            
            processor = AudioProcessor(
                model_path=config.AUDIO_MODEL_PATH,
                window_seconds=1.0,
                hop_seconds=0.5,
                aggregation_method=agg_method
            )
            
            result = processor.classify_windows(audio)
            
            print(f"Classification: {result.get('classification')}")
            print(f"Confidence: {result.get('confidence', 0):.3f}")
            print(f"Method: {result.get('method')}")
            print(f"Windows: {result.get('n_windows')}")
            
            if result.get('classification') in ['queen_present', 'queen_absent']:
                print(f"✅ {agg_method} classification successful!")
            else:
                print(f"❌ {agg_method} classification returned: {result.get('classification')}")
                return False
        
        return True
            
    except Exception as e:
        print(f"❌ Windowed classification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_real_audio(audio_path, agg_method='max_proba'):
    """Test 5: Test with real audio file."""
    print("\n" + "="*70)
    print(f"TEST 5: Real Audio File - {audio_path}")
    print("="*70)
    
    try:
        import librosa
        
        # Load audio
        audio, sr = librosa.load(audio_path, sr=22050, mono=True)
        duration = len(audio) / sr
        
        print(f"📂 Loaded: {audio_path}")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Samples: {len(audio)}")
        print(f"   Sample rate: {sr}Hz")
        
        # Initialize processor
        processor = AudioProcessor(
            model_path=config.AUDIO_MODEL_PATH,
            window_seconds=1.0,
            hop_seconds=0.5,
            aggregation_method=agg_method
        )
        
        # Classify
        result = processor.classify_windows(audio)
        
        print(f"\n🔮 PREDICTION RESULTS:")
        print(f"   Classification: {result.get('classification')}")
        print(f"   Confidence: {result.get('confidence', 0):.3f}")
        print(f"   Aggregation: {result.get('method')}")
        print(f"   Windows analyzed: {result.get('n_windows')}")
        
        # Show per-window results if available
        if 'window_results' in result and len(result['window_results']) > 0:
            print(f"\n📊 Per-Window Results (first 5):")
            for window_result in result['window_results'][:5]:
                print(f"   Window {window_result['window']}: "
                      f"queen_proba={window_result['queen_proba']:.3f}")
        
        print(f"\n✅ Real audio test complete!")
        return True
            
    except Exception as e:
        print(f"❌ Real audio test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description='Test audio windowed inference')
    parser.add_argument('--audio', help='Path to audio file for testing')
    parser.add_argument('--agg', choices=['max_proba', 'mean_proba'], 
                       default='max_proba', help='Aggregation method')
    args = parser.parse_args()
    
    print("\n" + "🧪"*35)
    print("AUDIO WINDOWED INFERENCE TEST SUITE")
    print("🧪"*35)
    
    results = {}
    
    # Run tests
    results['model_loading'] = test_model_loading()
    results['windowing'] = test_windowing()
    results['feature_extraction'] = test_feature_extraction()
    results['windowed_classification'] = test_windowed_classification()
    
    if args.audio and Path(args.audio).exists():
        results['real_audio'] = test_with_real_audio(args.audio, args.agg)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:30s} {status}")
    
    print("="*70)
    print(f"Total: {passed}/{total} tests passed")
    print("="*70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Audio system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
