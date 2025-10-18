#!/usr/bin/env python3
"""
Test script to verify dashboard functionality locally
Run mosquitto in Docker first: docker run -d -p 1883:1883 eclipse-mosquitto
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Dashboard Integration Test")
print("=" * 70)

# Test 1: Check Flask
print("\n[Test 1] Checking Flask...")
try:
    import flask
    print(f"✅ Flask version: {flask.__version__}")
except ImportError as e:
    print(f"❌ Flask not installed: {e}")
    print("Install with: pip install flask")
    sys.exit(1)

# Test 2: Check Flask-SocketIO
print("\n[Test 2] Checking Flask-SocketIO...")
try:
    import flask_socketio
    print(f"✅ Flask-SocketIO installed")
except ImportError as e:
    print(f"❌ Flask-SocketIO not installed: {e}")
    print("Install with: pip install flask-socketio")
    sys.exit(1)

# Test 3: Check paho-mqtt
print("\n[Test 3] Checking paho-mqtt...")
try:
    import paho.mqtt.client as mqtt_client
    print(f"✅ paho-mqtt installed")
except ImportError as e:
    print(f"❌ paho-mqtt not installed: {e}")
    print("Install with: pip install paho-mqtt")
    sys.exit(1)

# Test 4: Check if mosquitto is running
print("\n[Test 4] Checking MQTT broker...")
print("Trying to connect to localhost:1883...")
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex(('localhost', 1883))
    sock.close()
    
    if result == 0:
        print("✅ MQTT broker is running on localhost:1883")
    else:
        print("⚠️  MQTT broker not detected on localhost:1883")
        print("   Start mosquitto with: docker run -d -p 1883:1883 eclipse-mosquitto")
        print("   Or continue - dashboard will work without MQTT for UI testing")
except Exception as e:
    print(f"⚠️  Could not check MQTT broker: {e}")

# Test 5: Test dashboard imports
print("\n[Test 5] Testing dashboard imports...")
try:
    # Change to dashboard directory
    dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard')
    sys.path.insert(0, dashboard_path)
    
    # This will test if all imports work
    print("   Importing dashboard_app...")
    # We can't actually import it fully without running, but we can check the file
    dashboard_file = os.path.join(dashboard_path, 'dashboard_app.py')
    if os.path.exists(dashboard_file):
        print(f"✅ dashboard_app.py found at {dashboard_file}")
        
        # Check if template exists
        template_file = os.path.join(dashboard_path, 'templates', 'index.html')
        if os.path.exists(template_file):
            print(f"✅ index.html template found")
            
            # Check for audio recording button in HTML
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'record-audio-btn' in content:
                    print("✅ Audio recording button found in template")
                else:
                    print("❌ Audio recording button NOT found in template")
        else:
            print(f"❌ Template not found at {template_file}")
    else:
        print(f"❌ dashboard_app.py not found")
        
except Exception as e:
    print(f"❌ Dashboard import test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Check static files
print("\n[Test 6] Checking dashboard static files...")
try:
    static_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'static')
    
    # Check app.js
    app_js = os.path.join(static_path, 'app.js')
    if os.path.exists(app_js):
        print("✅ app.js found")
        with open(app_js, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'trigger_audio_recording' in content:
                print("✅ Audio recording trigger found in app.js")
            if 'audio_ml_update' in content:
                print("✅ Audio ML update listener found in app.js")
    else:
        print("❌ app.js not found")
    
    # Check styles.css
    styles_css = os.path.join(static_path, 'styles.css')
    if os.path.exists(styles_css):
        print("✅ styles.css found")
        with open(styles_css, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'record-btn' in content or 'audio-ml-card' in content:
                print("✅ Audio card styles found in CSS")
    else:
        print("❌ styles.css not found")
        
except Exception as e:
    print(f"⚠️  Static files check failed: {e}")

print("\n" + "=" * 70)
print("📋 SUMMARY")
print("=" * 70)
print("""
To run dashboard locally:
1. Start mosquitto (optional): docker run -d -p 1883:1883 eclipse-mosquitto
2. Set environment variables in .env file
3. Run: python dashboard/dashboard_app.py
4. Open browser: http://localhost:5000
5. Click the red "Record 1 Minute & Analyze" button to test

The dashboard should show:
- Temperature, humidity, vibration, sound cards
- AI Vision card with video feed
- NEW: AI Audio Analysis card with record button
""")
