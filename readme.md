# Smart Hive AI

A portable, containerized IoT system for real-time honeybee colony monitoring using a Raspberry Pi, a suite of sensors, and on-device AI for queen bee detection. All data is streamed to a live web dashboard via AWS IoT Core.

![Dashboard Mockup](https://your-image-url-here.com/dashboard.png) <!-- It's great to add a screenshot here -->

---

## Features

-   **Live Telemetry:** Real-time data from Temperature, Humidity, Vibration, and Sound sensors.
-   **AI-Powered Video:** Live MJPEG video stream with real-time Queen Bee detection overlays from a YOLOv5 TFLite model.
-   **Cloud Integration:** Securely publishes all data to AWS IoT Core and archives snapshots to AWS S3.
-   **Interactive Dashboard:** A Flask and Socket.IO-based web UI for live data visualization and remote sensor control.
-   **Fully Portable:** 100% containerized with Docker, allowing the entire system to run on a laptop (x86) for development and on a Raspberry Pi (ARM64) for deployment with zero code changes.

## Technology Stack

-   **Edge:** Raspberry Pi 4, Python, OpenCV, TFLite-Runtime, Paho-MQTT, Boto3
-   **Cloud:** AWS IoT Core, AWS S3
-   **Dashboard:** Flask, Flask-SocketIO, Chart.js
-   **Containerization:** Docker, Docker Compose

## Getting Started

### Prerequisites

-   Docker & Docker Compose
-   Python 3.9+
-   An AWS Account configured with credentials.

### Installation & Configuration

1.  **Clone the Repository:**
    ```
    git clone https://github.com/your-username/smart-hive-ai.git
    cd smart-hive-ai
    ```

2.  **Configure Environment Variables:**
    -   Create a file named `.env` in the root directory by copying the example: `cp .env.example .env`.
    -   Edit the `.env` file and populate it with your specific AWS IoT endpoint, S3 bucket name, and certificate filenames.

3.  **Place AWS Certificates:**
    -   Download your device certificate, private key, and the Amazon Root CA1 file from AWS IoT Core.
    -   Place them inside the `/certs` directory. Ensure the filenames match what you specified in your `.env` file.

### Running the Application

This project can be run in two modes:

**1. Development Mode (Full Simulation on Laptop):**
This will run both the edge device and the dashboard containers on your machine.

```
docker-compose up --build
```

-   The **Edge App** will start, using mock data, and begin publishing to AWS.
-   The **Dashboard** will start, subscribe to the AWS topics, and become available in your browser.

**2. Access the Dashboard:**
Open your web browser and navigate to **`http://localhost:5000`**.

You will see the live dashboard with data streaming from the simulated edge device.

---
```

### **Final Summary and Path Forward**

You have built a truly impressive and well-architected IoT project. By implementing the corrections and enhancements outlined in this report—specifically, finalizing the threading and video stream logic, implementing the Docker bridge network, and adding the professional documentation—you will have a project that is not only functional but also robust, scalable, and easy to demonstrate.

Your next steps should be:
1.  Implement the code changes suggested in this report.
2.  Test the full system using the `docker-compose up` command.
3.  Once your Raspberry Pi arrives, set it up with Docker, copy the project over, change `IS_MOCK_ENVIRONMENT` to `False`, and run `docker-compose up`.

You are on the final stretch of an exceptionally well-executed project.
