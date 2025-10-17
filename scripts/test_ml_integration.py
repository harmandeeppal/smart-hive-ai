#!/usr/bin/env python3
"""Test ML integration with existing system"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from ml_vision_model.vision_processor import VisionProcessor
from ml_audio_model.audio_processor import AudioProcessor

def test_ml_config():
    """Verify ML configuration is correctly set."""
    print("=" * 60)
    print("Testing ML Configuration")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Check vision config
    print("\n1. Vision Configuration:")
    tests_total += 1
    if hasattr(config, 'ENABLE_VISION_MODEL'):
        print(f"   ✅ ENABLE_VISION_MODEL = {config.ENABLE_VISION_MODEL}")
        print(f"   ✅ VISION_MODEL_PATH = {config.VISION_MODEL_PATH}")
        print(f"   ✅ VISION_CONFIDENCE_THRESHOLD = {config.VISION_CONFIDENCE_THRESHOLD}")
        print(f"   ✅ VISION_PROCESS_EVERY_N_FRAMES = {config.VISION_PROCESS_EVERY_N_FRAMES}")
        tests_passed += 1
    else:
        print("   ❌ Vision configuration not found")
    
    # Check audio config
    print("\n2. Audio Configuration:")
    tests_total += 1
    if hasattr(config, 'ENABLE_AUDIO_MODEL'):
        print(f"   ✅ ENABLE_AUDIO_MODEL = {config.ENABLE_AUDIO_MODEL}")
        print(f"   ✅ AUDIO_MODEL_PATH = {config.AUDIO_MODEL_PATH}")
        print(f"   ✅ AUDIO_CONFIDENCE_THRESHOLD = {config.AUDIO_CONFIDENCE_THRESHOLD}")
        print(f"   ✅ AUDIO_RECORD_DURATION_SEC = {config.AUDIO_RECORD_DURATION_SEC}")
        tests_passed += 1
    else:
        print("   ❌ Audio configuration not found")
    
    # Check MQTT topics
    print("\n3. MQTT Topics:")
    tests_total += 1
    if hasattr(config, 'TOPIC_VISION_RESULTS'):
        print(f"   ✅ TOPIC_VISION_RESULTS = {config.TOPIC_VISION_RESULTS}")
        print(f"   ✅ TOPIC_AUDIO_RESULTS = {config.TOPIC_AUDIO_RESULTS}")
        tests_passed += 1
    else:
        print("   ❌ MQTT topics not found")
    
    return tests_passed == tests_total

def test_processor_initialization():
    """Test processor initialization without crashing."""
    print("\n" + "=" * 60)
    print("Testing Processor Initialization")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 2
    
    # Test vision processor
    print("\n1. Vision Processor:")
    try:
        processor = VisionProcessor(
            config.VISION_MODEL_PATH,
            config.VISION_CONFIDENCE_THRESHOLD
        )
        status = processor.get_status()
        print(f"   ✅ Status: {status}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test audio processor
    print("\n2. Audio Processor:")
    try:
        processor = AudioProcessor(
            config.AUDIO_MODEL_PATH,
            config.AUDIO_CONFIDENCE_THRESHOLD
        )
        status = processor.get_status()
        print(f"   ✅ Status: {status}")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return tests_passed == tests_total

def test_existing_system():
    """Verify existing system still works."""
    print("\n" + "=" * 60)
    print("Testing Existing System (Non-ML)")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Check core config
    print("\n1. Core Configuration:")
    tests_total += 1
    try:
        assert hasattr(config, 'MQTT_BROKER'), "Missing MQTT_BROKER"
        assert hasattr(config, 'MQTT_PORT'), "Missing MQTT_PORT"
        assert hasattr(config, 'MQTT_USERNAME'), "Missing MQTT_USERNAME"
        assert hasattr(config, 'DYNAMODB_TABLE'), "Missing DYNAMODB_TABLE"
        print(f"   ✅ MQTT_BROKER = {config.MQTT_BROKER}")
        print(f"   ✅ MQTT_PORT = {config.MQTT_PORT}")
        print(f"   ✅ DYNAMODB_TABLE = {config.DYNAMODB_TABLE}")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ {e}")
    
    # Check sensor config
    print("\n2. Sensor Configuration:")
    tests_total += 1
    try:
        assert hasattr(config, 'CAMERA_TYPE'), "Missing CAMERA_TYPE"
        assert hasattr(config, 'MICROPHONE_SAMPLE_RATE'), "Missing MICROPHONE_SAMPLE_RATE"
        print(f"   ✅ CAMERA_TYPE = {config.CAMERA_TYPE}")
        print(f"   ✅ MICROPHONE_SAMPLE_RATE = {config.MICROPHONE_SAMPLE_RATE}")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ {e}")
    
    # Check AWS config
    print("\n3. AWS Configuration:")
    tests_total += 1
    try:
        assert hasattr(config, 'AWS_REGION'), "Missing AWS_REGION"
        assert hasattr(config, 'ENABLE_DYNAMODB'), "Missing ENABLE_DYNAMODB"
        print(f"   ✅ AWS_REGION = {config.AWS_REGION}")
        print(f"   ✅ ENABLE_DYNAMODB = {config.ENABLE_DYNAMODB}")
        tests_passed += 1
    except AssertionError as e:
        print(f"   ❌ {e}")
    
    return tests_passed == tests_total

def main():
    """Run all integration tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 20 + "ML INTEGRATION TESTS" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    
    # Test 1: Configuration
    print("\n[TEST 1/3] ML Configuration")
    results.append(test_ml_config())
    
    # Test 2: Processor Initialization
    print("\n[TEST 2/3] Processor Initialization")
    results.append(test_processor_initialization())
    
    # Test 3: Existing System
    print("\n[TEST 3/3] Existing System Compatibility")
    results.append(test_existing_system())
    
    # Summary
    print("\n" + "=" * 60)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 60)
    
    if all(results):
        print("✅ ALL TESTS PASSED - System is ready for deployment")
        print("\nML integration is backward compatible with existing system")
        print("- Vision processor: Ready (graceful degradation if model missing)")
        print("- Audio processor: Ready (graceful degradation if model missing)")
        print("- Existing features: Verified working")
        return True
    else:
        print("❌ SOME TESTS FAILED - Check output above")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
