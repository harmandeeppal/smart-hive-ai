"""
Smart Hive AI — Non-Docker Demo Runner

Starts all services as managed subprocesses in the correct boot order.
Use this when Docker is not available.

Boot order:
  mosquitto → audio → vision → dashboard → simulator (last)

The simulator starts last so all MQTT subscribers are ready before data flows.
"""

import os
import sys
import shutil
import time
import signal
import subprocess
import webbrowser
from pathlib import Path


def find_mosquitto() -> str:
    """Return the path to the mosquitto binary, searching common conda locations."""
    # Check PATH first (works on Linux/Mac and Windows system installs)
    found = shutil.which("mosquitto")
    if found:
        return found
    # conda on Windows installs to Library/sbin/ inside the env
    env_root = Path(sys.executable).parent
    for candidate in [
        env_root / "Library" / "sbin" / "mosquitto.exe",
        env_root / "Library" / "bin" / "mosquitto.exe",
        env_root / "Scripts" / "mosquitto.exe",
    ]:
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(
        "mosquitto not found. Install with: conda install -c conda-forge mosquitto"
    )

ROOT = Path(__file__).resolve().parent.parent

# ── Load .env.demo ────────────────────────────────────────────────────────────
env_file = ROOT / ".env.demo"
if env_file.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")
    except ImportError:
        print("python-dotenv not installed — reading .env.demo manually")
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

# ── Shared env ────────────────────────────────────────────────────────────────
DEMO_ENV = {
    **os.environ,
    "MQTT_BROKER": "localhost",
    "MQTT_PORT": "1883",
    "DEMO_MODE": "true",
}

processes: list[tuple[str, subprocess.Popen]] = []


def start(name: str, cmd: list, extra_env: dict | None = None) -> subprocess.Popen:
    env = {**DEMO_ENV, **(extra_env or {})}
    p = subprocess.Popen(cmd, cwd=str(ROOT), env=env)
    processes.append((name, p))
    print(f"  ✅  {name} started (PID {p.pid})")
    return p


def shutdown(sig=None, frame=None):
    print("\nShutting down all services...")
    for name, p in reversed(processes):
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            p.kill()
        print(f"  ✋  {name} stopped")
    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


def main():
    print("=" * 55)
    print("  Smart Hive AI Demo — Direct Run (no Docker)")
    print("=" * 55)
    print()

    # 1. MQTT broker — use demo config (no Docker paths, logs to stdout only)
    print("Starting MQTT broker...")
    mosquitto_bin = find_mosquitto()
    mosquitto_conf = str(ROOT / "demo" / "mosquitto.demo.conf")
    start("MQTT Broker", [mosquitto_bin, "-c", mosquitto_conf])
    time.sleep(2)

    # 2. Audio service (demo mode — no microphone required)
    print("Starting Audio Service (demo mode)...")
    start("Audio Service", [sys.executable, "ml_audio_service.py"])
    time.sleep(1)

    # 3. Vision service
    print("Starting Vision Service...")
    start("Vision Service", [sys.executable, "ml_vision_service.py"])
    time.sleep(1)

    # 4. Dashboard
    print("Starting Dashboard...")
    start("Dashboard", [sys.executable, "dashboard/dashboard_app.py"])
    time.sleep(2)

    # 5. Simulator — starts last so all subscribers are ready
    print("Starting Simulator...")
    start("Simulator", [sys.executable, "demo/simulator.py"])

    print()
    print("✅  All services running")
    print("   Dashboard → http://localhost:5000")
    print("   Press Ctrl+C to stop all services")
    print()

    webbrowser.open("http://localhost:5000")

    # Wait — if any process exits unexpectedly, report it once
    reported = set()
    while True:
        for name, p in processes:
            if name not in reported:
                ret = p.poll()
                if ret is not None:
                    print(f"⚠️  {name} exited with code {ret}")
                    reported.add(name)
        time.sleep(5)


if __name__ == "__main__":
    main()
