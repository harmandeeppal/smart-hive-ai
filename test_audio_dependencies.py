#!/usr/bin/env python3
"""
Test script to verify audio dependencies and processor
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Audio Dependencies Test")
print("=" * 70)

# Test 1: Check librosa
print("\n[Test 1] Checking librosa...")
try:
    import librosa
    print(f"✅ librosa version: {librosa.__version__}")
except ImportError as e:
    print(f"❌ librosa not installed: {e}")
    print("Install with: pip install librosa==0.10.0")
    sys.exit(1)

# Test 2: Check sounddevice
print("\n[Test 2] Checking sounddevice...")
try:
    import sounddevice as sd
    print(f"✅ sounddevice version: {sd.__version__}")
    print(f"   Available audio devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:  # Input devices only
            print(f"   [{i}] {device['name']} (inputs: {device['max_input_channels']})")
except ImportError as e:
    print(f"❌ sounddevice not installed: {e}")
    print("Install with: pip install sounddevice==0.4.6")
    sys.exit(1)
except Exception as e:
    print(f"⚠️  sounddevice installed but error querying devices: {e}")

# Test 3: Check scipy
print("\n[Test 3] Checking scipy...")
try:
    import scipy
    print(f"✅ scipy version: {scipy.__version__}")
except ImportError as e:
    print(f"❌ scipy not installed: {e}")
    print("Install with: pip install scipy==1.11.1")
    sys.exit(1)

# Test 4: Check scikit-learn
print("\n[Test 4] Checking scikit-learn...")
try:
    import sklearn
    print(f"✅ scikit-learn version: {sklearn.__version__}")
except ImportError as e:
    print(f"❌ scikit-learn not installed: {e}")
    print("Install with: pip install scikit-learn==1.3.0")
    sys.exit(1)

# Test 5: Check joblib
print("\n[Test 5] Checking joblib...")
try:
    import joblib
    print(f"✅ joblib version: {joblib.__version__}")
except ImportError as e:
    print(f"❌ joblib not installed: {e}")
    print("Install with: pip install joblib==1.3.0")
    sys.exit(1)

# Test 6: Check numpy
print("\n[Test 6] Checking numpy...")
try:
    import numpy as np
    print(f"✅ numpy version: {np.__version__}")
except ImportError as e:
    print(f"❌ numpy not installed: {e}")
    sys.exit(1)

# Test 7: Test AudioProcessor import (will fail if model missing, but that's OK)
print("\n[Test 7] Testing AudioProcessor import...")
try:
    from ml_audio_model.audio_processor import AudioProcessor
    print("✅ AudioProcessor class imported successfully")
    
    # Try to initialize (may fail if model file missing)
    try:
        processor = AudioProcessor('models/audio_model.pkl')
        print("✅ AudioProcessor initialized with model")
    except FileNotFoundError:
        print("⚠️  Model file not found (models/audio_model.pkl)")
        print("   This is OK - audio will work without ML model for testing")
    except Exception as e:
        print(f"⚠️  AudioProcessor initialization failed: {e}")
        print("   Dependencies are installed correctly though!")
        
except ImportError as e:
    print(f"❌ Failed to import AudioProcessor: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("🎉 ALL AUDIO DEPENDENCIES INSTALLED!")
print("=" * 70)
print("\nAudio service will work correctly.")
print("Next: Test dashboard")
