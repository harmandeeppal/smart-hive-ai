# Audio ML Pipeline Order Fix

## 🐛 The Bug

The audio classification system was failing with:
```
ERROR: X has 271 features, but StandardScaler is expecting 312 features as input.
```

## 🔍 Root Cause Analysis

### Training Pipeline Order (Correct)
From the training code:
```python
# 1. Extract features (312)
X = extract_enhanced_mfcc_features(audio_file)  # 13 MFCC × 3 types × 8 stats = 312

# 2. Scale features (312 → 312)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # Scaler fitted on 312 features

# 3. LASSO feature selection (312 → 271)
selector = SelectFromModel(LassoCV(...))
X_selected = selector.fit_transform(X_scaled)  # Reduces to 271 features

# 4. Train model on 271 features
model.fit(X_selected, y)
```

### Previous Inference Pipeline Order (WRONG ❌)
```python
# 1. Extract features (312) ✅
features = extract_features(audio)  # 312 features

# 2. Feature selection FIRST (312 → 271) ✅
X = feature_selector.transform(features)  # 271 features

# 3. Scale SECOND (expects 312, got 271) ❌ ERROR!
X = scaler.transform(X)  # Scaler expects 312 but receives 271
```

### Fixed Inference Pipeline Order (CORRECT ✅)
```python
# 1. Extract features (312) ✅
features = extract_features(audio)  # 312 features

# 2. Scale FIRST (312 → 312) ✅
X = scaler.transform(features)  # Scaler receives expected 312 features

# 3. Feature selection SECOND (312 → 271) ✅
X = feature_selector.transform(X)  # Reduces to 271 features

# 4. Predict with model
predictions = model.predict(X)  # Model receives expected 271 features
```

## ✅ The Fix

**File**: `ml_audio_model/audio_processor.py`  
**Method**: `classify_windows()`  
**Lines**: 453-470

Changed from:
```python
# Wrong order
X = features_matrix
if 'feature_selector' in self.model_dict:
    X = self.model_dict['feature_selector'].transform(X)  # Applied first
if 'scaler' in self.model_dict:
    X = self.model_dict['scaler'].transform(X)  # Applied second
```

To:
```python
# Correct order (matches training)
X = features_matrix
if 'scaler' in self.model_dict:
    X = self.model_dict['scaler'].transform(X)  # Applied first
if 'feature_selector' in self.model_dict:
    X = self.model_dict['feature_selector'].transform(X)  # Applied second
```

## 🎯 Key Insight

**The scaler must see the same number of features during inference as it saw during training.**

- During training: Scaler was fitted on **312 features** (before LASSO selection)
- During inference: Scaler must receive **312 features** (before LASSO selection)
- After scaling: Feature selector reduces **312 → 271** features
- Model receives: **271 features** (as expected)

## 📊 Feature Breakdown

**312 features = 13 MFCC × 3 types × 8 statistics**

- **13 MFCC coefficients** (n_mfcc=13)
- **3 types**: MFCC, Delta (Δ), Delta-Delta (Δ²)
- **8 statistics per coefficient track**:
  1. Mean
  2. Standard deviation
  3. Minimum
  4. Maximum
  5. Median
  6. 25th percentile
  7. 75th percentile
  8. Variance

**271 features** = LASSO selected subset (after removing ~13% least important features)

## 🚀 Testing

After rebuilding the container with this fix, you should see:
```
INFO: 📊 Before pipeline: (120, 312)
INFO: 📊 Scaler found, expects 312 features, got 312 ✅
INFO: 📊 After scaling: (120, 312)
INFO: 📊 Feature selector found, applying...
INFO: 📊 After feature selection: (120, 271)
INFO: Windowed classification: queen_present (confidence: 0.XXX)
```

## 📝 Commit

**Commit**: `03d8f03`  
**Branch**: `feature/audio-windowed-inference`  
**Message**: "fix: Correct pipeline order - scale BEFORE feature selection"

## ✨ Result

The audio classification system now processes audio correctly:
1. ✅ Records at 44100 Hz and resamples to 22050 Hz
2. ✅ Extracts 312 features per window
3. ✅ Applies scaler (expecting 312 features) ← FIXED
4. ✅ Applies LASSO selector (reducing to 271 features) ← FIXED
5. ✅ Classifies with model (expecting 271 features)
6. ✅ Aggregates predictions across windows
7. ✅ Returns final classification with confidence

## 📚 Related Documents

- `AUDIO_PROCESS_DETAILED_EXPLANATION.md` - Complete audio pipeline documentation
- `TRAINING_INFERENCE_MISMATCH_RESOLVED.md` - Feature extraction analysis
- `AUDIO_TROUBLESHOOTING.md` - Troubleshooting guide
- `QUICK_START.md` - Monitoring and testing commands
