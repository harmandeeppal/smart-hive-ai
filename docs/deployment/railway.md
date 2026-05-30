# Railway Cloud Deployment — Smart Hive AI

Deploy the full demo stack to Railway so anyone can view the live dashboard
without cloning the repo or owning a Raspberry Pi.

## Architecture on Railway

```
Railway Project: smart-hive-ai
│
├── mosquitto   (eclipse-mosquitto:2)       ← internal MQTT broker
├── simulator   (demo/Dockerfile.simulator) ← synthetic sensor + camera frames
├── ml-audio    (Dockerfile.audio)          ← audio classification (DEMO_MODE)
├── ml-vision   (Dockerfile.vision)         ← YOLOv8 queen detection (DEMO_MODE)
└── dashboard   (Dockerfile.dashboard)      ← PUBLIC URL ← users visit this
```

Services talk to each other via Railway's private network.
Only `dashboard` gets a public HTTPS URL.

---

## Step 1 — Install Railway CLI and login

```bash
npm install -g @railway/cli
railway login
```

---

## Step 2 — Create the project and link repo

```bash
railway init          # choose "Empty project", name it smart-hive-ai
railway link          # link to the project you just created
```

---

## Step 3 — Deploy the dashboard (auto from railway.toml)

```bash
railway up
```

Railway reads `railway.toml` → builds `Dockerfile.dashboard` → deploys.

Then set environment variables:

```bash
railway variables set MQTT_BROKER=mosquitto.railway.internal
railway variables set MQTT_PORT=1883
railway variables set DEMO_MODE=true
railway variables set DEMO_PASSWORD=smarthive
railway variables set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
railway variables set HF_TOKEN=<your-huggingface-token>
```

---

## Step 4 — Add the mosquitto service

In the Railway dashboard → **+ New** → **Docker Image**:
- Image: `eclipse-mosquitto:2`
- Name: `mosquitto`

No environment variables needed. No public port (internal only).

---

## Step 5 — Add simulator, ml-audio, ml-vision services

For each service: Railway dashboard → **+ New → GitHub Repo → harmandeeppal/smart-hive-ai → branch: main**

Then set Dockerfile path: Service → Settings → Build → Dockerfile Path

| Service name | Dockerfile path | Key env vars |
|---|---|---|
| `simulator` | `demo/Dockerfile.simulator` | `MQTT_BROKER=mosquitto.railway.internal` |
| `ml-audio` | `Dockerfile.audio` | `MQTT_BROKER=mosquitto.railway.internal`, `DEMO_MODE=true`, `HF_TOKEN=<token>` |
| `ml-vision` | `Dockerfile.vision` | `MQTT_BROKER=mosquitto.railway.internal`, `VISION_CONFIDENCE_THRESHOLD=0.35`, `HF_TOKEN=<token>` |

---

## Environment variables — complete reference

| Variable | Services | Value |
|---|---|---|
| `MQTT_BROKER` | all except mosquitto | `mosquitto.railway.internal` |
| `MQTT_PORT` | all except mosquitto | `1883` |
| `DEMO_MODE` | dashboard, ml-audio | `true` |
| `DEMO_PASSWORD` | dashboard | your chosen login password |
| `SECRET_KEY` | dashboard | random 32-char hex string |
| `HF_TOKEN` | ml-audio, ml-vision | your Hugging Face token (Read access) |
| `VISION_CONFIDENCE_THRESHOLD` | ml-vision | `0.35` |

---

## Step 6 — Get the public URL

Dashboard service → Settings → Networking → **Generate Domain**

Your live demo will be at `https://smart-hive-ai-xxxx.up.railway.app`

---

## Verify the deployment

1. Open the Railway-generated URL
2. Log in with `DEMO_PASSWORD`
3. Sensor cards should update every 5 seconds
4. Enable **AI Vision** → queen bee bounding boxes appear
5. Enable **Audio** → waveform animates with real audio signal
6. Click **Record 30 Seconds & Analyze** → classification result appears

---

## Troubleshooting

**Dashboard blank / MQTT disconnected**
→ mosquitto service must be running first.
→ Confirm `MQTT_BROKER=mosquitto.railway.internal` (not `localhost`).

**ml-vision build times out**
→ PyTorch CPU wheel is ~800 MB — first build takes 10–15 min.
→ Railway → Service Settings → increase build timeout to 20 min.

**Models fail to download**
→ HF repo is private — `HF_TOKEN` must be set on ml-audio and ml-vision.
→ Token needs at least **Read** access to `harmandeeppal/smart-hive-ai`.

**No telemetry data**
→ Wait 30 s for simulator to start, then check its logs.
→ Confirm `MQTT_BROKER` is identical across all services.
