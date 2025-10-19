# ⚠️ Documentation Folder - Important Notice

## Documentation Status

**This folder contains mixed documentation** - some current, some legacy/outdated.

### 📍 START HERE - Current Documentation

**For up-to-date information, refer to the ROOT documentation:**

1. **[../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)** - **Master Index & Getting Started** ⭐
2. **[../README.md](../README.md)** - Project overview and features
3. **[../BUILD_CONTAINERS_GUIDE.md](../BUILD_CONTAINERS_GUIDE.md)** - Deployment instructions

### 📂 Files in This Folder

| File | Status | Description |
|------|--------|-------------|
| **CONFIGURATION_GUIDE.md** | ✅ Updated | Configuration settings (sensors, Audio ML, thresholds) |
| **DEPLOYMENT.md** | ✅ Updated | Raspberry Pi deployment guide |
| **TROUBLESHOOTING.md** | ⚠️ Partial | Basic troubleshooting (see root docs for comprehensive guides) |
| **SETUP_AND_DEPLOYMENT.md** | ⚠️ Outdated | Contains legacy info, see warning at top |
| **VIDEO_STREAM_CONFIGURATION.md** | ⚠️ Legacy | Describes unused Vision AI features |
| **historical/** | 📦 Archive | Original project plan and ML implementation guide |

### 🚨 What Changed?

**Features NOT in current implementation:**
- ❌ **S3 Image Uploads** - Configured but disabled (`ENABLE_S3=false`)
- ❌ **Vision ML / YOLO Detection** - TFLite model exists but not used
- ❌ **Queen Bee Detection** - Not implemented

**Features CURRENTLY WORKING:**
- ✅ **USB Camera** - Live video streaming (no AI detection)
- ✅ **Audio ML** - Random Forest classifier for hive sound analysis
- ✅ **Sensor Monitoring** - BME280 (temp/humidity), LIS3DH (vibration), INMP441 (microphone)
- ✅ **Local MQTT** - Mosquitto broker for inter-container messaging
- ✅ **DynamoDB** - Optional cloud storage (disabled by default)

### 📚 Recommended Reading Order

**For new users:**
1. [../README.md](../README.md) - Understand what the system does
2. [../DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) - Complete guide with quick start
3. [../BUILD_CONTAINERS_GUIDE.md](../BUILD_CONTAINERS_GUIDE.md) - Deploy to Raspberry Pi

**For configuration:**
- [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) - Adjust settings
- [../config.py](../config.py) - Edit directly

**For troubleshooting:**
- [../USB_CAMERA_TROUBLESHOOTING.md](../USB_CAMERA_TROUBLESHOOTING.md) - Camera issues
- [../AUDIO_TROUBLESHOOTING.md](../AUDIO_TROUBLESHOOTING.md) - Audio ML issues
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General hardware/sensor issues

### 🏛️ Historical Documentation

**Original project documentation preserved in `historical/` folder:**
- `historical/original_plan.md` - Initial project plan (includes S3, Vision ML objectives)
- `historical/ML_MODELS_IMPLEMENTATION_GUIDE.md` - YOLO vision implementation guide (697 lines)

These files are kept for reference but **do not reflect the current system**.

### 💡 Pro Tip

**Always check the root folder first!** The most accurate and up-to-date documentation is in the project root:
```
smart-hive-ai/
├── DOCUMENTATION_INDEX.md    ⭐ Start here
├── README.md                 ⭐ Project overview
├── BUILD_CONTAINERS_GUIDE.md ⭐ Deployment
├── USB_CAMERA_TROUBLESHOOTING.md
├── AUDIO_TROUBLESHOOTING.md
└── docs/                     📂 You are here
```

---

**Last Updated:** December 2024  
**Current System:** Audio ML + Sensor Monitoring + Live Camera (NO Vision ML, NO S3)
