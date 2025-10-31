#!/usr/bin/env python3
"""
Test script to verify YOLO model loading with pretrained YOLOv8n
This will download the model (~6MB) on first run
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("YOLO Model Loading Test")
print("=" * 70)

# Test 1: Check ultralytics installation
print("\n[Test 1] Checking ultralytics installation...")
try:
    from ultralytics import YOLO
    print("✅ ultralytics imported successfully")
except ImportError as e:
    print(f"❌ Failed to import ultralytics: {e}")
    print("Install with: pip install ultralytics")
    sys.exit(1)

# Test 2: Check PyTorch
print("\n[Test 2] Checking PyTorch...")
try:
    import torch
    print(f"✅ PyTorch version: {torch.__version__}")
except ImportError as e:
    print(f"❌ Failed to import torch: {e}")
    sys.exit(1)

# Test 3: Load pretrained YOLOv8n model
print("\n[Test 3] Loading pretrained YOLOv8n model...")
print("(This will download ~6MB on first run)")
try:
    model = YOLO('yolov8n.pt')
    print("✅ YOLO model loaded successfully!")
    print(f"   Model type: {type(model)}")
    print(f"   Model names: {list(model.names.values())[:10]}...")  # Show first 10 classes
except Exception as e:
    print(f"❌ Failed to load YOLO model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test inference on dummy image
print("\n[Test 4] Testing inference on dummy image...")
try:
    import numpy as np
    import cv2
    
    # Create a dummy 640x480 BGR image
    dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Run inference
    results = model.predict(dummy_image, imgsz=640, conf=0.5, verbose=False)
    print("✅ Inference completed successfully!")
    print(f"   Results type: {type(results)}")
    print(f"   Number of detections: {len(results[0].boxes) if results[0].boxes else 0}")
except Exception as e:
    print(f"❌ Inference failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test VisionProcessor class
print("\n[Test 5] Testing VisionProcessor class...")
try:
    from ml_vision_model.vision_processor import VisionProcessor
    
    # Initialize without camera (like vision service does)
    processor = VisionProcessor(use_camera=False, confidence_threshold=0.7)
    print("✅ VisionProcessor initialized successfully!")
    print(f"   Model enabled: {processor.enabled}")
    print(f"   Model loaded: {processor.model is not None}")
    
    # Test frame processing
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    result = processor.process_frame(test_frame)
    print("✅ Frame processing successful!")
    print(f"   Result: {result}")
    
except Exception as e:
    print(f"❌ VisionProcessor test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("🎉 ALL TESTS PASSED!")
print("=" * 70)
print("\nThe YOLO model will work correctly in the vision service.")
print("Next: Test audio dependencies")
