<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# You are an IoT, AI/ML, and Computer Engineering expert and will advise and help me implement this IoT Project. At the same time, you are my assistant. Let's first start with structuring the plan below without leaving out any details already there. In fact, you need to enhance the already existing information (no omissions allowed). Take your time and build a comprehensive, detailed information plan. There is NO limit to words so take your time.

Comprehensive Project Plan: Smart Hive AI

1. Project Abstract
To develop a portable, containerized IoT system for real-time honeybee colony monitoring. Housed in a model beehive, a Raspberry Pi 4 will use a suite of sensors (temperature, humidity, vibration, sound) and a camera to stream health data to AWS. An on-device AI model (YOLOv5s-TFLite) will perform real-time queen bee detection. All data and video will be visualized on a simple, responsive web dashboard, which also allows for remote sensor control. The entire system is designed with Docker for maximum portability between development (laptop) and deployment (Raspberry Pi).
2. Core Objectives \& Success Criteria
Must-Haves (The MVP for your 3-Day Sprint)
Live Video Feed: A web dashboard displaying the camera stream with a bounding box and confidence score overlaid when a queen is detected.

Sensor Telemetry: Temperature, humidity, vibration, and sound data are successfully published to AWS IoT Core and displayed numerically on the dashboard.

Visual Health Indicators: The dashboard must show simple bar gauges that visualize whether sensor readings are in their optimal range.

Cloud Storage: A snapshot from the camera is successfully saved to an AWS S3 bucket once every minute.

Remote Control: Each of the 4 sensors can be toggled on/off from the dashboard, with the command being successfully sent to and executed by the Raspberry Pi.

Portability: The entire application stack (edge and dashboard) is containerized with Docker, allowing it to run on a laptop for development and on the Pi for deployment.

Success Criteria (How to measure success)
AI Vision Latency: Queen detection inference time on the Raspberry Pi is under 1000ms per frame.

Dashboard Latency: Sensor data updates on the dashboard within 5 seconds of being measured.

Reliability: Snapshot-to-S3 upload success rate is >95% over a 1-hour test period.

Functionality: All sensor toggles are functional and responsive.

3. System Architecture
Hardware Layer (Edge Device): Raspberry Pi 4 and all connected sensors.

Edge Software Layer (Docker on Pi): A Python application reads sensors, runs the TFLite model, and publishes data.

Communication Layer (MQTT): All data and control messages are sent over MQTT topics to AWS IoT Core.

Cloud Layer (AWS):

AWS IoT Core: Acts as the central MQTT broker.

AWS S3: Stores image snapshots.

(For this sprint, we will skip Lambda, DynamoDB, and Kinesis to save time. The dashboard will get data directly from IoT Core.)

Presentation Layer (Docker on Laptop/Cloud): A Flask-based web dashboard that subscribes to MQTT topics for live data and displays the video stream.

Data Flow
Telemetry: Pi Sensors → Python App → paho-mqtt publish → AWS IoT Core Topic (hive/telemetry) → Dashboard subscribes and displays.

Vision: Pi Camera → Python App (OpenCV + TFLite) → Live Stream to Dashboard | Bounding Box Data → AWS IoT Core Topic (hive/vision) → Dashboard displays.

Snapshots: Pi Camera → Python App → boto3 upload → AWS S3 Bucket.

Control: Dashboard Toggle Click → Flask Backend publish → AWS IoT Core Topic (hive/control) → Pi subscribes and toggles sensor.

4. Technology Stack (Optimized for Speed)
This stack is chosen specifically for its simplicity, excellent documentation, and rapid implementation.

🍓 Edge Hardware:

Compute: Raspberry Pi 4 (Model B, 4GB+).

Temp/Humidity: SHT31. More accurate than the DHT series and has great library support.

Vibration: MPU-6050. The standard for hobbyist projects, very easy to work with.

Sound: INMP441 (I2S Microphone). Superior quality and direct GPIO connection compared to a USB mic.

Camera: Raspberry Pi Camera Module v2.

🐍 Edge Software (in Docker Container):

Language: Python 3.9+.

AI Model: YOLOv5s converted to TensorFlow Lite (TFLite) with INT8 quantization. We will use a pre-trained model; no training will be done in this sprint.

Libraries:

tflite-runtime: For running the model without installing the full TensorFlow.

opencv-python-headless: For image processing.

paho-mqtt: The de-facto standard for MQTT in Python.

boto3: The official AWS SDK for Python (for S3 uploads).

Sensor-specific libraries (e.g., adafruit-circuitpython-sht31d, adafruit-circuitpython-mpu6050).

☁️ Cloud Services:

AWS IoT Core: For MQTT brokering.

AWS S3: For image storage.

🖥️ Web Dashboard (in Docker Container):

Backend Framework: Flask. Simple, Python-based, and perfect for this scale.

Real-time Communication: Flask-SocketIO. The easiest way to push live sensor data to the web interface.

Frontend: Vanilla JavaScript, HTML, CSS. No complex frameworks like React to speed up development. We will use a simple library like Chart.js for the bars if needed.

5. Portability Strategy: Docker is Everything
This is non-negotiable for meeting your portability requirement.

Dockerfile.rpi: An ARM64-based Dockerfile to build the container for the Raspberry Pi. It will install Python and all the edge libraries.

Dockerfile.dashboard: An x86-based Dockerfile for the Flask web dashboard.

docker-compose.yml: A single file to run the entire system on your laptop for development. It will launch the dashboard container and a local Mosquitto MQTT broker container to simulate AWS IoT Core, allowing you to develop and test without constant cloud deployment.

6. 🚀 The 3-Day Sprint Plan: An Actionable Guide
Day 1: Foundation - Hardware \& Connectivity (Goal: See data in the AWS console)
Hardware Assembly: Wire all 4 sensors and the camera to the Raspberry Pi GPIO pins. Use a breadboard.

Pi Setup: Flash Raspberry Pi OS Lite (64-bit). Configure Wi-Fi. Install Docker and Docker Compose.

Sensor Validation: Do not containerize yet. Write a simple Python script (test_sensors.py) on the Pi to read a value from each sensor and print it to the console. This verifies your wiring is correct.

AWS Setup:

Create an AWS account.

Go to AWS IoT Core, create a "Thing" for your hive.

Download the security certificates.

Go to AWS S3 and create a bucket for your snapshots.

First Cloud Message: Write a new Python script (send_mqtt.py) that connects to AWS IoT Core using the certificates and sends a test JSON message (e.g., {"message": "hello world"}). Use the AWS IoT Core "Test client" to subscribe to the topic and see your message arrive.

Deliverable for Day 1: A Raspberry Pi successfully publishing a "hello world" message to your AWS IoT Core account.

Day 2: Edge Intelligence - AI \& Integration (Goal: A master script that does everything)
Get the AI Model: Download a pre-trained YOLOv5s model and use the official export script to convert it to a .tflite file.

Create the Master App: Create a single Python application (app.py). This script will:

Initialize all sensors and the camera.

Load the queen_detector.tflite model using tflite-runtime.

Start the MQTT client.

Run a main loop that:

Reads temperature, humidity, vibration (as RMS), and sound (as dB).

Captures a frame from the camera.

Runs inference on the frame to get bounding boxes.

Publishes a JSON payload with all sensor data to hive/telemetry.

(Optional) Publishes bounding box data to hive/vision.

Implement Snapshotting: Add a timer to your main loop. Every 60 seconds, it should encode the current frame as a JPEG and upload it to your S3 bucket using boto3.

Containerize It: Write the Dockerfile.rpi and build the container on the Pi. Run it and verify that data is still flowing to AWS IoT Core and images are appearing in S3.

Deliverable for Day 2: A Docker container running on the Pi that successfully performs detection, sends telemetry to AWS, and saves snapshots to S3.

Day 3: Interface \& Control - The Dashboard (Goal: A working demo)
Dashboard Backend: On your laptop, create a Flask application.

Use paho-mqtt within the Flask app to subscribe to the hive/telemetry topic from AWS IoT Core.

Use Flask-SocketIO to push any data received from MQTT immediately to connected web browsers.

Create an HTTP endpoint for the video stream (/video_feed).

Create a Socket.IO event handler that receives commands (e.g., toggle_sensor) from the browser and publishes them to the hive/control MQTT topic.

Dashboard Frontend: Create a single index.html file.

Lay out the page with a section for the video (<img> tag pointing to /video_feed) and sections for each sensor.

Use JavaScript's Socket.IO client to connect to the backend.

Write JS functions to update the temperature/humidity numbers and bar gauges when a new message arrives.

Add toggle buttons. When a button is clicked, use Socket.IO to emit a toggle_sensor event to the backend.

Final Integration:

Modify your Raspberry Pi app.py to also subscribe to the hive/control topic. When it receives a message (e.g., {"sensor": "temp", "state": "off"}), it should disable reading from that sensor.

Containerize the dashboard using Dockerfile.dashboard.

Run everything and test the full end-to-end flow.

Deliverable for Day 3: A fully functional system where you can view live data and toggle sensors from a web browser.

7. Risk Management \& Mitigation
Risk: AI model is too slow on the Pi.

Mitigation: 1) Reduce camera resolution to 640x480. 2) Process every 3rd or 5th frame instead of every frame. 3) Ensure you are using the quantized INT8 TFLite model.

Risk: AWS setup takes too long (IAM policies, etc.).

Mitigation: For this 3-day sprint, use your root AWS account credentials directly. This is bad practice for production, but acceptable for a short-term academic project to avoid getting stuck on permissions. Delete the credentials after the project.

Risk: Frontend development is time-consuming.

Mitigation: Stick to plain HTML and JavaScript. Do not use React, Vue, or Angular. Use a simple CSS framework like Bootstrap for layout if you must, but otherwise, keep it simple. The goal is functionality, not beauty.
Master Project Plan: Smart Hive AI

1. Project Abstract
The Smart Hive AI project will develop a portable, cloud-connected beehive monitoring system integrating IoT sensing and AI-based visual recognition. Using a Raspberry Pi 4, the system continuously monitors temperature, humidity, vibration, and hive acoustics. An on-device, optimized AI model (YOLOv5s-TFLite) performs real-time queen bee detection from a live camera feed.

All data streams are relayed via AWS IoT Core, with image snapshots stored in AWS S3. A Flask-based web dashboard provides a user interface for live data visualization, video streaming, and remote sensor control. The entire solution is fully containerized using Docker, ensuring seamless portability and reproducibility between a development laptop and the target Raspberry Pi.

2. Objectives \& Measurable Success Criteria
This project is defined by a set of core objectives, each with a clear, measurable metric for success.

Core Objectives
Live Vision AI: Implement real-time, on-device detection of the queen bee.

IoT Data Flow: Reliably collect and transmit data from all four sensors to the AWS cloud.

Interactive Dashboard: Provide a browser-based interface for live monitoring and control.

Cloud Storage: Automate the periodic upload of camera snapshots to AWS S3.

Full Portability: Ensure the entire application can be moved between a development laptop and the Raspberry Pi with minimal friction using Docker.

Success Metrics
Metric	Target	Priority
Inference Latency	≤ 1000 ms per frame	High
Sensor Data Refresh	≤ 5 seconds on dashboard	High
S3 Upload Reliability	≥ 95% success rate over 1 hour	High
Sensor Toggle Response	< 2 second round-trip delay	Medium
Portability	Fully functional via docker-compose on both laptop (x86) and Pi (ARM64)	High

Export to Sheets
3. System Architecture \& Data Flow
The architecture is composed of four distinct layers connected by the MQTT protocol.

Hardware (Edge): Raspberry Pi 4, SHT31, MPU-6050, INMP441 Mic, Camera Module v2.

Edge Software (Docker on Pi): A containerized Python application responsible for sensor reading, AI inference, and cloud communication (paho-mqtt, boto3).

Cloud Layer (AWS):

AWS IoT Core: The central MQTT broker for all telemetry (hive/telemetry) and control (hive/control) messages.

AWS S3: The destination for all minute-by-minute image snapshots.

Dashboard Layer (Docker on Laptop/Cloud): A containerized Flask application that subscribes to AWS IoT Core for live data and serves the web UI.

Data Flow Summary
Sensors → Python App → MQTT Publish → AWS IoT Core → Dashboard (Live Telemetry)

Camera → AI Detection → Frame with Bounding Box → Dashboard (Live Video)

Dashboard Toggle → MQTT Publish → AWS IoT Core → Pi Executes Command (Remote Control)

Every 60s → Camera Snapshot → S3 Upload (Cloud Storage)

4. Hardware \& Sensor Functions
Each sensor has a specific purpose and a clear representation on the dashboard.

Sensor	Function	Dashboard Display	Optimal Range for Indicator Bar
Temperature	Monitors internal hive temperature for brood health.	34.5 °C + Color-coded Bar	32–36 °C (Green)
Humidity	Monitors hive humidity to prevent egg desiccation.	58 % + Color-coded Bar	50–70 % (Green)
Vibration	Measures hive activity/disturbance via RMS acceleration.	Numeric RMS + Bar	Baseline set on a "calm" hive.
Sound	Captures colony acoustic signature.	52 dB + Bar	Baseline set on a "healthy hum."

Export to Sheets
5. Technology Stack \& Portability Strategy
The tech stack is optimized for speed of implementation and portability.

Layer	Technology	Purpose
Edge Compute	Raspberry Pi 4 (64-bit OS)	Host sensors and run edge container.
Edge Software	Python, OpenCV, tflite-runtime	Sensor reading, AI inference.
Communication	MQTT via paho-mqtt	Lightweight data and control messaging.
Cloud	AWS IoT Core, AWS S3	Data relay and image storage.
Web Dashboard	Flask, Flask-SocketIO, Chart.js	Real-time visualization and control.
Containerization	Docker, docker-compose	CRITICAL: For portability and reproducibility.

Export to Sheets
Portability: The Docker Strategy
Dockerfile.rpi: Builds a Python container with all necessary libraries for the ARM64 architecture of the Raspberry Pi.

Dockerfile.dashboard: Builds the Flask container for the x86 architecture of your development laptop.

docker-compose.yml: Orchestrates the entire system locally for testing. It will spin up the dashboard and a local Mosquitto MQTT broker to simulate AWS, allowing for rapid, offline development.

6. 🧠 Strategy for AI Agent Collaboration
To maximize the efficiency of your AI coding agent, provide it with modular, structured prompts. Do not ask it to "build the project." Instead, give it specific, self-contained tasks.

Example Prompt Structure:

You are: A senior Python IoT developer.
Context: We are building a beehive monitoring system on a Raspberry Pi 4. The main application is in a file named app.py.
Task: Write a Python class named VibrationSensor that reads data from an MPU-6050 sensor connected via I2C.
Requirements:

The class should have an __init__ method to set up the sensor.

It must have a read() method that returns the Root Mean Square (RMS) of the accelerometer's X, Y, and Z axes as a single float value.

Include error handling for I2C communication failures.

Add comprehensive comments explaining the code.
Expected Output: A single Python code block containing the complete VibrationSensor class.

7. 🚀 The 3-Day Hyper-Sprint Execution Plan
Day 1: Foundation – Hardware \& Cloud Handshake
Primary Goal: Prove that the hardware works and can communicate with the cloud.

Key Deliverables:

All sensors physically wired to the Raspberry Pi.

A test script that successfully reads data from every sensor.

A test message successfully published from the Pi and visible in the AWS IoT Core console.

Actionable Sub-Tasks

1. Hardware Assembly: Wire the SHT31, MPU-6050, INMP441, and Camera to the Pi's GPIO pins.
2. Sensor Validation Script: Give your agent a prompt to write a test_sensors.py script that initializes each sensor and prints a reading to the console. Run this on the Pi to verify wiring.
3. AWS Setup: Configure AWS IoT Core (create a "Thing," download certificates) and create your S3 bucket.
4. Cloud Connectivity Test: Prompt your agent to write a simple script (test_aws.py) using paho-mqtt to publish a JSON message ({"status": "online"}) to your AWS IoT Core endpoint. Confirm its arrival in the AWS console.

Export to Sheets
Day 2: Edge Intelligence – AI \& Full Integration
Primary Goal: Create a single, containerized application on the Pi that performs all edge tasks.

Key Deliverables:

A working TFLite model for queen detection.

A unified Python application (app.py) that reads all sensors, runs inference, and publishes to AWS.

A Docker container running this application on the Pi.

Actionable Sub-Tasks

1. AI Model Prep: Download a YOLOv5s model. Prompt your agent for the command to convert it to a quantized queen_bee.tflite file.
2. Build Master Script: Prompt your agent to build the main app.py. Break it down: "Add the TemperatureSensor class," "Integrate the TFLite model inference loop," "Add the MQTT publishing logic."
3. S3 Snapshot Logic: Instruct the agent to add a function to app.py that, on a 60-second timer, captures a camera frame and uploads it to S3 using boto3.
4. Containerize the Edge App: Prompt your agent to write the Dockerfile.rpi and a simple requirements.txt. Build and run the container on the Pi, verifying that data still flows to AWS and images appear in S3.

Export to Sheets
Day 3: Interface \& Control – The Dashboard
Primary Goal: Create a working user interface to visualize data and control the hive.

Key Deliverables:

A Flask web server that displays live data.

A functional video stream with AI overlays.

Working toggle switches for all four sensors.

Actionable Sub-Tasks

1. Build Flask Backend: Prompt your agent to create a dashboard.py file. "Set up a basic Flask app." "Add a paho-mqtt client that subscribes to hive/telemetry." "Use Flask-SocketIO to push received MQTT data to the browser."
2. Design Frontend UI: Prompt for an index.html file with placeholders for the video stream and four sensor panels (each with a spot for a number, a bar, and a toggle switch).
3. Implement Real-Time Updates: Ask for the JavaScript code that connects to Socket.IO and updates the sensor values and bars in the HTML when new data arrives.
4. Implement Control Logic: Ask for the JavaScript for the toggle switches. When clicked, they should emit a Socket.IO event. In your Flask backend, handle this event by publishing a control message (e.g., {"sensor": "temp", "state": "off"}) to the hive/control MQTT topic.
5. Final Integration: Instruct the agent to modify the Pi's app.py to subscribe to hive/control and act on the incoming messages. Test the full round trip.

Export to Sheets
8. Risk Management
Risk	Impact	Mitigation Plan
AI Model Too Slow on Pi	Medium	1. Reduce Resolution: Process frames at 640x480. 2. Skip Frames: Run inference on every 3rd frame. 3. Quantize: Ensure the TFLite model is INT8 quantized.
AWS Connectivity Issues	High	Fallback to Local: Use the docker-compose.yml with a local Mosquitto MQTT broker for development and demonstration if AWS proves too time-consuming to configure.
Docker Build Fails on Pi	Medium	Cross-Compile: Build the ARM64 image on your more powerful laptop using docker buildx and push it to Docker Hub, then pull it on the Pi.
Sensor Reading Inaccurate	Low	Averaging: Take 5 readings in quick succession and use the average to smooth out noise.

Of course. As an expert in IoT, AI/ML, and Computer Engineering, I will enhance and structure your project plan for the Smart Hive AI system. My goal is to add detail, provide professional context, and offer actionable insights while ensuring all of your original requirements are retained and expanded upon.

Here is the comprehensive and enhanced project plan.

### **Master Project Plan: Smart Hive AI**

#### **1. Executive Summary \& Project Abstract**

The Smart Hive AI project is an initiative to engineer a portable, non-invasive, and intelligent beehive monitoring system. This system leverages the confluence of Internet of Things (IoT) sensors and Edge AI to provide real-time insights into the health and status of a honeybee colony.

The core of the system is a Raspberry Pi 4, housed within a model beehive, which serves as the edge computing device. It interfaces with a suite of environmental and activity sensors—monitoring temperature, humidity, acoustics, and vibration—while simultaneously processing a live video feed via an onboard camera. A highly optimized, quantized TensorFlow Lite (TFLite) version of the YOLOv5s object detection model is deployed directly on the device. This enables real-time, low-latency detection of the queen bee, a key indicator of colony vitality.

All collected telemetry and vision metadata are securely transmitted to the AWS cloud infrastructure via the MQTT protocol, utilizing AWS IoT Core as the central message broker. For data persistence, camera snapshots are archived periodically in an AWS S3 bucket. A responsive, Flask-based web dashboard serves as the presentation layer, offering live data visualization, video streaming with AI overlays, and remote device control.

Crucially, the entire software stack—for both the edge device and the web dashboard—is fully containerized using Docker. This strategy guarantees maximum portability, enabling seamless development, testing, and deployment across different architectures (x86 for development, ARM64 for deployment) and ensuring consistent, reproducible behavior.

***

#### **2. Core Objectives \& Measurable Success Criteria**

The project is structured around a set of primary objectives that define the Minimum Viable Product (MVP). Each objective is paired with a quantifiable success metric to ensure an objective evaluation of the project's completion.

**Core Objectives**

* **Live Vision AI:** Implement real-time, on-device detection of the queen bee from a live video stream, overlaying bounding boxes and confidence scores.
* **IoT Data Flow:** Reliably collect data from all four environmental and activity sensors and transmit it to the AWS cloud in a structured format.
* **Interactive Dashboard:** Provide a simple, browser-based interface for live data monitoring and remote control of the edge device's sensors.
* **Automated Cloud Storage:** Implement a mechanism for the automated, periodic upload of camera image snapshots to a designated AWS S3 bucket.
* **Complete Portability:** Ensure the entire application stack can be deployed and run with minimal configuration changes on both a development laptop (x86) and the target Raspberry Pi (ARM64) using Docker and Docker Compose.

**Success Metrics and Evaluation**
This table details the specific metrics that will be used to validate the successful completion of the 3-day sprint.


| Metric | Target | Priority | Measurement Method |
| :-- | :-- | :-- | :-- |
| **AI Inference Latency** | ≤ 1000 ms per frame | **High** | Time the inference execution block in the Python code on the Raspberry Pi over 100 consecutive frames and calculate the average. |
| **Sensor Data Refresh Rate** | ≤ 5 seconds on dashboard | **High** | Measure the time delta between the timestamp of data generation on the Pi and its visual update on the web dashboard. |
| **S3 Upload Reliability** | ≥ 95% success rate | **High** | Over a continuous 1-hour test, log each attempt to upload an image to S3 and verify its successful arrival in the bucket. |
| **Sensor Toggle Response** | < 2-second round-trip | **Medium** | Measure the time from clicking a toggle button on the dashboard to receiving confirmation of the state change back from the Pi. |
| **Deployment Portability** | Fully functional on both platforms | **High** | Execute `docker-compose up` on both an x86 laptop (with local Mosquitto) and the ARM64 Pi (connected to AWS) and verify full system functionality. |


***

#### **3. System Architecture \& Data Flow**

The system is designed with a layered architecture to separate concerns and enhance modularity. The MQTT protocol serves as the lightweight communication backbone connecting the edge to the cloud and the cloud to the dashboard.

* **Hardware Layer (Edge Device):** This physical layer consists of the **Raspberry Pi 4 (Model B, 4GB+)** and all directly connected peripherals: **SHT31** (Temperature/Humidity), **MPU-6050** (Vibration/Accelerometer), **INMP441** (I2S Microphone), and the **Raspberry Pi Camera Module v2**.
* **Edge Software Layer (Docker on Pi):** A containerized Python application orchestrates all on-device tasks. It uses multi-threading to concurrently read sensor data, process the camera feed, run the TFLite model for inference, and communicate with the cloud.
* **Communication Layer (MQTT):** The MQTT protocol is used for all real-time messaging. This choice minimizes network bandwidth, latency, and device power consumption. Standardized topics (`hive/telemetry`, `hive/vision`, `hive/control`) ensure organized communication.
* **Cloud Layer (AWS):** For this sprint, the cloud layer is streamlined for speed.
    * **AWS IoT Core:** Acts as the central, secure, and scalable MQTT broker. It authenticates the device and routes messages based on topics.
    * **AWS S3:** Provides durable, cost-effective object storage for the image snapshots, accessed via `boto3`.
    * *(Post-Sprint Evolution): For a production system, this layer would expand to include AWS Lambda for serverless data processing, DynamoDB for structured data storage, and potentially Kinesis for large-scale stream analysis.*
* **Presentation Layer (Dashboard):** A containerized Flask web application provides the user interface. It subscribes to MQTT topics via a backend process and uses Flask-SocketIO to push live data to the frontend, creating a real-time experience without requiring browser refreshes.

**Data Flow Diagram**

1. **Telemetry Data:**
    * `Pi Sensors (SHT31, MPU-6050, INMP441)` → `Python App (reads data)` → `paho-mqtt publish` → `AWS IoT Core (topic: hive/telemetry)` → `Dashboard (subscribes and displays)`.
2. **Vision Data:**
    * `Pi Camera` → `Python App (OpenCV + TFLite inference)` → `Live MJPEG Stream to Dashboard` \& `Bounding Box Data` → `paho-mqtt publish` → `AWS IoT Core (topic: hive/vision)` → `Dashboard (overlays boxes)`.
3. **Snapshot Storage:**
    * `Pi Camera (every 60s)` → `Python App (encodes frame)` → `boto3 upload` → `AWS S3 Bucket`.
4. **Remote Control:**
    * `Dashboard Toggle Click` → `Flask Backend (emits Socket.IO event)` → `paho-mqtt publish` → `AWS IoT Core (topic: hive/control)` → `Pi Python App (subscribes and executes command)`.

***

#### **4. Technology Stack \& Portability Strategy**

The technology stack is carefully selected for rapid development, robustness, excellent documentation, and cross-platform compatibility.

**🍓 Edge Hardware \& Sensor Functions**
Each sensor is chosen for its specific capabilities and ease of integration with the Raspberry Pi.


| Sensor | Function \& Rationale | Dashboard Display | Optimal Range for Health Indicator |
| :-- | :-- | :-- | :-- |
| **SHT31 (I2C)** | Monitors internal hive temperature and humidity, crucial for brood (egg and larva) health. Chosen for its accuracy and simple I2C interface. | `34.5 °C` / `58%` + Color-coded Bar | **Temp:** 32–36 °C (Green)<br>**Humidity:** 50–70% (Green) |
| **MPU-6050 (I2C)** | Measures hive activity and external disturbances by calculating the Root Mean Square (RMS) of accelerometer data. Standard and well-supported. | Numeric RMS Value + Bar | A baseline is established on a "calm" hive; significant deviations indicate swarming, attack, or disturbance. |
| **INMP441 (I2S)** | Captures the colony's acoustic signature (the "hum"). The I2S digital interface provides superior audio quality and noise immunity compared to USB or analog mics. | `52 dB` + Bar | A baseline is set on a "healthy hum." Changes can indicate stress, queen loss (queen piping), or preparation for swarming. |
| **Camera Module v2** | Provides the visual feed for AI detection. Chosen for its native integration with the Raspberry Pi, ensuring low-level hardware access for optimal performance. | Live Video Stream | N/A |

**🐍 Edge Software (in Docker Container)**

* **Language:** Python 3.9+
* **AI Model:** **YOLOv5s** converted to **TensorFlow Lite (TFLite)** with **INT8 quantization**. This quantization process significantly reduces the model's size and computational demand, making it ideal for CPU-based inference on the Pi while maintaining acceptable accuracy.
* **Core Libraries:**
    * `tflite-runtime`: For executing the model without the full TensorFlow dependency.
    * `opencv-python-headless`: For all image capture and processing tasks (headless to save space).
    * `paho-mqtt`: The de facto standard library for MQTT communication in Python.
    * `boto3`: The official AWS SDK for Python, used for all interactions with S3.
    * `adafruit-circuitpython-sht31d`, `adafruit-circuitpython-mpu6050`: High-level libraries to simplify sensor interaction.

**☁️ Cloud \& 🖥️ Web Dashboard (in Docker Containers)**

* **Cloud Services:** AWS IoT Core, AWS S3.
* **Backend Framework:** Flask (Python). Simple, lightweight, and perfect for managing the dashboard's logic and data flow.
* **Real-time Communication:** Flask-SocketIO. Abstracting WebSockets to easily push data from the server (which gets it from MQTT) to the client.
* **Frontend:** Vanilla JavaScript, HTML5, CSS3. No complex frameworks like React or Vue are used, drastically simplifying and accelerating frontend development. `Chart.js` will be used for simple, effective bar gauges.

**Portability: The Docker-Centric Strategy**
This is the cornerstone of the project's flexibility.

* **`Dockerfile.rpi`:** An ARM64-based Dockerfile that builds the Python environment for the Raspberry Pi. It will install all edge libraries and copy the application code.
* **`Dockerfile.dashboard`:** An x86-based Dockerfile for the Flask web dashboard, ensuring it runs identically on any developer's machine.
* **`docker-compose.yml`:** A powerful orchestration file. For local development, it will launch the dashboard container and a `mosquitto` MQTT broker container. This simulates the entire cloud environment locally, allowing for rapid, offline development and testing of the full communication flow before deploying to the Pi or AWS.

***

#### **5. Strategy for AI Agent Collaboration**

To maximize productivity when working with an AI coding assistant, it is critical to break down complex requests into modular, well-defined tasks. This approach, known as "Prompt Engineering," yields more accurate and useful code.

**Example Prompt Structure:**

> **You are:** A senior Python IoT developer specializing in Raspberry Pi projects.
> **Context:** We are building a beehive monitoring system in a file named `app.py`. We are using the `adafruit-circuitpython-mpu6050` library to interface with an MPU-6050 accelerometer.
> **Task:** Write a Python class named `VibrationSensor`.
> **Requirements:**
> 1.  The `__init__` method should initialize the sensor on the default I2C bus. It must include robust error handling (e.g., a `try-except` block for `ValueError`) in case the sensor is not found.
> 2.  It must have a `read()` method that returns the Root Mean Square (RMS) of the accelerometer's X, Y, and Z axes as a single float value. RMS is calculated as `sqrt((x^2 + y^2 + z^2) / 3)`.
> 3.  If a reading fails, the `read()` method should return `None` and log an error message.
> 4.  Include comprehensive docstrings for the class and its methods.
> **Expected Output:** A single, clean Python code block containing the complete `VibrationSensor` class with all necessary imports.

***

#### **6. The 3-Day Hyper-Sprint Execution Plan**

This aggressive plan is designed to achieve a fully functional prototype in three days by focusing on core deliverables.

##### **Day 1: Foundation – Hardware \& Cloud Handshake**

* **Primary Goal:** Prove that the physical hardware works and can establish a basic communication link with the AWS cloud.
* **Key Deliverables:**

1. A Raspberry Pi with all sensors and camera physically wired and verified.
2. A standalone Python script that successfully reads a value from every sensor.
3. A test message successfully published from the Pi and confirmed as received in the AWS IoT Core MQTT test client.

| Actionable Sub-Tasks |
| :-- |
| **1. Hardware Assembly:** Wire all components to the Pi's GPIO pins. Use a breadboard for initial setup. Document your pinout (e.g., SHT31/MPU-6050 to I2C pins 3 and 5; INMP441 to I2S pins). |
| **2. Pi OS \& Docker Setup:** Flash Raspberry Pi OS Lite (64-bit) to an SD card. Configure headless Wi-Fi. Install Docker and Docker Compose. |
| **3. Sensor Validation Script:** Prompt your AI agent to write a `test_sensors.py` script that initializes each sensor in sequence and prints a reading to the console. Run this on the Pi to verify wiring and library installation. |
| **4. AWS Primitives Setup:** In the AWS console, navigate to IoT Core. Create a "Thing" representing your hive. Create and download the security certificates (`.pem.key`, `.pem.crt`, `AmazonRootCA1.pem`). Store them securely on the Pi. Then, go to S3 and create a uniquely named bucket. |
| **5. Cloud Connectivity Test:** Prompt your agent to write a simple script (`test_aws.py`) using `paho-mqtt` that connects to your AWS IoT Core endpoint using the downloaded certificates and publishes a JSON message (`{"status": "online", "timestamp": "..."}`) to a test topic. Subscribe to this topic in the AWS IoT Core web console to see your message arrive. |

##### **Day 2: Edge Intelligence – AI \& Full Integration**

* **Primary Goal:** Develop and containerize a single, unified application on the Pi that performs all edge-side tasks.
* **Key Deliverables:**

1. A quantized `queen_bee.tflite` model ready for deployment.
2. A master Python application (`app.py`) that reads all sensors, runs AI inference, and publishes telemetry and vision data to respective MQTT topics.
3. A Docker container running this application successfully on the Raspberry Pi.

| Actionable Sub-Tasks |
| :-- |
| **1. AI Model Preparation:** Download a pre-trained YOLOv5s model. Prompt your AI agent for the exact `export.py` command from the YOLOv5 repository to convert the PyTorch model to a quantized INT8 TensorFlow Lite model. |
| **2. Modular Application Structure:** Instead of one large script, prompt your agent to build `app.py` in a modular fashion. "Write a `SensorManager` class to handle all sensor readings." "Write a `VisionProcessor` class to manage the camera feed and TFLite inference." "Write an `MqttClient` class to handle all MQTT connections and publishing." The main part of the script will then instantiate and coordinate these classes. |
| **3. S3 Snapshot Logic:** Instruct the agent to add a function to `app.py` that is triggered by a `threading.Timer`. This function should capture a high-resolution frame, encode it as a JPEG, and upload it to your S3 bucket using `boto3`. Ensure you configure `boto3` with AWS credentials (for this sprint, using an access key is acceptable; in production, an IAM role is preferred). |
| **4. Containerize the Edge App:** Prompt your agent to write the `Dockerfile.rpi` and a `requirements.txt` file listing all Python dependencies. Build the container on the Pi using `docker build`. Run it and verify that telemetry is flowing to AWS IoT Core and images are appearing in S3. |

##### **Day 3: Interface \& Control – The Dashboard**

* **Primary Goal:** Create a functional web interface to visualize live data and exercise remote control over the edge device.
* **Key Deliverables:**

1. A Flask web server that displays live, updating sensor data.
2. A functional video stream with AI bounding boxes rendered.
3. Working toggle switches for all four sensors that successfully alter the state of the Raspberry Pi application.

| Actionable Sub-Tasks |
| :-- |
| **1. Build Flask Backend (`dashboard.py`):** Prompt your agent to create the Flask application. "Set up a Flask app with Flask-SocketIO." "In a background thread, create a `paho-mqtt` client that subscribes to `hive/telemetry`." "When an MQTT message arrives, use `socketio.emit()` to push the JSON data to all connected web clients." |
| **2. Implement Video Streaming:** Create an HTTP endpoint (e.g., `/video_feed`). This endpoint will return a multipart response (`multipart/x-mixed-replace; boundary=frame`) that continuously streams JPEG-encoded frames captured by the Pi's `VisionProcessor`. |
| **3. Design Frontend UI (`index.html`):** Prompt for an HTML file with placeholders for the video stream (`<img src="/video_feed">`) and four sensor "cards." Each card should contain elements with unique IDs for the numeric value, the `Chart.js` bar gauge canvas, and a toggle switch. |
| **4. Implement Real-Time Updates \& Control (JavaScript):** Ask for the client-side JavaScript. It should connect to the server using the Socket.IO client library. Write JS functions that listen for the data event and update the appropriate HTML elements' content and `Chart.js` gauge values. Add event listeners to the toggle buttons that, when clicked, emit a `toggle_sensor` event back to the Flask server with the sensor name and desired state. |
| **5. Final Integration (End-to-End Test):** In the Flask backend, create a Socket.IO event handler for `toggle_sensor` that publishes a control message to the `hive/control` MQTT topic. Finally, instruct your agent to modify the Pi's `app.py` to subscribe to `hive/control` and update its internal state (e.g., stop reading from a sensor) when a message arrives. Run the entire system and test the full round-trip functionality. |


***

#### **7. Risk Management \& Mitigation**

Proactive risk management is essential for a fast-paced project.


| Risk | Impact | Likelihood | Mitigation Plan |
| :-- | :-- | :-- | :-- |
| **AI Model Too Slow on Pi** | **Medium** | **High** | 1.  **Reduce Resolution:** Process frames at 640x480 or 320x320. 2.  **Skip Frames:** Run inference on every 3rd or 5th frame instead of every frame. 3.  **Verify Quantization:** Ensure the `.tflite` model is indeed an INT8 quantized model, not FP32. 4.  **Use Coral Accelerator:** For future work, adding a Google Coral USB Accelerator would offload inference and guarantee high frame rates. |
| **AWS IAM/Connectivity Issues** | **High** | **Medium** | 1.  **Sprint-Only Credentials:** For the 3-day sprint, use root AWS account credentials directly to bypass complex IAM policy creation. **This is a critical security risk in production but acceptable for a short-term, firewalled academic project.** Delete the credentials immediately after the sprint. 2.  **Local Fallback:** Have the `docker-compose.yml` with the local Mosquitto broker ready as a complete fallback for demonstration if AWS connectivity becomes an insurmountable blocker. |
| **Docker Build Fails on Pi** | **Medium** | **Medium** | 1.  **Cross-Compilation:** Use `docker buildx` on a more powerful x86 laptop to build the ARM64 image (`docker buildx build --platform linux/arm64 ...`). Push the image to Docker Hub and then simply pull it on the Pi. This is much faster and more reliable than building on the Pi itself. |
| **Unstable Wi-Fi Connectivity** | **High** | **Medium** | 1.  **Resilient Code:** Implement automatic reconnection logic in both the `paho-mqtt` client and the `boto3` uploader. 2.  **Data Buffering:** In case of connection loss, temporarily buffer a small number of sensor readings in memory and publish them once the connection is restored. |
| **Inaccurate Sensor Readings** | **Low** | **High** | 1.  **Averaging/Filtering:** For noisy sensors like the MPU-6050, take 5-10 readings in a quick burst and use the average or a median filter to smooth out the data. 2.  **Calibration:** Run the sensors in a known, stable environment to establish a baseline reading. |
| **Power Supply Issues on Pi** | **High** | **Low** | Use an official Raspberry Pi power supply (5V, 3A minimum). Under-voltage can cause silent data corruption, Wi-Fi drops, and unpredictable crashes. |

