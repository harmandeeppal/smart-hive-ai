#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Smart Hive AI architecture diagrams using Graphviz.

Outputs (PNG and SVG):
  docs/diagrams/standalone_vision.*
  docs/diagrams/edge_microservices.*

Prerequisites:
  - Graphviz installed (dot available on PATH)
  - Python package `graphviz` (pip install graphviz)
"""

from __future__ import annotations

from pathlib import Path

from graphviz import Digraph


def _apply_common_style(diagram: Digraph) -> None:
    diagram.graph_attr.update(
        {
            "rankdir": "TB",
            "splines": "true",
            "fontname": "Arial",
            "fontsize": "10",
            "pad": "0.2",
        }
    )
    diagram.node_attr.update(
        {
            "shape": "box",
            "style": "rounded,filled",
            "fillcolor": "white",
            "color": "#555555",
            "fontname": "Arial",
            "fontsize": "10",
        }
    )
    diagram.edge_attr.update(
        {
            "color": "#555555",
            "fontname": "Arial",
            "fontsize": "9",
        }
    )


def standalone_vision_diagram() -> Digraph:
    diagram = Digraph("standalone_vision", comment="Standalone Vision Architecture")
    _apply_common_style(diagram)

    pi_label = (
        "Raspberry Pi 4B+\\n(Standalone AI Vision Model)\\n\\n"
        "Components\\n"
        "• Pi Camera Module v3 (NoIR)\\n"
        "• 4 GB RAM, 32-GB SD card\\n"
        "• Python + OpenCV + PyTorch\\n\\n"
        "Processing Flow\\n"
        "1. Capture image frame (~10 FPS)\\n"
        "2. Run ML Vision model (YOLOv8)\\n"
        "3. Detect queen-bee bounding box\\n"
        "4. Annotate image in memory\\n"
        "5. Display result via dashboard"
    )
    diagram.node("pi", pi_label)

    display_label = 'HDMI / Local Display\\n("Queen Present" or "Not Present")'
    diagram.node("display", display_label)

    diagram.edge("pi", "display", arrowhead="normal")

    return diagram


def edge_microservices_diagram() -> Digraph:
    diagram = Digraph("edge_microservices", comment="Edge Microservices Architecture")
    _apply_common_style(diagram)

    # Optional AWS cluster
    with diagram.subgraph(name="cluster_aws") as aws_cluster:
        aws_cluster.attr(label="AWS Cloud (Optional)", color="#888888")
        aws_cluster.node("aws_iot", "IoT Core (MQTT)")
        aws_cluster.node("aws_ddb", "DynamoDB (Telemetry)\\n7-day storage")

    # Edge node cluster
    with diagram.subgraph(name="cluster_edge") as edge_cluster:
        edge_cluster.attr(label="Raspberry Pi 4 — Edge Node", color="#888888")

        sensors_label = (
            "Sensors (I²C/I²S)\\n"
            "• BME280 Temp/Hum\\n"
            "• LIS3DH Vibration\\n"
            "• INMP441 Mic"
        )
        edge_cluster.node("sensors", sensors_label)

        audio_label = (
            "Audio ML Service\\n"
            "Container: smart-hive-audio\\n"
            "• 1 s windows, MFCC (312)\\n"
            "• RandomForest model\\n"
            "• Output: {Normal|Swarming|Queenless}+confidence"
        )
        edge_cluster.node("audio_ml", audio_label)

        dashboard_label = (
            "Dashboard Service\\n"
            "Container: smart-hive-dashboard\\n"
            "• Live video\\n"
            "• Telemetry widgets\\n"
            "• Queen status alerts"
        )
        edge_cluster.node("dashboard", dashboard_label)

        flask_label = (
            "Flask + SocketIO API\\n"
            "• REST/WebSocket endpoints\\n"
            "• Aggregates MQTT topics"
        )
        edge_cluster.node("flask", flask_label)

        edge_cluster.node("mosquitto", "Local MQTT Broker\\nContainer: mosquitto")
        edge_cluster.node("camera", "USB Camera\\n(MJPEG stream)")
        edge_cluster.node(
            "vision",
            "Vision Service (optional)\\nContainer: smart-hive-vision\\n• YOLOv8 inference",
        )
        edge_cluster.node("browser", "User Browser")

        edge_cluster.edge(
            "sensors",
            "mosquitto",
            label="Telemetry\\nMQTT topic hive/telemetry",
        )
        edge_cluster.edge(
            "audio_ml",
            "mosquitto",
            label="Predictions\\nMQTT topic hive/audio",
        )
        edge_cluster.edge(
            "mosquitto",
            "audio_ml",
            label="Record/control\\nMQTT topic hive/audio/control",
        )
        edge_cluster.edge(
            "camera",
            "dashboard",
            label="MJPEG stream\\n(no vision AI)",
        )
        edge_cluster.edge(
            "camera",
            "vision",
            label="JPEG frames\\nMQTT topic hive/telemetry/camera/frame",
        )
        edge_cluster.edge(
            "vision",
            "mosquitto",
            label="Detections\\nMQTT topic hive/vision",
        )
        edge_cluster.edge(
            "mosquitto",
            "flask",
            label="Pub/Sub all topics",
        )
        edge_cluster.edge(
            "flask",
            "dashboard",
            label="UI updates\\n(WebSocket)",
        )
        edge_cluster.edge(
            "dashboard",
            "audio_ml",
            label="Recording trigger\\n(REST / MQTT control)",
            style="dashed",
        )
        edge_cluster.edge(
            "dashboard",
            "browser",
            label="HTTP / WebSocket UI",
        )

    # Optional cloud interactions
    diagram.edge(
        "mosquitto",
        "aws_iot",
        style="dashed",
        label="optional MQTT bridge",
    )
    diagram.edge(
        "flask",
        "aws_ddb",
        style="dashed",
        label="optional telemetry writes\\n(DynamoDB 7-day store)",
    )

    return diagram


def render_diagram(diagram: Digraph, out_path: Path) -> None:
    for fmt in ("png", "svg"):
        diagram.render(filename=str(out_path), format=fmt, cleanup=True)


def main() -> None:
    output_dir = Path("docs/diagrams")
    output_dir.mkdir(parents=True, exist_ok=True)

    render_diagram(standalone_vision_diagram(), output_dir / "standalone_vision")
    render_diagram(edge_microservices_diagram(), output_dir / "edge_microservices")

    print(f"Diagrams generated under: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
