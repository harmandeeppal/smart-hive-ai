# Master Project Plan: Smart Hive AI

---

## 1. Executive Summary & Project Abstract

The Smart Hive AI project is an initiative to engineer a portable, non-invasive, and intelligent beehive monitoring system. This system leverages the confluence of Internet of Things (IoT) sensors and Edge AI to provide real-time insights into the health and status of a honeybee colony.

The core of the system is a Raspberry Pi 4, housed within a model beehive, which serves as the edge computing device. It interfaces with a suite of environmental and activity sensors—monitoring temperature, humidity, acoustics, and vibration—while simultaneously processing a live video feed via an onboard camera. A highly optimized, quantized TensorFlow Lite (TFLite) version of the YOLOv5s object detection model is deployed directly on the device. This enables real-time, low-latency detection of the queen bee, a key indicator of colony vitality.

All collected telemetry and vision metadata are securely transmitted to the AWS cloud infrastructure via the MQTT protocol, utilizing AWS IoT Core as the central message broker. For data persistence, camera snapshots are archived periodically in an AWS S3 bucket. A responsive, Flask-based web dashboard serves as the presentation layer, offering live data visualization, video streaming with AI overlays, and remote device control.

Crucially, the entire software stack—for both the edge device and the web dashboard—is fully containerized using Docker. This strategy guarantees maximum portability, enabling seamless development, testing, and deployment across different architectures (x86 for development, ARM64 for deployment) and ensuring consistent, reproducible behavior.

---

## 2. Core Objectives & Measurable Success Criteria

The project is structured around a set of primary objectives that define the Minimum Viable Product (MVP). Each objective is paired with a quantifiable success metric to ensure an objective evaluation of the project's completion.

### Core Objectives

- **Live Vision AI:** Implement real-time, on-device detection of the queen bee from a live video stream, overlaying bounding boxes and confidence scores.  
- **IoT Data Flow:** Reliably collect data from all four environmental and activity sensors and transmit it to the AWS cloud in a structured format.  
- **Interactive Dashboard:** Provide a simple, browser-based interface for live data monitoring and remote control of the edge device's sensors.  
- **Automated Cloud Storage:** Implement a mechanism for the automated, periodic upload of camera image snapshots to a designated AWS S3 bucket.  
- **Complete Portability:** Ensure the entire application stack can be deployed and run with minimal configuration changes on both a development laptop (x86) and the target Raspberry Pi (ARM64) using Docker and Docker Compose.  

### Success Metrics and Evaluation

| Metric | Target | Priority | Measurement Method |
|--------|---------|-----------|--------------------|
| AI Inference Latency | ≤ 1000 ms per frame | High | Time the inference execution block in the Python code on the Raspberry Pi over 100 consecutive frames and calculate the average. |
| Sensor Data Refresh Rate | ≤ 5 seconds on dashboard | High | Measure the time delta between the timestamp of data generation on the Pi and its visual update on the web dashboard. |
| S3 Upload Reliability | ≥ 95% success rate | High | Over a continuous 1-hour test, log each attempt to upload an image to S3 and verify its successful arrival in the bucket. |
| Sensor Toggle Response | < 2-second round-trip | Medium | Measure the time from clicking a toggle button on the dashboard to receiving confirmation of the state change back from the Pi. |
| Deployment Portability | Fully functional on both platforms | High | Execute `docker-compose up` on both an x86 laptop (with local Mosquitto) and the ARM64 Pi (connected to AWS) and verify full system functionality. |

---

## 3. System Architecture & Data Flow

The system is designed with a layered architecture to separate concerns and enhance modularity. The MQTT protocol serves as the lightweight communication backbone connecting the edge to the cloud and the cloud to the dashboard.

### Hardware Layer (Edge Device)
This physical layer consists of the Raspberry Pi 4 (Model B, 4GB+) and all directly connected peripherals:  
- SHT31 (Temperature/Humidity)  
- MPU-6050 (Vibration/Accelerometer)  
- INMP441 (I2S Microphone)  
- Raspberry Pi Camera Module v2  

### Edge Software Layer (Docker on Pi)
A containerized Python application orchestrates all on-device tasks. It uses multi-threading to concurrently read sensor data, process the camera feed, run the TFLite model for inference, and communicate with the cloud.

### Communication Layer (MQTT)
The MQTT protocol is used for all real-time messaging. This choice minimizes network bandwidth, latency, and device power consumption. Standardized topics (`hive/telemetry`, `hive/vision`, `hive/control`) ensure organized communication.

### Cloud Layer (AWS)
For this sprint, the cloud layer is streamlined for speed.

- **AWS IoT Core:** Acts as the central, secure, and scalable MQTT broker.  
- **AWS S3:** Provides durable, cost-effective object storage for the image snapshots, accessed via boto3.  

**(Post-Sprint Evolution):** For a production system, this layer would expand to include AWS Lambda, DynamoDB, and Kinesis for large-scale analysis.

### Presentation Layer (Dashboard)
A containerized Flask web application provides the user interface. It subscribes to MQTT topics via a backend process and uses Flask-SocketIO to push live data to the frontend, creating a real-time experience without requiring browser refreshes.

### Data Flow Diagram

**Telemetry Data:**  
`Pi Sensors → Python App → MQTT publish → AWS IoT Core → Dashboard`

**Vision Data:**  
`Pi Camera → Python App (OpenCV + TFLite) → MJPEG Stream + Bounding Boxes → MQTT publish → AWS IoT Core → Dashboard`

**Snapshot Storage:**  
`Pi Camera → Python App (every 60s) → boto3 upload → AWS S3`

**Remote Control:**  
`Dashboard → Flask Backend (Socket.IO) → MQTT publish → AWS IoT Core → Pi (subscribes and executes command)`

---

## 4. Technology Stack & Portability Strategy

The technology stack is carefully selected for rapid development, robustness, excellent documentation, and cross-platform compatibility.

### 🍓 Edge Hardware & Sensor Functions

| Sensor | Function & Rationale | Dashboard Display | Optimal Range for Health Indicator |
|--------|----------------------|-------------------|------------------------------------|
| SHT31 (I2C) | Monitors internal hive temperature and humidity, crucial for brood health. | 34.5 °C / 58% + Color-coded Bar | Temp: 32–36 °C (Green); Humidity: 50–70% (Green) |
| MPU-6050 (I2C) | Measures hive activity and external disturbances (RMS accelerometer). | Numeric RMS Value + Bar | Deviation indicates swarming or disturbance. |
| INMP441 (I2S) | Captures the colony's acoustic signature ("hum"). | 52 dB + Bar | Baseline “healthy hum”; deviations indicate stress or queen loss. |
| Camera Module v2 | Provides visual feed for AI detection. | Live Video Stream | N/A |

---

### 🐍 Edge Software (in Docker Container)

- **Language:** Python 3.9+  
- **AI Model:** YOLOv5s → TensorFlow Lite (TFLite) INT8 Quantization  
- **Core Libraries:**  
  - `tflite-runtime`  
  - `opencv-python-headless`  
  - `paho-mqtt`  
  - `boto3`  
  - `adafruit-circuitpython-sht31d`  
  - `adafruit-circuitpython-mpu6050`

---

### ☁️ Cloud & 🖥️ Web Dashboard (in Docker Containers)

- **Cloud Services:** AWS IoT Core, AWS S3  
- **Backend Framework:** Flask + Flask-SocketIO  
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Chart.js  
- **Portability:** Docker-based setup for full simulation locally and deployment to Pi.

---

### The Docker-Centric Strategy

- **Dockerfile.rpi:** ARM64 image for Raspberry Pi edge app.  
- **Dockerfile.dashboard:** x86 image for Flask web dashboard.  
- **docker-compose.yml:** Orchestrates containers, simulates cloud environment with local Mosquitto broker for offline testing.

---

## 5. Strategy for AI Agent Collaboration

To maximize productivity when working with an AI coding assistant, tasks are modularized for prompt precision.

### Example Prompt Structure

> **You are:** A senior Python IoT developer specializing in Raspberry Pi projects.  
> **Context:** We are building a beehive monitoring system in `app.py` using `adafruit-circuitpython-mpu6050`.  
> **Task:** Write a `VibrationSensor` class with initialization, RMS calculation, and robust error handling. Include docstrings.  

**Expected Output:**  
A clean Python class `VibrationSensor` with all imports and docstrings.

---

## 6. The 3-Day Hyper-Sprint Execution Plan

An aggressive 3-day plan to achieve a functional prototype.

### **Day 1: Foundation – Hardware & Cloud Handshake**

**Primary Goal:** Verify hardware and AWS connectivity.

**Key Deliverables:**
- Wired and tested sensors  
- Sensor read validation script  
- Successful MQTT message from Pi to AWS IoT Core  

**Sub-Tasks:**
1. Hardware assembly and pin documentation.  
2. Install Raspberry Pi OS Lite, Docker, and Docker Compose.  
3. Create and test `test_sensors.py`.  
4. Set up AWS IoT Core & S3.  
5. Publish test MQTT message using certificates.

---

### **Day 2: Edge Intelligence – AI & Full Integration**

**Primary Goal:** Develop and containerize the unified edge application.

**Key Deliverables:**
- Quantized `queen_bee.tflite` model  
- `app.py` with modular classes (SensorManager, VisionProcessor, MqttClient)  
- Working Docker container on Pi  

**Sub-Tasks:**
1. Convert YOLOv5 → TFLite INT8 model.  
2. Build modular `app.py`.  
3. Implement S3 snapshot logic with threading.  
4. Create Dockerfile and requirements.txt.  
5. Build and run container; verify AWS data flow.

---

### **Day 3: Interface & Control – The Dashboard**

**Primary Goal:** Build and connect the web interface.

**Key Deliverables:**
- Flask dashboard showing real-time sensor data and AI video  
- Working sensor toggle controls  

**Sub-Tasks:**
1. Build Flask backend (`dashboard.py`).  
2. Implement `/video_feed` endpoint.  
3. Design `index.html` for UI.  
4. Write JavaScript for real-time updates and toggles.  
5. Conduct end-to-end integration test.

---

## 7. Risk Management & Mitigation

| Risk | Impact | Likelihood | Mitigation Plan |
|------|---------|-------------|----------------|
| **AI Model Too Slow on Pi** | Medium | High | Reduce resolution, skip frames, ensure INT8 quantization, consider Coral Accelerator. |
| **AWS IAM/Connectivity Issues** | High | Medium | Use temporary root credentials for sprint; fallback to local Mosquitto. |
| **Docker Build Fails on Pi** | Medium | Medium | Use `docker buildx` for cross-compilation; push to Docker Hub. |
| **Unstable Wi-Fi Connectivity** | High | Medium | Implement reconnection and buffering logic. |
| **Inaccurate Sensor Readings** | Low | High | Use averaging/median filters and calibration. |
| **Power Supply Issues on Pi** | High | Low | Use official 5V 3A PSU. |

---

### **Note**

There was a little change in the original project plan:  
Everything will be portable and tested on the laptop, and only needs to be moved to the Raspberry Pi in a workable condition a day before the project demo.
