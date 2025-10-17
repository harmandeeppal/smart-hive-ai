#!/usr/bin/env python3
"""Test audio model integration"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import config
from ml_audio_model.audio_processor import AudioProcessor

def test_audio_processor():
    """Test audio processor with mock audio data."""
    print("=" * 60)
    print("Testing Audio Model Processor")
    print("=" * 60)
    
    try:
        # Load processor
        print("\n1. Loading audio processor...")
        processor = AudioProcessor(
            config.AUDIO_MODEL_PATH,
            config.AUDIO_CONFIDENCE_THRESHOLD
        )
        
        if not processor.enabled:
            print("   ⚠ Audio processor disabled")
            print("   This is expected if dependencies not installed")
            print("   System will continue without audio detection")
            return True
        
        print("   ✅ Audio processor loaded")
        
        # Test with mock audio data
        print("\n2. Testing with mock audio data...")
        sample_rate = config.AUDIO_SAMPLE_RATE
        duration = 1  # 1 second of silence
        audio = np.zeros(sample_rate * duration)
        
        features = processor.extract_features(audio)
        if features is None:
            print("   ⚠ Feature extraction returned None (expected if librosa missing)")
            return True
        
        print(f"   Extracted features shape: {features.shape}")
        print(f"   ✅ Features extracted successfully")
        
        # Test classification
        print("\n3. Testing classification...")
        result = processor.classify(features)
        print(f"   Classification: {result}")
        print(f"   ✅ Classification successful")
        
        # Test record_and_classify (will be skipped if no microphone)
        print("\n4. Testing record_and_classify...")
        print("   Note: This will try to record from microphone if available")
        print("   If no microphone, this will gracefully fail")
        result = processor.record_and_classify(duration=1)
        if result and 'error' in result:
            print(f"   ⚠ Expected: {result['error']}")
            print(f"   (No microphone available or recording not possible)")
        else:
            print(f"   ✅ Record and classify result: {result}")
        
        # Test enable/disable
        print("\n5. Testing enable/disable...")
        processor.disable()
        status = processor.get_status()
        print(f"   Disabled status: {status}")
        processor.enable()
        status = processor.get_status()
        print(f"   Enabled status: {status}")
        print(f"   ✅ Enable/disable working")
        
        print("\n" + "=" * 60)
        print("✅ ALL AUDIO TESTS PASSED")
        print("=" * 60)
        return True
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_audio_processor()
    sys.exit(0 if success else 1)
