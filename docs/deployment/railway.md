# Railway Cloud Deployment — Smart Hive AI

Deploy the full demo stack to Railway so anyone can view the live dashboard
without cloning the repo or owning a Raspberry Pi.

## Architecture on Railway

```
Railway Project: smart-hive-ai
│
├── mosquitto   (eclipse-mosquitto:2)  ← internal MQTT broker
├── simulator   (demo/Dockerfile.simulator) ← synthetic sensor data
├── ml-audio    (Dockerfile.audio)     ← audio classification
├── ml-vision   (Dockerfile.vision)    ← YOLOv8 queen detection
└── dashboard   (Dockerfile.dashboard) ← PUBLIC URL ← users visit this
```

Services communicate internally via Railway's private network.
Only `dashboard` exposes a public URL.

---

## Prerequisites

- Railway account → https://railway.app
- Railway CLI: `npm install -g @railway/cli` then `railway login`
- This repo pushed to GitHub

---

## Step 1 — Create the Railway project

```bash
railway init
# Choose "Empty project", name it "smart-hive-ai"
```

---

## Step 2 — Add the mosquitto service

In the Railway dashboard → **New Service** → **Docker Image**:
- Image: `eclipse-mosquitto:2`
- Service name: `mosquitto`

Add a custom config volume or use the default (anonymous access, port 1883).
No environment variables needed.

---

## Step 3 — Add the dashboard service (auto-detected from railway.toml)

```bash
railway up
```

Railway reads `railway.toml` and deploys `Dockerfile.dashboard`.

Set these environment variables in the Railway dashboard for this service:

| Variable | Value |
|----------|-------|
| `MQTT_BROKER` | `mosquitto.railway.internal` |
| `MQTT_PORT` | `1883` |
| `DEMO_MODE` | `true` |
| `DEMO_PASSWORD` | *(choose a password for the login page)* |
| `SECRET_KEY` | *(random 32-char string — keep secret)* |
| `PORT` | `5000` |

---

## Step 4 — Add the simulator service

In Railway dashboard → **New Service** → **GitHub Repo** (same repo):
- Service name: `simulator`
- Dockerfile path: `demo/Dockerfile.simulator`

Environment variables:

| Variable | Value |
|----------|-------|
| `MQTT_BROKER` | `mosquitto.railway.internal` |
| `MQTT_PORT` | `1883` |
| `TELEMETRY_INTERVAL` | `5` |
| `FRAME_INTERVAL` | `3` |

---

## Step 5 — Add the ml-audio service

New Service → GitHub Repo (same repo):
- Service name: `ml-audio`
- Dockerfile path: `Dockerfile.audio`

Environment variables:

| Variable | Value |
|----------|-------|
| `MQTT_BROKER` | `mosquitto.railway.internal` |
| `MQTT_PORT` | `1883` |
| `DEMO_MODE` | `true` |

---

## Step 6 — Add the ml-vision service

New Service → GitHub Repo (same repo):
- Service name: `ml-vision`
- Dockerfile path: `Dockerfile.vision`

Environment variables:

| Variable | Value |
|----------|-------|
| `MQTT_BROKER` | `mosquitto.railway.internal` |
| `MQTT_PORT` | `1883` |
| `VISION_CONFIDENCE_THRESHOLD` | `0.35` |

---

## Step 7 — Verify

1. Open the Railway-generated dashboard URL (e.g. `https://smart-hive-ai.up.railway.app`)
2. Log in with `DEMO_PASSWORD`
3. Check all sensor cards update every 5 seconds
4. Enable AI Vision — queen bee bounding boxes should appear
5. Enable Audio and click "Record 30 Seconds" — classification result should appear

---

## Environment variables summary

Generate a secure `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

| Service | Key variables |
|---------|--------------|
| dashboard | `MQTT_BROKER`, `SECRET_KEY`, `DEMO_PASSWORD`, `DEMO_MODE=true`, `PORT=5000` |
| simulator | `MQTT_BROKER`, `MQTT_PORT` |
| ml-audio | `MQTT_BROKER`, `DEMO_MODE=true` |
| ml-vision | `MQTT_BROKER`, `VISION_CONFIDENCE_THRESHOLD=0.35` |
| mosquitto | *(none)* |

---

## Troubleshooting

**Dashboard shows "MQTT disconnected"**
→ Check `MQTT_BROKER=mosquitto.railway.internal` is set correctly.
→ Ensure mosquitto service is running and healthy.

**No telemetry data**
→ Simulator service may be starting. Wait 30s, check simulator logs.

**Vision detection never fires**
→ Lower `VISION_CONFIDENCE_THRESHOLD` to `0.25`.
→ Check ml-vision service logs — first startup downloads model weights (~6 MB).

**Build timeout on ml-vision**
→ PyTorch CPU wheel is ~800 MB. Railway may need 10–15 min on first build.
→ Set the build timeout to 20 min in Railway service settings.
