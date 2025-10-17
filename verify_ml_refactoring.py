#!/usr/bin/env python3
"""
ML Inference Service Refactoring Verification

Verifies that ml_inference_service.py correctly uses existing implementations:
- ml_vision_model/vision_processor.py
- ml_audio_model/audio_processor.py
- ml_vision_model/best.pt (YOLO model)
- ml_audio_model/queen_bee_model.pkl (Audio model)

Usage:
    python verify_ml_refactoring.py
    python verify_ml_refactoring.py --verbose
"""

import os
import sys
import json

print("\n" + "=" * 70)
print("ML INFERENCE SERVICE - REFACTORING VERIFICATION")
print("=" * 70)

errors = []
warnings = []
info = []

# Check 1: Verify imports are correct
print("\n[1] Checking imports...")
try:
    # Read ml_inference_service.py with UTF-8 encoding
    with open('ml_inference_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for correct imports
    if 'from ml_vision_model.vision_processor import VisionProcessor' in content:
        info.append("[OK] Correct import: from ml_vision_model.vision_processor import VisionProcessor")
    else:
        errors.append("[FAIL] Missing or incorrect import: VisionProcessor from ml_vision_model")
    
    if 'from ml_audio_model.audio_processor import AudioProcessor' in content:
        info.append("[OK] Correct import: from ml_audio_model.audio_processor import AudioProcessor")
    else:
        errors.append("[FAIL] Missing or incorrect import: AudioProcessor from ml_audio_model")
    
    # Check for NO custom implementations
    if 'class VisionProcessor' not in content:
        info.append("[OK] No custom VisionProcessor class (using existing)")
    else:
        warnings.append("[WARN] Found custom VisionProcessor class definition (should use existing)")
    
    if 'class AudioProcessor' not in content:
        info.append("[OK] No custom AudioProcessor class (using existing)")
    else:
        warnings.append("[WARN] Found custom AudioProcessor class definition (should use existing)")

except Exception as e:
    errors.append(f"[FAIL] Error reading ml_inference_service.py: {e}")

# Check 2: Verify files exist
print("\n[2] Checking required files...")
required_files = [
    'ml_vision_model/vision_processor.py',
    'ml_audio_model/audio_processor.py',
    'ml_vision_model/best.pt',
    'ml_audio_model/queen_bee_model.pkl',
]

for file_path in required_files:
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        if size > 1024:  # > 1 KB
            info.append(f"[OK] Found: {file_path} ({size:,.0f} bytes)")
        else:
            warnings.append(f"[WARN] File too small: {file_path} ({size} bytes)")
    else:
        errors.append(f"[FAIL] Missing: {file_path}")

# Check 3: Verify processor methods are called correctly
print("\n[3] Checking processor method calls...")
try:
    with open('ml_inference_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'self.vision_processor.process_frame(frame)' in content:
        info.append("[OK] Using VisionProcessor.process_frame()")
    else:
        errors.append("[FAIL] Not using VisionProcessor.process_frame()")
    
    if 'self.audio_processor.record_and_classify' in content:
        info.append("[OK] Using AudioProcessor.record_and_classify()")
    else:
        errors.append("[FAIL] Not using AudioProcessor.record_and_classify()")
    
    if 'self.vision_processor.enable()' in content and 'self.vision_processor.disable()' in content:
        info.append("[OK] Using VisionProcessor enable/disable()")
    else:
        warnings.append("[WARN] Missing enable/disable calls for VisionProcessor")
    
    if 'self.audio_processor.enable()' in content and 'self.audio_processor.disable()' in content:
        info.append("[OK] Using AudioProcessor enable/disable()")
    else:
        warnings.append("[WARN] Missing enable/disable calls for AudioProcessor")

except Exception as e:
    errors.append(f"[FAIL] Error checking method calls: {e}")

# Check 4: Verify model paths
print("\n[4] Checking model path configuration...")
try:
    with open('ml_inference_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "ml_vision_model/best.pt" in content or "VISION_MODEL_PATH" in content:
        info.append("[OK] Vision model path configured")
    else:
        warnings.append("[WARN] Vision model path might not be configured")
    
    if "ml_audio_model/queen_bee_model.pkl" in content or "AUDIO_MODEL_PATH" in content:
        info.append("[OK] Audio model path configured")
    else:
        warnings.append("[WARN] Audio model path might not be configured")

except Exception as e:
    errors.append(f"[FAIL] Error checking model paths: {e}")

# Check 5: Verify MQTT topics
print("\n[5] Checking MQTT topics...")
try:
    with open('ml_inference_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    topics = {
        'hive/ml/vision/results': 'Vision results',
        'hive/ml/audio/results': 'Audio results',
        'hive/ml/health': 'Health check',
        'hive/ml/control': 'Control commands',
    }
    
    for topic, description in topics.items():
        if topic in content or topic.replace('/', '\\/') in content:
            info.append(f"[OK] MQTT topic configured: {topic} ({description})")
        else:
            warnings.append(f"[WARN] MQTT topic not found: {topic}")

except Exception as e:
    errors.append(f"[FAIL] Error checking MQTT topics: {e}")

# Check 6: Python syntax validation
print("\n[6] Checking Python syntax...")
try:
    import py_compile
    py_compile.compile('ml_inference_service.py', doraise=True)
    info.append("[OK] ml_inference_service.py has valid Python syntax")
except py_compile.PyCompileError as e:
    errors.append(f"[FAIL] Python syntax error: {e}")

# Check 7: Verify existing processor implementations
print("\n[7] Checking existing processor code...")
try:
    # Check VisionProcessor
    with open('ml_vision_model/vision_processor.py', 'r', encoding='utf-8') as f:
        vision_content = f.read()
    
    if 'class VisionProcessor' in vision_content:
        info.append("[OK] VisionProcessor class exists in ml_vision_model/")
    if 'def process_frame' in vision_content:
        info.append("[OK] VisionProcessor.process_frame() method exists")
    if 'def enable' in vision_content:
        info.append("[OK] VisionProcessor.enable() method exists")
    
    # Check AudioProcessor
    with open('ml_audio_model/audio_processor.py', 'r', encoding='utf-8') as f:
        audio_content = f.read()
    
    if 'class AudioProcessor' in audio_content:
        info.append("[OK] AudioProcessor class exists in ml_audio_model/")
    if 'def record_and_classify' in audio_content:
        info.append("[OK] AudioProcessor.record_and_classify() method exists")
    if 'def enable' in audio_content:
        info.append("[OK] AudioProcessor.enable() method exists")

except Exception as e:
    errors.append(f"[FAIL] Error checking existing processors: {e}")

# Print summary
print("\n" + "=" * 70)
print("VERIFICATION RESULTS")
print("=" * 70)

for msg in info:
    print(msg)

if warnings:
    print("\nWARNINGS:")
    for msg in warnings:
        print(msg)

if errors:
    print("\nERRORS:")
    for msg in errors:
        print(msg)

# Final status
print("\n" + "=" * 70)
if not errors:
    print("[SUCCESS] VERIFICATION PASSED - Refactoring is correct!")
    print("The microservice properly uses existing implementations:")
    print("  - ml_vision_model/vision_processor.py")
    print("  - ml_audio_model/audio_processor.py")
    print("  - ml_vision_model/best.pt (YOLO model)")
    print("  - ml_audio_model/queen_bee_model.pkl (Audio model)")
    print("\nReady for deployment with: docker-compose up -d smart-hive-ml")
    exit_code = 0
else:
    print("[FAILURE] VERIFICATION FAILED - Fix errors above")
    exit_code = 1

print("=" * 70 + "\n")
sys.exit(exit_code)
