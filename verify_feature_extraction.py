#!/usr/bin/env python3
"""
Verify that inference feature extraction matches training exactly.
"""

import numpy as np
import librosa

# Training configuration
SR = 22050
N_FFT = 2048
HOP = 512
N_MFCC = 13

def training_extract_features(y, sr):
    """EXACT copy of training feature extraction."""
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=N_MFCC, n_fft=N_FFT, hop_length=HOP)
    delta = librosa.feature.delta(mfccs, order=1)
    delta2 = librosa.feature.delta(mfccs, order=2)

    feat = []
    for mat in (mfccs, delta, delta2):
        for coeff in mat:
            feat.extend([
                np.mean(coeff), np.std(coeff), np.min(coeff), np.max(coeff),
                np.median(coeff), np.percentile(coeff, 25),
                np.percentile(coeff, 75), np.var(coeff)
            ])
    return np.array(feat, dtype=np.float32)


def inference_extract_features(y, sr):
    """Inference feature extraction (should match training)."""
    mfcc = librosa.feature.mfcc(
        y=y,
        sr=sr,
        n_mfcc=13,
        n_fft=2048,
        hop_length=512
    )
    
    delta = librosa.feature.delta(mfcc, order=1)
    delta_delta = librosa.feature.delta(mfcc, order=2)
    
    features = []
    for mat in (mfcc, delta, delta_delta):
        for coeff_track in mat:
            features.extend([
                np.mean(coeff_track),
                np.std(coeff_track),
                np.min(coeff_track),
                np.max(coeff_track),
                np.median(coeff_track),
                np.percentile(coeff_track, 25),
                np.percentile(coeff_track, 75),
                np.var(coeff_track)
            ])
    
    return np.array(features, dtype=np.float32)


def test_feature_extraction():
    """Test that both methods produce identical results."""
    print("=" * 70)
    print("Feature Extraction Verification")
    print("=" * 70)
    
    # Create synthetic 1-second audio
    duration = 1.0
    y = np.random.randn(int(SR * duration)).astype(np.float32)
    
    print(f"\nTest audio: {len(y)} samples at {SR} Hz ({duration}s)")
    
    # Extract features using both methods
    print("\n1. Training method...")
    feat_train = training_extract_features(y, SR)
    print(f"   Features: {len(feat_train)}")
    print(f"   Shape: {feat_train.shape}")
    print(f"   First 5: {feat_train[:5]}")
    
    print("\n2. Inference method...")
    feat_infer = inference_extract_features(y, SR)
    print(f"   Features: {len(feat_infer)}")
    print(f"   Shape: {feat_infer.shape}")
    print(f"   First 5: {feat_infer[:5]}")
    
    # Compare
    print("\n3. Comparison:")
    print(f"   Length match: {len(feat_train) == len(feat_infer)}")
    print(f"   Shape match: {feat_train.shape == feat_infer.shape}")
    
    if feat_train.shape == feat_infer.shape:
        diff = np.abs(feat_train - feat_infer)
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)
        
        print(f"   Max difference: {max_diff:.10f}")
        print(f"   Mean difference: {mean_diff:.10f}")
        
        if max_diff < 1e-6:
            print("\n✅ PERFECT MATCH! Features are identical.")
        else:
            print(f"\n⚠️  Small numerical differences (max: {max_diff:.2e})")
            print("   This is normal due to floating point precision.")
            if max_diff < 1e-3:
                print("   ✅ Differences are negligible - PASS")
            else:
                print("   ❌ Differences too large - FAIL")
    else:
        print("\n❌ MISMATCH! Feature shapes don't match.")
        print("   Training and inference are extracting different features!")
    
    print("\n" + "=" * 70)
    print("Expected: 13 MFCC × 3 types × 8 stats = 312 features")
    print("=" * 70)


if __name__ == "__main__":
    test_feature_extraction()
