#!/usr/bin/env python3
"""
Enhanced Queen Bee Detection System (Windowed)
Features: MFCC + Delta + Delta-Delta statistics per 10s window
LASSO feature selection + Multiple classifiers (RF, SVM, LR)

Notes:
- Audio is split into 10-second windows (non-overlapping by default).
- Training/test split is done at the FILE level to prevent leakage.
- Inference aggregates window predictions to a single file-level decision.
"""

import os
import warnings
warnings.filterwarnings('ignore')

import joblib
import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression, LassoCV
from sklearn.feature_selection import SelectFromModel
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score


# =========================
# Config
# =========================
SR = 22050               # target sample rate
N_FFT = 2048
HOP = 512
N_MFCC = 13
WINDOW_SECONDS = 1.0    # <-- window size
HOP_SECONDS = 0.5       # non-overlapping; set < WINDOW_SECONDS for overlap


# =========================
# Data loading
# =========================
def load_audio_data(data_path='data/'):
    """Load audio file paths and labels from folder names."""
    audio_files, labels = [], []

    present = os.path.join(data_path, 'queen_present')
    if os.path.exists(present):
        for f in os.listdir(present):
            if f.lower().endswith(('.wav', '.mp3', '.flac')):
                audio_files.append(os.path.join(present, f))
                labels.append('queen_present')

    absent = os.path.join(data_path, 'queen_absent')
    if os.path.exists(absent):
        for f in os.listdir(absent):
            if f.lower().endswith(('.wav', '.mp3', '.flac')):
                audio_files.append(os.path.join(absent, f))
                labels.append('queen_absent')

    print(f"Found {len(audio_files)} audio files:")
    print(f"  Queen present: {labels.count('queen_present')}")
    print(f"  Queen absent:  {labels.count('queen_absent')}")
    return audio_files, labels


# =========================
# Windowing
# =========================
def window_audio(audio, sr, window_seconds=WINDOW_SECONDS, hop_seconds=HOP_SECONDS,
                 include_partial_last=True):
    """
    Slice a 1-D audio array into windows.
    Returns a list of 1-D arrays (each a window).
    """
    win = int(round(window_seconds * sr))
    hop = int(round(hop_seconds * sr))
    if hop <= 0:
        hop = win

    windows = []
    n = len(audio)
    start = 0
    while start + win <= n:
        windows.append(audio[start:start+win])
        start += hop

    if include_partial_last and start < n:
        # Include tail shorter than win
        windows.append(audio[start:n])

    return windows


# =========================
# Feature extraction
# =========================
def _extract_features_from_array(y, sr, n_mfcc=N_MFCC, n_fft=N_FFT, hop_length=HOP):
    """
    Extract MFCC + Delta + Delta-Delta statistics over ALL frames of y.
    Returns a 312-D vector (13 coeffs × 3 types × 8 stats).
    """
    # Frame-level features
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc, n_fft=n_fft, hop_length=hop_length)
    delta = librosa.feature.delta(mfccs, order=1)
    delta2 = librosa.feature.delta(mfccs, order=2)

    # Aggregate stats across time for each coefficient track
    feat = []
    for mat in (mfccs, delta, delta2):
        for coeff in mat:  # coeff has shape (T,)
            feat.extend([
                np.mean(coeff), np.std(coeff), np.min(coeff), np.max(coeff),
                np.median(coeff), np.percentile(coeff, 25),
                np.percentile(coeff, 75), np.var(coeff)
            ])
    return np.array(feat, dtype=np.float32)


def extract_enhanced_mfcc_features(audio_file, sr=SR, window_seconds=WINDOW_SECONDS,
                                   hop_seconds=HOP_SECONDS, include_partial_last=True):
    """
    Load a file, split into windows, and compute 312-D features per window.
    Returns:
      features: np.ndarray [num_windows, 312]
    """
    try:
        y, _sr = librosa.load(audio_file, sr=sr)  # mono, resampled
        wins = window_audio(y, _sr, window_seconds, hop_seconds, include_partial_last)
        feats = []
        for w in wins:
            feats.append(_extract_features_from_array(w, _sr))
        if not feats:
            return np.empty((0, 312), dtype=np.float32)
        return np.vstack(feats)
    except Exception as e:
        print(f"Error processing {audio_file}: {e}")
        return np.empty((0, 312), dtype=np.float32)


def create_windowed_feature_dataset(audio_files, labels,
                                    window_seconds=WINDOW_SECONDS, hop_seconds=HOP_SECONDS,
                                    include_partial_last=True):
    """
    For each file, create features for all windows, and replicate its label per window.
    Returns window-level (features, labels).
    """
    X_list, y_list = [], []
    print(f"Windowizing {len(audio_files)} files with {window_seconds}s windows (hop {hop_seconds}s)...")
    for i, (path, lbl) in enumerate(zip(audio_files, labels)):
        if i % 10 == 0:
            print(f"  Processing {i+1}/{len(audio_files)}")
        feats = extract_enhanced_mfcc_features(
            path, sr=SR, window_seconds=window_seconds, hop_seconds=hop_seconds,
            include_partial_last=include_partial_last
        )
        if feats.size > 0:
            X_list.append(feats)
            y_list.append(np.array([lbl]*feats.shape[0], dtype=object))

    if not X_list:
        return np.empty((0, 312), dtype=np.float32), np.empty((0,), dtype=object)

    X = np.vstack(X_list)
    y = np.concatenate(y_list)
    print(f"Created {X.shape[0]} windows; feature dim = {X.shape[1]}")
    return X, y


# =========================
# Feature selection (LASSO)
# =========================
def perform_lasso_feature_selection(X_train, y_train):
    """Perform LASSO-based feature selection on scaled training data."""
    print("Performing LASSO feature selection...")
    lasso_cv = LassoCV(alphas=np.logspace(-4, 1, 50), cv=5, random_state=42, max_iter=2000)
    lasso_cv.fit(X_train, y_train)

    print(f"Optimal alpha: {lasso_cv.alpha_:.6f}")
    selector = SelectFromModel(lasso_cv, prefit=True)
    X_train_sel = selector.transform(X_train)

    print(f"Features: {X_train.shape[1]} -> {X_train_sel.shape[1]} "
          f"({(1 - X_train_sel.shape[1]/X_train.shape[1]) * 100:.1f}% reduction)")
    return selector, lasso_cv


# =========================
# Preprocessing utilities
# =========================
def preprocess_already_split(X_train, X_test, y_train_str, y_test_str):
    """
    Scale + LASSO-select on pre-split window-level data.
    Returns encoded labels and fitted scaler/selector/label_encoder.
    """
    # Encode labels
    label_encoder = LabelEncoder()
    label_encoder.fit(np.unique(np.concatenate([y_train_str, y_test_str])))
    y_train = label_encoder.transform(y_train_str)
    y_test = label_encoder.transform(y_test_str)

    # Scale
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc = scaler.transform(X_test)

    # LASSO selection
    selector, _ = perform_lasso_feature_selection(X_train_sc, y_train)
    X_train_fin = selector.transform(X_train_sc)
    X_test_fin = selector.transform(X_test_sc)

    return X_train_fin, X_test_fin, y_train, y_test, scaler, label_encoder, selector


# =========================
# Modeling
# =========================
def train_models(X_train, X_test, y_train, y_test, label_encoder):
    """Train and evaluate RF, SVM (RBF), and Logistic Regression on window-level data."""
    models = {
        'Random Forest': RandomForestClassifier(
            n_estimators=200, max_depth=15, min_samples_split=5, random_state=42
        ),
        'SVM': SVC(kernel='rbf', C=10, gamma='scale', probability=True, random_state=42),
        'Logistic Regression': LogisticRegression(C=1.0, max_iter=2000, random_state=42)
    }

    results = {}
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        results[name] = {'model': model, 'accuracy': acc, 'predictions': y_pred}
        print(f"{name} Accuracy (window-level): {acc:.4f}")
        print("Classification Report (window-level):")
        print(classification_report(y_test, y_pred, target_names=label_encoder.classes_, digits=4))
    return results


# =========================
# Visualization
# =========================
def visualize_results(results, y_test, label_encoder):
    """Bar chart of accuracies + confusion matrices (window-level)."""
    accuracies = [results[m]['accuracy'] for m in results]
    names = list(results.keys())

    plt.figure(figsize=(10, 6))
    bars = plt.bar(names, accuracies, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    plt.title('Model Performance Comparison (Window-Level)')
    plt.ylabel('Accuracy')
    plt.ylim(0.5, 1.0)
    for b, a in zip(bars, accuracies):
        plt.text(b.get_x() + b.get_width()/2, b.get_height() + 0.01, f'{a:.4f}',
                 ha='center', va='bottom', fontweight='bold')
    plt.show()

    fig, axes = plt.subplots(1, len(results), figsize=(15, 5))
    if len(results) == 1: axes = [axes]
    for i, (name, res) in enumerate(results.items()):
        cm = confusion_matrix(y_test, res['predictions'])
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[i],
                    xticklabels=label_encoder.classes_,
                    yticklabels=label_encoder.classes_)
        axes[i].set_title(f'{name}\nAcc: {res["accuracy"]:.4f}')
        axes[i].set_ylabel('Actual')
        axes[i].set_xlabel('Predicted')
    plt.tight_layout()
    plt.show()


# =========================
# Cross-validation on windows
# =========================
def cross_validate_pipeline(features, labels, cv_folds=5):
    """CV on window-level features (scaler + LASSO + RF pipeline)."""
    print(f"Cross-validation with {cv_folds} folds (window-level)...")
    le = LabelEncoder()
    y = le.fit_transform(labels)
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('lasso_selection', SelectFromModel(LassoCV(cv=3, random_state=42, max_iter=2000))),
        ('classifier', RandomForestClassifier(n_estimators=100, random_state=42)),
    ])
    scores = cross_val_score(pipe, features, y, cv=cv_folds, scoring='accuracy')
    print(f"CV scores: {scores}")
    print(f"Mean CV accuracy: {scores.mean():.4f} (+/- {scores.std()*2:.4f})")
    return scores


# =========================
# Save & Predict (with window aggregation)
# =========================
def save_model(model, scaler, label_encoder, feature_selector, model_path='queen_bee_model.pkl'):
    """Save model and preprocessors."""
    joblib.dump({
        'model': model,
        'scaler': scaler,
        'label_encoder': label_encoder,
        'feature_selector': feature_selector
    }, model_path)
    print(f"Model saved to {model_path}")


def predict_queen_presence(audio_file, model_components,
                           window_seconds=WINDOW_SECONDS, hop_seconds=HOP_SECONDS,
                           include_partial_last=True, agg='mean_proba'):
    """
    Predict queen presence for a file by scoring all windows and aggregating.
    Returns (predicted_label, confidence).
    - If proba available: confidence = mean probability of the chosen class.
    - Else: confidence = fraction of windows voting for the chosen class.
    """
    # Extract window-level features
    feats = extract_enhanced_mfcc_features(
        audio_file, sr=SR, window_seconds=window_seconds,
        hop_seconds=hop_seconds, include_partial_last=include_partial_last
    )
    if feats.size == 0:
        return None, None

    scaler = model_components['scaler']
    selector = model_components['feature_selector']
    model = model_components['model']
    le = model_components['label_encoder']

    Xs = selector.transform(scaler.transform(feats))

    if hasattr(model, 'predict_proba'):
        probs = model.predict_proba(Xs)  # [n_windows, n_classes]
        mean_probs = probs.mean(axis=0)  # aggregate across windows
        pred_idx = int(np.argmax(mean_probs))
        pred_label = le.inverse_transform([pred_idx])[0]
        confidence = float(mean_probs[pred_idx])  # mean prob of chosen class
        return pred_label, confidence
    else:
        preds = model.predict(Xs)
        # Majority vote
        unique, counts = np.unique(preds, return_counts=True)
        pred_idx = int(unique[np.argmax(counts)])
        pred_label = le.inverse_transform([pred_idx])[0]
        confidence = float(np.max(counts) / len(preds))  # vote share
        return pred_label, confidence


# =========================
# Main
# =========================
def main():
    print("=== Enhanced Queen Bee Detection (10s Windowed) ===\n")

    # Step 1: File list + labels
    audio_files, labels = load_audio_data('data/')
    print()

    # Step 2: Split by FILE (prevents train/test leakage across windows)
    f_train, f_test, y_train_files, y_test_files = train_test_split(
        audio_files, labels, test_size=0.2, random_state=42, stratify=labels
    )
    print(f"Train files: {len(f_train)} | Test files: {len(f_test)}\n")

    # Step 3: Build window-level datasets for each split
    print("Extracting window-level features (train)...")
    X_train_win, y_train_win = create_windowed_feature_dataset(
        f_train, y_train_files, window_seconds=WINDOW_SECONDS, hop_seconds=HOP_SECONDS, include_partial_last=True
    )
    print("Extracting window-level features (test)...")
    X_test_win, y_test_win = create_windowed_feature_dataset(
        f_test, y_test_files, window_seconds=WINDOW_SECONDS, hop_seconds=HOP_SECONDS, include_partial_last=True
    )
    print()

    if X_train_win.shape[0] == 0 or X_test_win.shape[0] == 0:
        print("No windows were created. Check your data and window settings.")
        return

    print(f"Train windows: {X_train_win.shape[0]} | Test windows: {X_test_win.shape[0]}")
    print(f"Feature dimension: {X_train_win.shape[1]} (13 MFCC × 3 types × 8 stats)\n")

    # Step 4: Preprocess (scale + LASSO select) on pre-split data
    X_train, X_test, y_train, y_test, scaler, label_encoder, selector = preprocess_already_split(
        X_train_win, X_test_win, y_train_win, y_test_win
    )

    # Step 5: Train models (window-level metrics)
    results = train_models(X_train, X_test, y_train, y_test, label_encoder)
    print()

    # Step 6: Pick best by window-level accuracy
    best_name = max(results, key=lambda k: results[k]['accuracy'])
    best_model = results[best_name]['model']
    best_acc = results[best_name]['accuracy']
    print(f"Best model: {best_name} (window-level Acc: {best_acc:.4f})\n")

    # Step 7: Visualize window-level performance
    visualize_results(results, y_test, label_encoder)

    # Step 8: Cross-validation on ALL windows (train+test combined)
    X_all = np.vstack([X_train_win, X_test_win])
    y_all = np.concatenate([y_train_win, y_test_win])
    cv_scores = cross_validate_pipeline(X_all, y_all)
    print()

    # Step 9: Save best model + preprocessors
    save_model(best_model, scaler, label_encoder, selector)
    print("\n=== Pipeline Complete ===")

    # Example usage
    print("\n=== Example Usage ===")
    print("model_components = joblib.load('queen_bee_model.pkl')")
    print("prediction, confidence = predict_queen_presence('new_audio.wav', model_components)")
    print("print('Prediction:', prediction, 'Confidence:', confidence)")
    print("Tip: You can set overlap by using HOP_SECONDS < WINDOW_SECONDS in predict_queen_presence().")


if __name__ == "__main__":
    main()
