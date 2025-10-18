#!/usr/bin/env python3
"""
Quick diagnostic - Run inside container to check model expectations
"""

import sys
sys.path.insert(0, '/app')

import joblib

model_path = '/app/models/audio_model.pkl'
print("=" * 70)
print("Audio Model Diagnostic")
print("=" * 70)

model_dict = joblib.load(model_path)

print("\nModel Components:")
for key in model_dict.keys():
    print(f"  - {key}")

# Check scaler - this will tell us the feature count
if 'scaler' in model_dict:
    scaler = model_dict['scaler']
    print(f"\nScaler (StandardScaler):")
    print(f"  Features expected: {scaler.n_features_in_}")
    print(f"  Mean shape: {scaler.mean_.shape}")
    print(f"  Std shape: {scaler.scale_.shape}")

# Check feature selector
if 'feature_selector' in model_dict:
    selector = model_dict['feature_selector']
    support = selector.get_support()
    print(f"\nFeature Selector (SelectFromModel):")
    print(f"  Input features expected: {len(support)}")
    print(f"  Features selected (output): {support.sum()}")

# Check model
if 'model' in model_dict:
    model = model_dict['model']
    print(f"\nClassifier (SVM):")
    if hasattr(model, 'n_features_in_'):
        print(f"  Features expected: {model.n_features_in_}")

print("\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
print(f"\n✅ Your extraction code must produce {scaler.n_features_in_} features")
print(f"   (13 MFCC × 3 types × 8 stats = {13*3*8})")

if scaler.n_features_in_ != 312:
    print(f"\n❌ MISMATCH! Scaler expects {scaler.n_features_in_}, not 312!")
    print(f"   You need to adjust feature extraction!")

print("=" * 70)
