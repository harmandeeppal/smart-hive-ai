"""
Smart Hive AI — Demo Simulator

Generates biologically realistic beehive sensor data and publishes it to MQTT,
replacing the hardware edge app for local/cloud demo environments.

Publishes:
  hive/telemetry              — temperature, humidity, vibration, sound dB (every 5s)
  hive/telemetry/camera/frame — binary JPEG frames cycled from demo/sample_frames/ (every 3s)

Subscribes:
  hive/control/simulator      — accepts "start" / "stop" commands

Audio classification is handled by the audio service running in DEMO_MODE.
"""

import json
import math
import os
import random
import sys
import time
import logging
import threading
from datetime import datetime
from pathlib import Path

import numpy as np
import cv2
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [simulator] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TELEMETRY_INTERVAL = float(os.getenv("TELEMETRY_INTERVAL", "5"))
FRAME_INTERVAL = float(os.getenv("FRAME_INTERVAL", "3"))
VIDEO_FRAME_INTERVAL = float(os.getenv("VIDEO_FRAME_INTERVAL", "0.1"))  # ~10 fps for video
SAMPLE_FRAMES_DIR = Path(__file__).parent / "sample_frames"
SAMPLE_VIDEO_DIR = Path(__file__).parent / "sample_video"


class BeehiveSimulator:
    def __init__(self):
        self.running = False
        self._client = None
        self._connect()

    # ── MQTT ─────────────────────────────────────────────────────────────────

    def _connect(self):
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id="smart-hive-simulator")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

        for attempt in range(1, 11):
            try:
                self._client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                self._client.loop_start()
                logger.info(f"Connected to MQTT broker {MQTT_BROKER}:{MQTT_PORT}")
                return
            except Exception as exc:
                logger.warning(f"MQTT connect attempt {attempt}/10: {exc}")
                time.sleep(2)
        raise RuntimeError("Could not connect to MQTT broker after 10 attempts")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("hive/control/simulator")
            self.running = True
            logger.info("Subscribed to hive/control/simulator — simulator is RUNNING")
        else:
            logger.error(f"MQTT connect failed, rc={rc}")

    def _on_message(self, client, userdata, msg):
        cmd = msg.payload.decode().strip().lower()
        if cmd == "stop":
            self.running = False
            logger.info("Simulator paused via control topic")
        elif cmd == "start":
            self.running = True
            logger.info("Simulator resumed via control topic")

    # ── Data generation ───────────────────────────────────────────────────────

    @staticmethod
    def _activity(hour: float) -> float:
        """Forager activity 0.05–1.0, peaks at solar noon."""
        return max(0.05, math.sin((hour - 6) * math.pi / 12))

    def _telemetry(self) -> dict:
        h = datetime.now().hour + datetime.now().minute / 60.0
        a = self._activity(h)

        # Bees thermoregulate to ~35 °C; slight diurnal variation from ambient
        temp = 35.0 + 0.8 * math.sin((h - 12) * math.pi / 12) + random.gauss(0, 0.15)
        # Hive humidity 60–75 %; inversely coupled to temp
        humidity = 67.0 - 4.0 * math.sin((h - 6) * math.pi / 12) + random.gauss(0, 0.5)
        # Vibration low at night, forager spikes 5 % of the time
        vibration = 0.08 + 0.35 * a
        if random.random() < 0.05:
            vibration += random.uniform(0.3, 1.2)
        # Sound 52–64 dB, correlated with activity
        sound_db = 52.0 + 12.0 * a + random.gauss(0, 1.5)

        return {
            "timestamp": datetime.now().isoformat(),
            "temperature": round(temp, 2),
            "humidity": round(max(55.0, min(80.0, humidity)), 2),
            "vibration": round(max(0.0, vibration), 3),
            "sound_db": round(max(45.0, min(70.0, sound_db)), 1),
            "source": "simulator",
        }

    # ── Frame handling ────────────────────────────────────────────────────────

    def _load_frames(self) -> list:
        frames = []
        if SAMPLE_FRAMES_DIR.exists():
            patterns = ["*.jpg", "*.jpeg", "*.png"]
            paths = []
            for p in patterns:
                paths.extend(sorted(SAMPLE_FRAMES_DIR.glob(p)))
            for path in paths:
                img = cv2.imread(str(path))
                if img is not None:
                    frames.append(cv2.resize(img, (640, 480)))
                    logger.info(f"Loaded sample frame: {path.name}")

        if not frames:
            logger.info(
                "No images in demo/sample_frames/ — using generated placeholder. "
                "Add real beehive JPEGs for better vision demo."
            )
            frames.append(self._placeholder_frame())

        return frames

    @staticmethod
    def _placeholder_frame() -> np.ndarray:
        """Honeycomb-patterned placeholder frame."""
        img = np.full((480, 640, 3), (30, 80, 120), dtype=np.uint8)
        s = 30  # hex size
        for row_i, y in enumerate(range(0, 500, int(s * 1.5))):
            x_off = s if row_i % 2 else 0
            for x in range(-s, 660, s * 2):
                cx, cy = x + x_off, y
                pts = np.array([
                    [int(cx + s * math.cos(math.pi / 180 * (60 * i - 30))),
                     int(cy + s * math.sin(math.pi / 180 * (60 * i - 30)))]
                    for i in range(6)
                ], dtype=np.int32)
                cv2.polylines(img, [pts], isClosed=True, color=(0, 160, 220), thickness=1)

        cv2.putText(img, "Smart Hive AI — Demo Mode", (18, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(img, datetime.now().strftime("%Y-%m-%d  %H:%M:%S"), (18, 64),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        cv2.putText(img, "Add beehive images to demo/sample_frames/ for real vision demo",
                    (18, 465), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (160, 160, 160), 1)
        return img

    # ── Video source ──────────────────────────────────────────────────────────

    def _find_video(self):
        """Return path to first video in demo/sample_video/, or None."""
        if SAMPLE_VIDEO_DIR.exists():
            for ext in ("*.mp4", "*.avi", "*.mov", "*.mkv"):
                paths = sorted(SAMPLE_VIDEO_DIR.glob(ext))
                if paths:
                    return paths[0]
        return None

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        logger.info("=" * 55)
        logger.info("  Smart Hive AI — Demo Simulator starting")
        logger.info("=" * 55)

        # Prefer video over still images
        video_path = self._find_video()
        if video_path:
            cap = cv2.VideoCapture(str(video_path))
            frame_interval = VIDEO_FRAME_INTERVAL
            frames = None
            logger.info(f"Video mode: streaming {video_path.name} at ~{1/VIDEO_FRAME_INTERVAL:.0f} fps")
        else:
            cap = None
            frames = self._load_frames()
            frame_interval = FRAME_INTERVAL

        frame_idx = 0
        last_telemetry = 0.0
        last_frame = 0.0

        while True:
            now = time.time()

            if self.running:
                if now - last_telemetry >= TELEMETRY_INTERVAL:
                    data = self._telemetry()
                    self._client.publish("hive/telemetry", json.dumps(data), qos=1)
                    logger.debug(
                        f"Telemetry → {data['temperature']}°C  "
                        f"{data['humidity']}%  {data['sound_db']} dB"
                    )
                    last_telemetry = now

                if now - last_frame >= frame_interval:
                    if cap is not None:
                        ret, frame = cap.read()
                        if not ret:
                            # Loop video back to start
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            ret, frame = cap.read()
                        if ret:
                            frame = cv2.resize(frame, (640, 480))
                        else:
                            frame = self._placeholder_frame()
                    else:
                        frame = frames[frame_idx % len(frames)].copy()
                        if len(frames) == 1:
                            cv2.putText(frame, datetime.now().strftime("%H:%M:%S"),
                                        (18, 64), cv2.FONT_HERSHEY_SIMPLEX,
                                        0.55, (200, 200, 200), 1)
                        frame_idx += 1

                    _, buf = cv2.imencode(
                        ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70]
                    )
                    self._client.publish(
                        "hive/telemetry/camera/frame", buf.tobytes(), qos=0
                    )
                    last_frame = now

            time.sleep(0.04)


if __name__ == "__main__":
    sim = BeehiveSimulator()
    time.sleep(1)          # allow on_connect callback to fire
    sim.running = True     # start publishing immediately if MQTT connected
    try:
        sim.run()
    except KeyboardInterrupt:
        logger.info("Simulator stopped")
