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
from paho.mqtt import client as mqtt_client

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
mqtt_client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id="SmartHive_Dashboard")


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
    Configure and connect MQTT client to AWS IoT Core.
    
    Sets up TLS connection with AWS IoT Core and subscribes to telemetry
    and vision topics. Implements callbacks for connection and message handling.
    Runs MQTT network loop in background thread.
    """
    
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
        if rc == 0:
            print("Dashboard MQTT client connected successfully.")
            # Subscribe to telemetry and vision topics
            client.subscribe(config.TOPIC_TELEMETRY)
            client.subscribe(config.TOPIC_VISION)
        else:
            print(f"Dashboard MQTT failed to connect, reason code {rc}")

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
        print(f"Received message on topic: {msg.topic}")
        try:
            payload = json.loads(msg.payload.decode())
            
            # Route message to appropriate WebSocket event
            if msg.topic == config.TOPIC_TELEMETRY:
                socketio.emit('telemetry_update', payload)
            elif msg.topic == config.TOPIC_VISION:
                socketio.emit('vision_update', payload)
        except json.JSONDecodeError:
            print(f"Could not decode JSON payload: {msg.payload}")
        except Exception as e:
            print(f"An error occurred in on_message: {e}")
            
    # Assign callbacks
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    # Configure TLS connection with AWS IoT certificates
    mqtt_client.tls_set(ca_certs=config.CA_PATH, 
                       certfile=config.CERT_PATH, 
                       keyfile=config.KEY_PATH,
                       cert_reqs=ssl.CERT_REQUIRED, 
                       tls_version=ssl.PROTOCOL_TLS)
    
    # Connect to AWS IoT Core MQTT broker
    mqtt_client.connect(config.AWS_ENDPOINT, 8883, 60)
    
    # Start MQTT network loop in background thread
    mqtt_client.loop_start()


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
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
                 use_reloader=False, allow_unsafe_werkzeug=True)