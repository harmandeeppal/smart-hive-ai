#!/usr/bin/env python3
"""
Video Feed Diagnostic Test
Tests if the edge-app video feed is generating valid MJPEG frames
"""

import requests
import time

def test_video_feed():
    """Test video feed from edge-app"""
    print("=" * 70)
    print("Video Feed Diagnostic Test")
    print("=" * 70)
    
    # Test 1: Check if endpoint responds
    print("\n[Test 1] Testing video feed endpoint...")
    try:
        response = requests.get("http://192.168.88.16:5001/video_feed", stream=True, timeout=5)
        print(f"✅ Status Code: {response.status_code}")
        print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
        
        # Test 2: Check if we receive actual frame data
        print("\n[Test 2] Checking for frame data...")
        chunk_count = 0
        total_bytes = 0
        start_time = time.time()
        
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                chunk_count += 1
                total_bytes += len(chunk)
                
                # Check first chunk for MJPEG boundary
                if chunk_count == 1:
                    if b'--frame' in chunk:
                        print(f"✅ Found MJPEG boundary marker in first chunk")
                    else:
                        print(f"❌ No MJPEG boundary found! First bytes: {chunk[:50]}")
                
                # Stop after 3 seconds
                if time.time() - start_time > 3:
                    break
        
        print(f"✅ Received {chunk_count} chunks ({total_bytes} bytes) in 3 seconds")
        
        if chunk_count > 0 and total_bytes > 1000:
            print("\n✅ Video feed appears to be working!")
            print("   The issue might be browser-specific rendering.")
        else:
            print("\n❌ Video feed not generating enough data!")
            print("   Possible camera initialization issue.")
            
    except requests.exceptions.Timeout:
        print("❌ Connection timeout - video feed not responding")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_video_feed()
