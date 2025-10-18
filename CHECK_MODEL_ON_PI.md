# 🔍 Diagnostic: Check Model File on Raspberry Pi

Run these commands on the Pi to diagnose the model file issue:

## Quick Status Check

```bash
cd ~/smart-hive-ai

echo "=== 1. Check if model file exists on Pi ==="
ls -lh models/vision_model.pt

echo "=== 2. Check file type (real vs stub) ==="
file models/vision_model.pt

echo "=== 3. Check file size in bytes ==="
wc -c models/vision_model.pt

echo "=== 4. Show first 100 bytes ==="
head -c 100 models/vision_model.pt

echo "=== 5. Check if it's a text stub (Git LFS pointer) ==="
head -1 models/vision_model.pt
```

## What You'll See

### ✅ If File is REAL (6.2 MB model):
```
-rw-r--r-- 1 pi pi 6230250 Oct 17 12:34 vision_model.pt   ← Size ~6.2M
data                                                        ← file type
6230250                                                     ← byte count
PK (binary data)                                            ← starts with PK (ZIP format)
```

### ❌ If File is a Git LFS STUB (pointer):
```
-rw-r--r-- 1 pi pi 131 Oct 17 12:34 vision_model.pt       ← Size ~131 bytes
ASCII text                                                  ← file type
131                                                         ← byte count
version https://git-lfs.github.com/spec/v1                 ← starts with text pointer
```

## Full Diagnostic Bundle

Run this single command to get ALL diagnostic info at once:

```bash
cd ~/smart-hive-ai && \
echo "=== MODEL FILE DIAGNOSTICS ===" && \
echo "" && \
echo "File Location:" && \
pwd && \
echo "" && \
echo "File Properties:" && \
ls -lh models/vision_model.pt && \
echo "" && \
echo "File Type:" && \
file models/vision_model.pt && \
echo "" && \
echo "File Size (bytes):" && \
wc -c < models/vision_model.pt && \
echo "" && \
echo "First 150 characters:" && \
head -c 150 models/vision_model.pt && \
echo "" && \
echo "Is it accessible?" && \
test -r models/vision_model.pt && echo "✅ Readable" || echo "❌ Not readable" && \
echo "" && \
echo "=== DOCKER CHECK ===" && \
echo "Is file visible in vision service container?" && \
docker exec smart-hive-vision ls -lh /app/models/vision_model.pt 2>&1 && \
echo "" && \
echo "File inside container (first 100 bytes):" && \
docker exec smart-hive-vision head -c 100 /app/models/vision_model.pt 2>&1
```

## Expected Output Scenarios

### Scenario A: File exists and is REAL
```
-rw-r--r-- 1 pi pi 6230250
data
6230250
PK (binary)
✅ Readable
-rw-r--r-- 1 root root 6230250
PK (binary)
→ PROBLEM SOLVED! Model is accessible in Docker ✅
```

### Scenario B: File is a Git LFS stub on Pi
```
-rw-r--r-- 1 pi pi 131
ASCII text
131
version https://git-lfs.github.com/spec/v1
✅ Readable
-rw-r--r-- 1 root root 131
version https://git-lfs.github.com/spec/v1
→ SOLUTION: Need to download real file (see next section)
```

### Scenario C: File doesn't exist on Pi
```
ls: cannot access 'models/vision_model.pt': No such file or directory
→ SOLUTION: Copy file from Windows to Pi
```

---

## Solutions Based on Diagnosis

### If Scenario B (Git LFS stub):

```bash
# Option 1: Force Git LFS to download
cd ~/smart-hive-ai
git lfs pull --force
git lfs checkout --force

# Verify it worked
ls -lh models/vision_model.pt
# Should now show 6.2M

# Restart Docker to reload mounted file
docker compose restart smart-hive-vision
```

### If Scenario C (File missing):

```bash
# Copy from Windows machine to Pi
# Run this on Windows (or use WinSCP, FileZilla):
scp C:\Users\harma\OneDrive\ -\ AUT\ University\IDE_Workspace\aut_projects\smart-hive-ai\models\vision_model.pt pi@raspberrypi:~/smart-hive-ai/models/

# Then on Pi:
docker compose restart smart-hive-vision
```

---

## Verify the Fix Worked

After applying the solution, run:

```bash
echo "=== Verifying Fix ===" && \
docker logs smart-hive-vision | grep -i "model loaded\|error.*model" | tail -5 && \
echo "" && \
echo "=== Service Status ===" && \
docker compose ps smart-hive-vision
```

Expected output:
```
✅ YOLO model loaded successfully
smart-hive-vision    Up (healthy)
```

---

## Please Run and Share Output

Please run the **Full Diagnostic Bundle** command above on your Pi and share the complete output here. This will tell us exactly what the issue is and what the solution should be.
