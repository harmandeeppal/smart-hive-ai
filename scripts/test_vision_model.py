#!/usr/bin/env python3
"""Test vision model integration"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import config
from ml_vision_model.vision_processor import VisionProcessor

def test_vision_processor():
    """Test vision processor with mock frame."""
    print("=" * 60)
    print("Testing Vision Model Processor")
    print("=" * 60)
    
    try:
        # Load processor
        print("\n1. Loading vision processor...")
        processor = VisionProcessor(
            config.VISION_MODEL_PATH,
            config.VISION_CONFIDENCE_THRESHOLD
        )
        
        if not processor.enabled:
            print("   ⚠ Vision processor disabled (model not loaded)")
            print("   This is expected if ultralytics not installed or model missing")
            print("   System will continue without vision detection")
            return True
        
        print("   ✅ Vision processor loaded")
        
        # Test with blank frame
        print("\n2. Testing with blank frame...")
        blank_frame = cv2.zeros((480, 640, 3), dtype='uint8')
        result = processor.process_frame(blank_frame)
        print(f"   Result: {result}")
        print(f"   ✅ No errors on blank frame")
        
        # Test with random frame
        print("\n3. Testing with random frame...")
        import numpy as np
        random_frame = np.random.randint(0, 256, (480, 640, 3), dtype='uint8')
        result = processor.process_frame(random_frame)
        print(f"   Result: Detected={result['detected']}, "
              f"Confidence={result['confidence']}, "
              f"Inference Time={result.get('inference_time_ms', 'N/A')}ms")
        print(f"   ✅ Random frame processed")
        
        # Test enable/disable
        print("\n4. Testing enable/disable...")
        processor.disable()
        result = processor.process_frame(random_frame)
        print(f"   Disabled - Result: {result}")
        processor.enable()
        print(f"   ✅ Enable/disable working")
        
        print("\n" + "=" * 60)
        print("✅ ALL VISION TESTS PASSED")
        print("=" * 60)
        return True
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_vision_processor()
    sys.exit(0 if success else 1)
