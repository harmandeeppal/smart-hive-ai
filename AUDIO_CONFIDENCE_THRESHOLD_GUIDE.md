# Audio Confidence Threshold Configuration Guide

## ✅ **What Was Fixed**

**Previous Issue**: The `AUDIO_CONFIDENCE_THRESHOLD` in `config.py` was defined but NOT being passed to the AudioProcessor, so it was using a hardcoded default of 0.6.

**Fix Applied**: Now the config value is properly connected and actually used!

---

## 🎯 **How Confidence Threshold Works**

### **Classification Process:**

1. **Model Prediction**: The ML model outputs a probability for "queen_present" (0.0 to 1.0)
2. **Threshold Comparison**: Compare confidence to `AUDIO_CONFIDENCE_THRESHOLD`
3. **Decision**:
   - If `confidence >= threshold` → Accept the prediction
   - If `confidence < threshold` → Return opposite classification

### **Example with Current Threshold (0.6):**

**Scenario 1: Queen Detected**
```python
Model output: queen_present with confidence 0.856 (85.6%)
Threshold: 0.6 (60%)
Decision: 0.856 >= 0.6 ✅ TRUE
Result: "queen_present" with 85.6% confidence
```

**Scenario 2: Queen Not Detected** (Your recent test)
```python
Model output: queen_present with confidence 0.462 (46.2%)
Threshold: 0.6 (60%)
Decision: 0.462 >= 0.6 ❌ FALSE
Result: "queen_absent" with 46.2% confidence
(Threshold not met, so opposite classification returned)
```

**Scenario 3: Borderline Case**
```python
Model output: queen_present with confidence 0.65 (65%)
Threshold: 0.6 (60%)
Decision: 0.65 >= 0.6 ✅ TRUE
Result: "queen_present" with 65% confidence
```

---

## ⚙️ **How to Configure**

### **Edit config.py (Line 311):**

```python
# Current setting (default)
AUDIO_CONFIDENCE_THRESHOLD = 0.6  # 60% threshold

# More sensitive (catches more detections, but more false positives)
AUDIO_CONFIDENCE_THRESHOLD = 0.5  # 50% threshold

# More conservative (fewer false positives, but might miss some detections)
AUDIO_CONFIDENCE_THRESHOLD = 0.7  # 70% threshold

# Very conservative (only very confident detections)
AUDIO_CONFIDENCE_THRESHOLD = 0.8  # 80% threshold
```

### **After Changing:**

1. **Save `config.py`**
2. **Rebuild the container**:
   ```bash
   cd ~/smart-hive-ai
   git pull origin feature/audio-windowed-inference
   docker-compose build --no-cache smart-hive-audio
   docker-compose up -d smart-hive-audio
   ```
3. **Test with recording**
4. **Monitor logs**:
   ```bash
   docker logs -f smart-hive-audio
   ```

You should see:
```
INFO: ✅ Audio processor initialized with windowed inference
INFO:    Window: 1.0s, Hop: 0.5s, Aggregation: max_proba
INFO:    Confidence threshold: 0.6 (60%)  ← NEW LOG SHOWING YOUR THRESHOLD
```

---

## 📊 **Threshold Tuning Guide**

### **When to Lower Threshold (e.g., 0.5)**

**Symptoms:**
- Queen is present but system reports "queen_absent"
- Confidence scores are in 50-60% range when queen is actually there
- Missing too many valid detections (false negatives)

**Solution:**
```python
AUDIO_CONFIDENCE_THRESHOLD = 0.5  # Lower threshold
```

**Tradeoff**: May get more false positives (detecting queen when not there)

---

### **When to Raise Threshold (e.g., 0.7)**

**Symptoms:**
- System reports "queen_present" when queen is actually absent
- Getting false alarms
- Too many borderline detections (60-70% confidence)

**Solution:**
```python
AUDIO_CONFIDENCE_THRESHOLD = 0.7  # Higher threshold
```

**Tradeoff**: May miss some valid detections (false negatives)

---

### **Recommended Threshold by Use Case**

| Use Case | Threshold | Reasoning |
|----------|-----------|-----------|
| **Research/Testing** | 0.5 (50%) | Catch all possible detections for analysis |
| **Balanced Production** | 0.6 (60%) | **DEFAULT** - Good balance of accuracy |
| **Alert-Based System** | 0.7 (70%) | Reduce false alarms, only high confidence |
| **Critical Monitoring** | 0.8 (80%) | Only very confident detections |

---

## 🧪 **Testing Different Thresholds**

### **Method 1: Quick Test**

1. Record audio with known condition (queen present or absent)
2. Note the confidence score in logs
3. Adjust threshold accordingly
4. Re-test same audio

### **Method 2: A/B Testing**

Test multiple threshold values and track results:

| Threshold | Queen Present Count | Queen Absent Count | False Positives | False Negatives |
|-----------|---------------------|-------------------|-----------------|-----------------|
| 0.5 | ? | ? | ? | ? |
| 0.6 | ? | ? | ? | ? |
| 0.7 | ? | ? | ? | ? |

Choose the threshold with best accuracy for your hive.

---

## 📈 **Understanding Confidence Scores**

### **Confidence Ranges:**

- **90-100%**: Very high confidence (rare, excellent audio quality)
- **75-90%**: High confidence (strong signal)
- **60-75%**: Moderate confidence (acceptable, some ambiguity)
- **50-60%**: Low confidence (borderline, noisy audio)
- **Below 50%**: Very low confidence (opposite prediction returned)

### **Factors Affecting Confidence:**

1. **Audio Quality**:
   - Clear audio → Higher confidence
   - Background noise → Lower confidence
   - Wind/interference → Lower confidence

2. **Queen Bee Activity**:
   - Strong queen sounds → Higher confidence
   - Weak/intermittent sounds → Lower confidence
   - Mixed sounds → Medium confidence

3. **Recording Duration**:
   - Longer recordings (60s) → More windows → Better aggregation
   - Shorter recordings (10s) → Fewer windows → Less reliable

---

## 🔍 **Monitoring Confidence in Logs**

After rebuilding with the fix, you'll see:

```bash
INFO: ✅ Audio processor initialized with windowed inference
INFO:    Window: 1.0s, Hop: 0.5s, Aggregation: max_proba
INFO:    Confidence threshold: 0.6 (60%)  ← Your configured threshold
...
INFO: Windowed classification: queen_absent (confidence: 0.462)
                                              ↑
                                   This is compared to threshold
```

**Decision Logic:**
```
If 0.462 >= 0.6:  ← FALSE
    Result: queen_absent (because threshold not met)
Else:
    Result: queen_absent
```

---

## 🎛️ **Advanced Configuration**

### **Current Configuration (config.py):**

```python
# Windowing settings (match training)
AUDIO_WINDOW_SECONDS = 1.0      # 1-second windows
AUDIO_HOP_SECONDS = 0.5         # 50% overlap

# Aggregation method
AUDIO_AGGREGATION_METHOD = 'max_proba'  # Use maximum confidence across windows

# Confidence threshold
AUDIO_CONFIDENCE_THRESHOLD = 0.6  # 60% minimum confidence
```

### **Aggregation Methods:**

1. **`max_proba`** (Current, Conservative):
   - Uses **highest** confidence across all windows
   - Good for detecting strong queen signals
   - Less sensitive to noise

2. **`mean_proba`** (Balanced):
   - Uses **average** confidence across all windows
   - More sensitive to overall presence
   - Can be affected by noisy windows

3. **`majority_vote`** (Democratic):
   - Uses **majority** vote from all windows
   - Each window votes yes/no
   - Less dependent on confidence scores

---

## 🚀 **Deployment Steps**

1. **Edit config.py**:
   ```python
   AUDIO_CONFIDENCE_THRESHOLD = 0.6  # Your chosen threshold
   ```

2. **Pull latest code** (on Raspberry Pi):
   ```bash
   cd ~/smart-hive-ai
   git pull origin feature/audio-windowed-inference
   ```

3. **Rebuild container**:
   ```bash
   docker-compose build --no-cache smart-hive-audio
   docker-compose up -d smart-hive-audio
   ```

4. **Verify configuration**:
   ```bash
   docker logs smart-hive-audio | grep "Confidence threshold"
   ```

   Should show:
   ```
   INFO: Confidence threshold: 0.6 (60%)
   ```

5. **Test recording**:
   - Go to dashboard
   - Click "Record 1 Minute & Analyze"
   - Check results

---

## 📝 **Summary**

✅ **Fixed**: Config threshold now actually works  
✅ **Configurable**: Change `AUDIO_CONFIDENCE_THRESHOLD` in `config.py`  
✅ **Logged**: Threshold shown in startup logs  
✅ **Tunable**: Adjust based on your needs (0.5-0.8 recommended)  

**Default**: 0.6 (60%) - Balanced, recommended starting point  
**Testing**: Start with 0.6, adjust based on real-world results  

---

## 🐝 **Example Scenarios**

### **Scenario 1: Your Recent Test**
```
Audio: Office/ambient noise (no queen bee)
Model: queen_present confidence 0.462 (46.2%)
Threshold: 0.6 (60%)
Decision: 0.462 < 0.6 → Below threshold
Result: queen_absent ✅ CORRECT
```

### **Scenario 2: Queen Detected**
```
Audio: Strong queen bee sounds
Model: queen_present confidence 0.856 (85.6%)
Threshold: 0.6 (60%)
Decision: 0.856 >= 0.6 → Above threshold
Result: queen_present ✅ CORRECT
```

### **Scenario 3: Borderline Detection**
```
Audio: Weak queen sounds with noise
Model: queen_present confidence 0.58 (58%)
Threshold: 0.6 (60%)
Decision: 0.58 < 0.6 → Below threshold
Result: queen_absent ⚠️ MISSED (false negative)

Solution: Lower threshold to 0.5 if this happens frequently
```

---

**Need help tuning? Test with different thresholds and share the results!** 🐝🎵
