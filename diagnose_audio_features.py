#!/usr/bin/env python3
"""
Diagnostic script to inspect the audio model and determine correct feature extraction
"""

import joblib
import numpy as np

print("=" * 70)
print("Audio Model Feature Analysis")
print("=" * 70)

# Load the model
model_path = 'models/audio_model.pkl'
print(f"\n1. Loading model from: {model_path}")
model_dict = joblib.load(model_path)

print("\n2. Model components:")
for key in model_dict.keys():
    print(f"   - {key}: {type(model_dict[key]).__name__}")

# Check feature selector
if 'feature_selector' in model_dict:
    selector = model_dict['feature_selector']
    print(f"\n3. Feature Selector Details:")
    print(f"   Type: {type(selector).__name__}")
    
    if hasattr(selector, 'get_support'):
        support = selector.get_support()
        print(f"   Total features expected: {len(support)}")
        print(f"   Features selected: {support.sum()}")
        print(f"   Features to extract: {len(support)} (BEFORE selection)")
        print(f"   Features after selection: {support.sum()} (AFTER selection)")
    
    if hasattr(selector, 'estimator_'):
        print(f"   Estimator: {type(selector.estimator_).__name__}")

# Check scaler
if 'scaler' in model_dict:
    scaler = model_dict['scaler']
    print(f"\n4. Scaler Details:")
    print(f"   Type: {type(scaler).__name__}")
    if hasattr(scaler, 'n_features_in_'):
        print(f"   Features expected: {scaler.n_features_in_}")
    if hasattr(scaler, 'mean_'):
        print(f"   Mean shape: {scaler.mean_.shape}")

# Check main model
if 'model' in model_dict:
    model = model_dict['model']
    print(f"\n5. Classifier Details:")
    print(f"   Type: {type(model).__name__}")
    if hasattr(model, 'n_features_in_'):
        print(f"   Features expected: {model.n_features_in_}")

# Check label encoder
if 'label_encoder' in model_dict:
    encoder = model_dict['label_encoder']
    print(f"\n6. Label Encoder:")
    print(f"   Classes: {encoder.classes_}")

print("\n" + "=" * 70)
print("DIAGNOSIS:")
print("=" * 70)

if 'feature_selector' in model_dict and hasattr(model_dict['feature_selector'], 'get_support'):
    support = model_dict['feature_selector'].get_support()
    total_features = len(support)
    
    print(f"\n⚠️  Model expects {total_features} features BEFORE feature selection")
    print(f"✅ Current code extracts only 78 features (13 MFCC × 6 stats)")
    print(f"\n💡 SOLUTION: Need to extract {total_features} features")
    print(f"   This suggests using {total_features // 6} MFCC coefficients")
    print(f"   Or additional feature types beyond MFCC")
    
    # Suggest feature extraction
    if total_features == 312:
        print(f"\n📊 Recommended Feature Extraction:")
        print(f"   Option 1: 52 MFCC coefficients × 6 stats = 312 features")
        print(f"   Option 2: 26 MFCC coefficients × 12 stats = 312 features")
        print(f"   Option 3: Multiple feature types (MFCC + spectral + temporal)")

print("\n" + "=" * 70)
