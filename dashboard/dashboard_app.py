import json
import ssl
import time # <--- FIX 1: Added missing 'time' import
import threading
from flask import Response
from flask import Flask, render_template
from flask_socketio import SocketIO
# Import the standard Paho MQTT client for modern usage
from paho.mqtt import client as mqtt_client 

# Import the main config
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY 
# Use 'gevent' or 'eventlet' for production, 'threading' is fine for development
socketio = SocketIO(app, async_mode='threading')

# --- MQTT Client Setup ---
# FIX 4: Changed to VERSION2 (or simply removed the argument)
mqtt_client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id="SmartHive_Dashboard")

# --- Video Streaming Placeholder ---
def gen_frames():
    """Generator function for video streaming."""
    while True:
        # Placeholder logic
        time.sleep(1) 
        # In a real app, you'd yield MJPEG frames here:
        # yield (b'--frame\r\n'
        #        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route (Placeholder for MJPEG)."""
    # NOTE: The real MJPEG implementation would return a Response with
    # mimetype='multipart/x-mixed-replace; boundary=frame' and use gen_frames.
    return Response("Video stream will be implemented with Docker.", mimetype='text/plain')


# --- MQTT Client Logic ---

def setup_mqtt():
    """Configures and connects the MQTT client."""
    
    # Callback uses the VERSION2 signature (client, userdata, flags, reason_code, properties)
    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("Dashboard MQTT client connected successfully.")
            # Subscribe to topics upon connection
            client.subscribe(config.TOPIC_TELEMETRY)
            client.subscribe(config.TOPIC_VISION)
        else:
            print(f"Dashboard MQTT failed to connect, reason code {rc}")

    def on_message(client, userdata, msg):
        """Callback for when a message is received from a subscribed topic."""
        print(f"Received message on topic: {msg.topic}")
        try:
            # Note: SocketIO.emit is thread-safe and can be called directly from this MQTT thread
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == config.TOPIC_TELEMETRY:
                socketio.emit('telemetry_update', payload)
            elif msg.topic == config.TOPIC_VISION:
                socketio.emit('vision_update', payload)
        except json.JSONDecodeError:
            print(f"Could not decode JSON payload: {msg.payload}")
        except Exception as e:
            print(f"An error occurred in on_message: {e}")
            
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    # Secure connection setup
    mqtt_client.tls_set(ca_certs=config.CA_PATH, certfile=config.CERT_PATH, keyfile=config.KEY_PATH,
                      cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS)
    
    # Connect and start the network loop
    mqtt_client.connect(config.AWS_ENDPOINT, 8883, 60)
    
    # FIX 3: Start the loop in a background thread and return control.
    mqtt_client.loop_start() 

# --- Socket.IO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    print('Client connected to dashboard')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected from dashboard')

@socketio.on('toggle_sensor')
def handle_toggle_sensor(data):
    """Handles toggle commands and publishes them to the control topic."""
    print(f"Received sensor toggle command: {data}")
    
    # FIX 2: Thread-Safe Publishing. Since we are using loop_start()
    # it is now safer to use the main client for publishing, but for
    # *absolute* robustness, consider creating a small, temporary
    # client here if publishing fails unexpectedly. For simplicity
    # with loop_start(), we continue to use the main client.
    
    control_payload = json.dumps({"sensor": data['sensor'], "state": data['state']})
    # The publish call is generally thread-safe if loop_start() is used.
    result = mqtt_client.publish("hive/control", control_payload, qos=1)
    # The result.rc indicates success/failure of queuing the message, not delivery.
    print(f"Published control message with result: {result}")


# --- Flask Routes ---
@app.route('/')
def index():
    """Serves the main dashboard page."""
    return render_template('index.html')

if __name__ == '__main__':
    print("Setting up MQTT client...")
    # Now we call setup_mqtt directly in the main thread.
    # It handles its own threading with loop_start().
    setup_mqtt() 
    
    print("Starting Flask-SocketIO server...")
    # NOTE: The debug=True setting in socketio.run can interfere with threading.
    # use_reloader=False is good, as it prevents the code from running twice.
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
                 use_reloader=False, allow_unsafe_werkzeug=True)

    # Optional: Add cleanup on shutdown if you need to gracefully stop the MQTT client
    # mqtt_client.loop_stop()
    # mqtt_client.disconnect()