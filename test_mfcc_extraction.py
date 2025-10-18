#!/usr/bin/env python3
"""
Quick test to see what feature count we actually get with the training code
"""

import numpy as np
import librosa

SR = 22050
N_FFT = 2048
HOP = 512
N_MFCC = 13

# Create 1 second of audio
audio = np.random.randn(SR).astype(np.float32)

print(f"Audio: {len(audio)} samples ({len(audio)/SR}s)")

# Extract MFCC exactly as training code does
mfccs = librosa.feature.mfcc(y=audio, sr=SR, n_mfcc=N_MFCC, n_fft=N_FFT, hop_length=HOP)
delta = librosa.feature.delta(mfccs, order=1)
delta2 = librosa.feature.delta(mfccs, order=2)

print(f"\nMFCC shape: {mfccs.shape}")
print(f"Delta shape: {delta.shape}")
print(f"Delta2 shape: {delta2.shape}")

# Extract features exactly as training
feat = []
for mat in (mfccs, delta, delta2):
    print(f"\nProcessing matrix with shape: {mat.shape}")
    for i, coeff in enumerate(mat):
        print(f"  Coefficient {i}: shape {coeff.shape}")
        feat.extend([
            np.mean(coeff), np.std(coeff), np.min(coeff), np.max(coeff),
            np.median(coeff), np.percentile(coeff, 25),
            np.percentile(coeff, 75), np.var(coeff)
        ])

feat = np.array(feat, dtype=np.float32)
print(f"\n✅ Total features extracted: {len(feat)}")
print(f"   Expected: 13 × 3 × 8 = 312")
print(f"   Match: {len(feat) == 312}")

if len(feat) != 312:
    print(f"\n❌ Mismatch! Got {len(feat)} instead of 312")
    print(f"   Difference: {312 - len(feat)}")
    print(f"   Coeffs processed: {len(feat) / 8 / 3}")
