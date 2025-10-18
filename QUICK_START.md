# 🚀 Quick Start: Building Containers on Raspberry Pi

## ✅ Files Ready to Transfer to Pi

All necessary files are now ready in this repository:

```
✅ Dockerfile.edge           (878 bytes)
✅ Dockerfile.dashboard      (515 bytes) 
✅ Dockerfile.vision         (764 bytes) - NEW
✅ Dockerfile.audio          (726 bytes) - NEW
✅ docker-compose.yml
✅ requirements-edge.txt
✅ requirements-dashboard.txt
✅ requirements-vision.txt
✅ requirements-audio.txt
✅ All Python service files
```

---

## 🎯 Next Steps on Your Raspberry Pi

### 1️⃣ Pull Latest Code

```bash
ssh pi@192.168.88.16
cd ~/smart-hive-ai
git pull origin main
```

### 2️⃣ Verify New Dockerfiles Exist

```bash
ls -la Dockerfile.*
# Should show all 4 files including the NEW vision and audio Dockerfiles
```

### 3️⃣ Build All Containers

```bash
# Quick build (all at once - 40-55 minutes total)
docker-compose build --no-cache

# Or build one by one (recommended for debugging)
docker-compose build --no-cache dashboard          # 3-5 min
docker-compose build --no-cache edge-app           # 10-15 min
docker-compose build --no-cache smart-hive-vision  # 15-20 min
docker-compose build --no-cache smart-hive-audio   # 10-15 min
```

### 4️⃣ Start Everything

```bash
docker-compose up -d
docker-compose ps
```

### 5️⃣ Verify Services

```bash
docker logs smart-hive-audio --tail 20
# Look for: "AudioProcessor imported successfully"
# Look for: "librosa version: 0.10.0"

docker logs smart-hive-vision --tail 20
# Look for: "YOLO model loaded"

docker logs smart-hive-edge --tail 20  
# Look for: "Camera initialized successfully"
```

---

## 📚 Full Documentation

See `BUILD_CONTAINERS_GUIDE.md` for:
- Detailed step-by-step instructions
- Troubleshooting guide
- Verification checklist
- Expected output examples

---

## ⚡ Ultra Quick Command (Expert Mode)

If you're confident everything is set up:

```bash
cd ~/smart-hive-ai
git pull origin main
docker-compose down
docker builder prune -af
docker-compose build --no-cache
docker-compose up -d
docker-compose logs -f
```

Done! 🎉
