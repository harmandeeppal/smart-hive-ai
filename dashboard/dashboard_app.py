"""
Smart Hive AI - Dashboard Application

Description:
    Web-based dashboard for real-time beehive monitoring and visualization.
    Provides live sensor data display, video streaming, and sensor control
    through a responsive web interface using Flask and Socket.IO.

Author: Smart Hive AI Team
Created: 2024
Last Modified: October 2025

Dependencies:
    - Flask: Web application framework
    - Flask-SocketIO: WebSocket support for real-time updates
    - paho-mqtt: MQTT client for subscribing to telemetry data
    - requests: HTTP client for video stream proxying

Features:
    - Real-time telemetry data visualization
    - Live video streaming with AI detection overlays
    - Interactive sensor enable/disable controls
    - WebSocket-based data updates
    - MQTT integration with AWS IoT Core

Routes:
    - /: Main dashboard page
    - /video_feed: Video stream proxy from edge application
    - /toggle_sensor: Sensor control endpoint

Usage:
    Run as part of Docker Compose stack or standalone:
    python dashboard_app.py
    
    Access at: http://localhost:5000
"""

import json
import ssl
import time
import threading
import requests
from flask import Response
from flask import Flask, render_template
from flask_socketio import SocketIO
from paho.mqtt import client as mqtt_client_module

# Import main configuration from parent directory
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
socketio = SocketIO(app, async_mode='threading')

# Initialize MQTT client for telemetry subscription
mqtt_client = mqtt_client_module.Client(mqtt_client_module.CallbackAPIVersion.VERSION2, client_id="SmartHive_Dashboard")


# MQTT Callback functions (must be at module level to prevent garbage collection)
def on_connect(client, userdata, flags, rc, properties=None):
    """
    Callback for MQTT connection establishment.
    
    Args:
        client: MQTT client instance
        userdata: User data (unused)
        flags: Connection flags
        rc: Connection result code
        properties: Connection properties (MQTT v5)
    """
    print(f"🔗 on_connect callback fired! RC={rc}")
    if rc == 0:
        print("✅ Dashboard MQTT client connected successfully.")
        # Subscribe to telemetry, vision, and ML topics
        print(f"📡 Subscribing to: {config.TOPIC_TELEMETRY}")
        result1, mid1 = client.subscribe(config.TOPIC_TELEMETRY)
        print(f"   Result: {result1}, MID: {mid1}")
        
        print(f"📡 Subscribing to: {config.TOPIC_VISION}")
        result2, mid2 = client.subscribe(config.TOPIC_VISION)
        print(f"   Result: {result2}, MID: {mid2}")
        
        print(f"📡 Subscribing to: {config.TOPIC_VISION_RESULTS}")
        result3, mid3 = client.subscribe(config.TOPIC_VISION_RESULTS)
        print(f"   Result: {result3}, MID: {mid3}")
        
        print(f"📡 Subscribing to: {config.TOPIC_AUDIO_RESULTS}")
        result4, mid4 = client.subscribe(config.TOPIC_AUDIO_RESULTS)
        print(f"   Result: {result4}, MID: {mid4}")
        
        print("✅ All MQTT subscription requests sent")
    else:
        print(f"❌ Dashboard MQTT failed to connect, reason code {rc}")


def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """Callback when subscription is acknowledged by broker."""
    print(f"🔔 Subscription confirmed by broker: mid={mid}, QoS={granted_qos}")


def on_message(client, userdata, msg):
    """
    Callback for incoming MQTT messages.
    
    Parses JSON payload and emits data to connected WebSocket clients
    via Socket.IO for real-time dashboard updates.
    
    Args:
        client: MQTT client instance
        userdata: User data (unused)
        msg: MQTT message with topic and payload
    """
    print(f"📥 Received MQTT message on topic: {msg.topic}")
    try:
        payload = json.loads(msg.payload.decode())
        print(f"   Payload: {payload}")
        
        # Route message to appropriate WebSocket event
        if msg.topic == config.TOPIC_TELEMETRY:
            print("   → Emitting 'telemetry_update' via Socket.IO")
            socketio.emit('telemetry_update', payload, namespace='/')
        elif msg.topic == config.TOPIC_VISION:
            socketio.emit('vision_update', payload, namespace='/')
        elif msg.topic == config.TOPIC_VISION_RESULTS:
            socketio.emit('vision_ml_update', payload, namespace='/')
        elif msg.topic == config.TOPIC_AUDIO_RESULTS:
            socketio.emit('audio_ml_update', payload, namespace='/')
    except json.JSONDecodeError:
        print(f"❌ Could not decode JSON payload: {msg.payload}")
    except Exception as e:
        print(f"❌ An error occurred in on_message: {e}")
        import traceback
        traceback.print_exc()


@app.route('/video_feed')
def video_feed():
    """
    Proxy video stream from edge application container.
    
    Forwards the MJPEG video stream from the edge-app container running
    on port 5001 to dashboard clients. Handles connection errors gracefully.
    
    Returns:
        Response: Streaming response with video frames or error message
    """
    try:
        # URL of the video stream from edge application container
        video_url = "http://edge-app:5001/video_feed"
        
        # Stream video with chunked transfer encoding
        resp = requests.get(video_url, stream=True, timeout=10)
        
        if resp.status_code == 200:
            # Forward streaming response to client
            return Response(resp.iter_content(chunk_size=1024), 
                            content_type=resp.headers['Content-Type'],
                            status=resp.status_code)
        else:
            # Handle non-200 status codes
            error_message = f"Error fetching stream from edge-app: Status {resp.status_code}"
            return Response(error_message, mimetype='text/plain')
    except requests.exceptions.RequestException as e:
        # Handle connection errors (edge-app not running, network issues)
        error_message = f"Could not connect to video stream at {video_url}: {e}"
        return Response(error_message, mimetype='text/plain')


def setup_mqtt():
    """
    Configure and connect MQTT client to local Mosquitto broker.
    
    Assigns callbacks and connects to broker. Runs MQTT network loop in background thread.
    """
    
    # Assign callbacks (defined at module level)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_subscribe = on_subscribe
    mqtt_client.on_message = on_message
    
    # Connect to local MQTT broker (Mosquitto in Docker)
    # Using docker service name "mosquitto" as hostname
    try:
        mqtt_broker = os.getenv('MQTT_BROKER', 'mosquitto')
        mqtt_port = int(os.getenv('MQTT_PORT', 1883))
        
        print(f"Connecting to MQTT broker at {mqtt_broker}:{mqtt_port}")
        mqtt_client.connect(mqtt_broker, mqtt_port, 60)
        
        # Start MQTT network loop in background thread
        mqtt_client.loop_start()
        print("MQTT client started successfully")
    except Exception as e:
        print(f"Warning: Could not connect to MQTT broker: {e}")
        print("Dashboard will continue running without MQTT updates")


@socketio.on('connect')
def handle_connect():
    """Handle WebSocket client connection event."""
    print('Client connected to dashboard')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket client disconnection event."""
    print('Client disconnected from dashboard')


@socketio.on('toggle_sensor')
def handle_toggle_sensor(data):
    """
    Handle sensor toggle commands from dashboard UI.
    
    Publishes sensor control commands to MQTT control topic for
    edge application to process.
    
    Args:
        data (dict): Toggle command with sensor name and state
                    Example: {"sensor": "temperature", "enabled": true}
    """
    print(f"Received sensor toggle command: {data}")
    
    # Publish control command to MQTT control topic
    # Note: Publishing is thread-safe when using loop_start()
    control_payload = json.dumps({"sensor": data['sensor'], "state": data['state']})
    result = mqtt_client.publish("hive/control", control_payload, qos=1)
    print(f"Published control message with result: {result}")


@socketio.on('toggle_ml_sensor')
def handle_toggle_ml_sensor(data):
    """
    Handle ML model toggle commands from dashboard UI.
    
    Controls ML vision and audio processors through MQTT control topic.
    
    Args:
        data (dict): Toggle command with ML sensor name and state
                    Example: {"sensor": "ml_vision", "state": "on"}
    """
    print(f"Received ML sensor toggle command: {data}")
    
    # Publish ML control command to MQTT control topic
    control_payload = json.dumps({"sensor": data['sensor'], "state": data['state']})
    result = mqtt_client.publish("hive/control", control_payload, qos=1)
    print(f"Published ML control message with result: {result}")


@socketio.on('request_ml_status')
def handle_request_ml_status():
    """
    Handle ML status request from dashboard.
    
    Emits current ML processor status to requesting client.
    """
    ml_status = {
        "vision_enabled": config.ENABLE_VISION_MODEL if hasattr(config, 'ENABLE_VISION_MODEL') else False,
        "audio_enabled": config.ENABLE_AUDIO_MODEL if hasattr(config, 'ENABLE_AUDIO_MODEL') else False,
        "vision_model_path": config.VISION_MODEL_PATH if hasattr(config, 'VISION_MODEL_PATH') else "",
        "audio_model_path": config.AUDIO_MODEL_PATH if hasattr(config, 'AUDIO_MODEL_PATH') else "",
    }
    socketio.emit('ml_status_response', ml_status)


@socketio.on('trigger_audio_recording')
def handle_trigger_audio_recording(data):
    """
    Handle audio recording trigger from dashboard.
    
    Publishes MQTT command to audio service to start 1-minute recording
    and ML classification.
    
    Args:
        data (dict): Recording parameters
                    Example: {"duration": 60}
    """
    print(f"Audio recording trigger received: {data}")
    
    # Publish recording trigger to audio service
    recording_command = {
        "command": "record_and_classify",
        "duration_sec": data.get('duration', 60),  # Default 60 seconds
        "timestamp": int(time.time())
    }
    
    result = mqtt_client.publish(
        "hive/audio/control",
        json.dumps(recording_command),
        qos=1
    )
    print(f"Published audio recording command with result: {result}")
    
    # Acknowledge to client
    socketio.emit('recording_started', {
        "duration": recording_command["duration_sec"],
        "timestamp": recording_command["timestamp"]
    })


@app.route('/')
def index():
    """
    Serve main dashboard page.
    
    Returns:
        str: Rendered HTML template for dashboard interface
    """
    return render_template('index.html')


if __name__ == '__main__':
    """
    Application entry point.
    
    Initializes MQTT client connection and starts Flask-SocketIO server
    with WebSocket support for real-time updates.
    """
    print("Setting up MQTT client...")
    setup_mqtt()
    
    print("Starting Flask-SocketIO server...")
    # Run Socket.IO server on all interfaces, port 5000
    # use_reloader=False prevents double execution in debug mode
    # debug=False for production/Docker deployment
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, 
                 use_reloader=False, allow_unsafe_werkzeug=True)