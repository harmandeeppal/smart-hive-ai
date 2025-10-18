# 🎤 Audio Processing Pipeline - Complete Detailed Explanation

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Complete Process Flow](#complete-process-flow)
3. [Component Deep Dive](#component-deep-dive)
4. [Windowed Inference Explained](#windowed-inference-explained)
5. [Feature Extraction Process](#feature-extraction-process)
6. [ML Model Pipeline](#ml-model-pipeline)
7. [Data Flow Diagram](#data-flow-diagram)
8. [Configuration & Parameters](#configuration--parameters)
9. [Error Handling & Edge Cases](#error-handling--edge-cases)

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Smart Hive AI System                            │
│                                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────┐               │
│  │   Browser   │◄───┤   Dashboard  │◄───┤  MQTT       │               │
│  │   (User)    │    │   Flask App  │    │  Broker     │               │
│  └─────────────┘    └──────────────┘    └─────────────┘               │
│         │                    │                   ▲                      │
│         │                    │                   │                      │
│         │              Socket.IO             MQTT Topic                 │
│         │              WebSocket          (audio/results)               │
│         │                    │                   │                      │
│         ▼                    ▼                   │                      │
│  [Trigger Audio]────────►[MQTT Publish]─────────┤                      │
│                         (audio/control)          │                      │
│                                                  │                      │
│                                         ┌────────┴────────┐             │
│                                         │  Audio Service  │             │
│                                         │  (Microservice) │             │
│                                         └─────────────────┘             │
│                                                  │                      │
│                                         ┌────────▼────────┐             │
│                                         │ AudioProcessor  │             │
│                                         │    (Core)       │             │
│                                         └─────────────────┘             │
│                                                  │                      │
│                                    ┌─────────────┼─────────────┐       │
│                                    │             │             │       │
│                            ┌───────▼──────┐  ┌──▼─────┐  ┌────▼────┐  │
│                            │  Microphone  │  │ librosa│  │  Model  │  │
│                            │  (Hardware)  │  │ (MFCC) │  │ (.pkl)  │  │
│                            └──────────────┘  └────────┘  └─────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Process Flow

### Phase 1: User Trigger (Dashboard)

**Location**: `dashboard/templates/index.html` + `dashboard/static/app.js`

```javascript
// Step 1: User clicks "Record 1 Minute & Analyze" button
document.getElementById('record-audio-btn').addEventListener('click', () => {
    // Step 2: Emit Socket.IO event to Flask backend
    socket.emit('trigger_audio_recording', {duration_sec: 60});
});
```

**What Happens:**
- User sees dashboard UI with "🎤 Record 1 Minute & Analyze" button
- Click triggers Socket.IO event `trigger_audio_recording`
- Button becomes disabled during recording
- Progress bar appears showing recording status

---

### Phase 2: Dashboard Backend Processing

**Location**: `dashboard/dashboard_app.py` (Lines 220-250)

```python
@socketio.on('trigger_audio_recording')
def handle_trigger_audio_recording(data):
    """
    Socket.IO event handler for triggering audio recording
    
    Flow:
    1. Receive trigger from web UI
    2. Extract duration parameter (default 60s)
    3. Build MQTT control message
    4. Publish to 'hive/audio/control' topic
    5. Notify audio microservice to start recording
    """
    duration = data.get('duration_sec', 60)
    
    # Build control message
    control_msg = {
        'command': 'record_and_classify',
        'duration_sec': duration,
        'timestamp': datetime.now().isoformat()
    }
    
    # Publish to MQTT topic that audio service listens to
    mqtt_client.publish(
        'hive/audio/control',
        json.dumps(control_msg),
        qos=1
    )
    
    # Emit recording_started event back to UI
    socketio.emit('recording_started', {'duration': duration})
```

**What Happens:**
- Dashboard Flask backend receives Socket.IO event
- Creates MQTT control message with recording parameters
- Publishes to `hive/audio/control` MQTT topic
- Audio microservice (separate container) is listening to this topic
- Sends confirmation back to browser via Socket.IO

---

### Phase 3: Audio Microservice Receives Command

**Location**: `ml_audio_service.py` (Lines 100-120)

```python
def on_message(client, userdata, msg):
    """
    MQTT message handler for audio service
    
    Listens to: 'hive/audio/control'
    """
    try:
        payload = msg.payload.decode('utf-8')
        
        if msg.topic == "hive/audio/control":
            command_data = json.loads(payload)
            
            # Check if this is a recording command
            if command_data.get('command') == 'record_and_classify':
                # Set flag to trigger recording in main loop
                self.recording_requested = True
                self.recording_duration = command_data.get('duration_sec', 60)
                logger.info(f"🎤 Recording requested: {self.recording_duration} seconds")
    except Exception as e:
        logger.error(f"Message parse error: {e}")
```

**What Happens:**
- Audio microservice runs in separate Docker container
- Continuously listens to MQTT topics via `on_message` callback
- When control message arrives, sets internal flag `recording_requested = True`
- Main service loop detects this flag and starts processing

---

### Phase 4: Audio Recording & Processing

**Location**: `ml_audio_service.py` (Lines 130-155)

```python
def run_audio_inference(self):
    """Main loop that waits for recording triggers"""
    
    while self.is_running:
        # Wait for recording trigger from dashboard
        if self.recording_requested:
            self.recording_requested = False
            
            logger.info(f"🎙️  Starting {self.recording_duration}s recording...")
            
            # Call AudioProcessor to handle everything
            results = self.audio_processor.record_and_classify(
                duration_sec=self.recording_duration
            )
            
            if results:
                # Publish results back to MQTT
                message = {
                    "timestamp": datetime.now().isoformat(),
                    "model_type": "audio_ml_classifier",
                    "results": results  # Contains classification, confidence, method, n_windows, etc.
                }
                
                # Publish to config.TOPIC_AUDIO_RESULTS
                self.mqtt_client.publish(
                    config.TOPIC_AUDIO_RESULTS,  # 'hive/audio/results'
                    json.dumps(message),
                    qos=1
                )
                logger.info(f"✅ Audio results published: {results.get('classification')}")
```

**What Happens:**
- Main service loop detects `recording_requested` flag
- Calls `audio_processor.record_and_classify()` (this is where the magic happens)
- Waits for processing to complete (60 seconds + inference time)
- Gets back comprehensive results dictionary
- Publishes results to `hive/audio/results` MQTT topic
- Dashboard backend is subscribed to this topic

---

### Phase 5: Core Audio Processing (AudioProcessor)

**Location**: `ml_audio_model/audio_processor.py` (Lines 480-540)

```python
def record_and_classify(self, duration_sec=30, use_windowing=True):
    """
    Complete audio processing pipeline
    
    Steps:
    1. Record audio from microphone
    2. Create overlapping windows
    3. Extract MFCC features from each window
    4. Run ML model on each window
    5. Aggregate predictions
    6. Return final classification
    """
    
    # Step 1: Record audio from microphone
    audio_data, sr = self.record_audio(duration_sec)
    if audio_data is None:
        return {"error": "Recording failed", "status": "failed"}
    
    # Step 2: Use windowed inference (recommended)
    if use_windowing:
        logger.info("Using windowed inference (recommended)")
        classification = self.classify_windows(audio_data)
        if classification.get("classification") == "error":
            return {"error": "Classification failed", "status": "failed"}
    else:
        # Legacy whole-file approach (not recommended)
        features = self.extract_features(audio_data)
        classification = self.classify(features)
    
    # Step 3: Optionally save recording
    if self.save_recordings:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audio_{timestamp}.npy"
        filepath = os.path.join(self.recordings_dir, filename)
        np.save(filepath, audio_data)
        logger.info(f"💾 Audio saved to {filepath}")
    
    # Step 4: Compile final result
    self.last_result = {
        "classification": classification["classification"],  # e.g., "queen_present"
        "confidence": classification["confidence"],          # e.g., 0.87
        "duration": duration_sec,
        "timestamp": time.time(),
        "method": classification.get("method"),              # e.g., "max_proba"
        "n_windows": classification.get("n_windows"),        # e.g., 119
        "window_results": classification.get("window_results"),  # Per-window details
        "status": "complete"
    }
    
    return self.last_result
```

**What Happens:**
- Coordinates entire audio processing pipeline
- Records raw audio from Raspberry Pi microphone
- Delegates to windowed inference method
- Saves recording if configured
- Returns comprehensive results dictionary

---

## Component Deep Dive

### 1. Microphone Recording

**Location**: `ml_audio_model/audio_processor.py` (Lines 145-198)

```python
def record_audio(self, duration: int) -> Tuple[Optional[np.ndarray], Optional[int]]:
    """
    Record audio from microphone using sounddevice.
    
    Args:
        duration (int): Recording duration in seconds
    
    Returns:
        Tuple[np.ndarray, int]: (audio_data, sample_rate) or (None, None)
    
    Technical Details:
        - Sample Rate: 22050 Hz (standard for speech/music)
        - Channels: 1 (mono)
        - Duration: User-specified (default 60s)
        - Buffer: In-memory numpy array
    """
    try:
        import sounddevice as sd
        
        logger.info(f"🎙️  Recording for {duration} seconds at {self.sample_rate}Hz...")
        
        # Record blocking (waits for full duration)
        audio_data = sd.rec(
            int(duration * self.sample_rate),  # Total samples
            samplerate=self.sample_rate,
            channels=1,  # Mono
            dtype='float32'
        )
        
        # Wait for recording to complete
        sd.wait()
        
        # Convert to 1D array
        audio_data = audio_data.flatten()
        
        logger.info(f"✅ Recording complete: {len(audio_data)} samples")
        return audio_data, self.sample_rate
        
    except Exception as e:
        logger.error(f"❌ Recording failed: {e}")
        return None, None
```

**Technical Specs:**
- **Hardware**: Raspberry Pi USB microphone
- **Sample Rate**: 22,050 Hz (22.05 kHz)
- **Bit Depth**: 32-bit float
- **Channels**: Mono (1 channel)
- **Duration**: Configurable (default 60 seconds)
- **Output**: NumPy array of shape `(samples,)` where `samples = duration × sample_rate`

**Example**:
- 60 seconds @ 22050 Hz = **1,323,000 samples**
- Memory: ~5.3 MB (1,323,000 × 4 bytes)

---

## Windowed Inference Explained

### Why Windowing?

**Problem**: The ML model was trained on 1-second audio clips, not entire 60-second recordings.

**Solution**: Split the recording into overlapping 1-second windows and classify each independently.

### Window Creation Process

**Location**: `ml_audio_model/audio_processor.py` (Lines 257-287)

```python
def create_windows(self, audio_data: np.ndarray) -> list:
    """
    Split audio into overlapping windows.
    
    Parameters (from config.py):
        - AUDIO_WINDOW_SECONDS = 1.0  # Window size
        - AUDIO_HOP_SECONDS = 0.5      # Hop size (overlap)
    
    Example with 10-second audio:
        Window 1: [0.0s - 1.0s]
        Window 2: [0.5s - 1.5s]  ← 50% overlap
        Window 3: [1.0s - 2.0s]
        Window 4: [1.5s - 2.5s]
        ...
        Window 19: [9.0s - 10.0s]
    
    Result: 19 windows from 10 seconds of audio
    """
    window_samples = int(self.window_seconds * self.sample_rate)  # 22050 samples
    hop_samples = int(self.hop_seconds * self.sample_rate)        # 11025 samples
    
    windows = []
    start = 0
    
    # Create overlapping windows
    while start + window_samples <= len(audio_data):
        window = audio_data[start:start + window_samples]
        windows.append(window)
        start += hop_samples
    
    # Handle last partial window (if >50% of window size)
    if start < len(audio_data):
        remaining = len(audio_data) - start
        if remaining >= window_samples * 0.5:
            # Pad with zeros to full window size
            window = audio_data[start:]
            window = np.pad(window, (0, window_samples - len(window)), mode='constant')
            windows.append(window)
    
    logger.debug(f"Created {len(windows)} windows from {len(audio_data)} samples")
    return windows
```

### Windowing Math

For **60-second recording** at **22050 Hz**:

```
Total samples: 60 × 22050 = 1,323,000 samples

Window size: 1.0s × 22050 = 22,050 samples
Hop size: 0.5s × 22050 = 11,025 samples

Number of windows = (Total samples - Window size) / Hop size + 1
                  = (1,323,000 - 22,050) / 11,025 + 1
                  = 118 + 1
                  = 119 windows
```

**Visualization**:
```
Audio Timeline (60 seconds):
|-------|-------|-------|-------|-------|-------|  ...  |-------|
0s     1s      2s      3s      4s      5s      6s  ...  60s

Windows (1s each, 0.5s hop):
[Window 1 ]
      [Window 2 ]
            [Window 3 ]
                  [Window 4 ]
                        [Window 5 ]
                              ...
                                          [Window 119]

Each window overlaps 50% with previous/next window
```

---

## Feature Extraction Process

### MFCC (Mel-Frequency Cepstral Coefficients)

**Location**: `ml_audio_model/audio_processor.py` (Lines 234-289)

```python
def extract_features(self, audio_data: np.ndarray) -> Optional[np.ndarray]:
    """
    Extract MFCC features matching training methodology.
    
    Feature Set:
        - 52 MFCC coefficients (mean + std)       = 104 features
        - 52 Delta (Δ) coefficients (mean + std)  = 104 features
        - 52 Delta-Delta (Δ²) (mean + std)        = 104 features
        ─────────────────────────────────────────────────────
        TOTAL                                     = 312 features
    
    Returns:
        np.ndarray: Shape (1, 312) - Ready for model input
    """
    try:
        import librosa
        
        # 1. Extract MFCC (52 coefficients - matching training)
        mfcc = librosa.feature.mfcc(
            y=audio_data,
            sr=self.sample_rate,
            n_mfcc=52  # Model trained with 52, not 13
        )
        # Shape: (52, time_frames)
        
        # 2. Compute statistics: mean and std for each coefficient
        mfcc_mean = np.mean(mfcc, axis=1)  # Shape: (52,)
        mfcc_std = np.std(mfcc, axis=1)    # Shape: (52,)
        
        # 3. Extract Delta (first derivative - rate of change)
        delta = librosa.feature.delta(mfcc)
        delta_mean = np.mean(delta, axis=1)  # Shape: (52,)
        delta_std = np.std(delta, axis=1)    # Shape: (52,)
        
        # 4. Extract Delta-Delta (second derivative - acceleration)
        delta_delta = librosa.feature.delta(mfcc, order=2)
        delta_delta_mean = np.mean(delta_delta, axis=1)  # Shape: (52,)
        delta_delta_std = np.std(delta_delta, axis=1)    # Shape: (52,)
        
        # 5. Combine all features into single vector
        features = np.concatenate([
            mfcc_mean,        # 52 features
            mfcc_std,         # 52 features
            delta_mean,       # 52 features
            delta_std,        # 52 features
            delta_delta_mean, # 52 features
            delta_delta_std   # 52 features
        ])  # Total: 312 features
        
        logger.debug(f"Extracted {len(features)} features")
        return features.reshape(1, -1)  # Shape: (1, 312)
        
    except Exception as e:
        logger.error(f"❌ Feature extraction failed: {e}")
        return None
```

### What is MFCC?

**MFCC** = Mel-Frequency Cepstral Coefficients

**Purpose**: Represent the power spectrum of sound in a way that mimics human hearing.

**Process**:
1. **Fourier Transform**: Convert audio from time → frequency domain
2. **Mel Scale**: Apply perceptual scale (humans hear low frequencies better)
3. **Log**: Take logarithm (human hearing is logarithmic)
4. **DCT**: Discrete Cosine Transform to get coefficients

**Why Delta and Delta-Delta?**
- **Delta (Δ)**: Captures how features change over time (velocity)
- **Delta-Delta (Δ²)**: Captures acceleration of changes
- These add temporal dynamics to static features

---

## ML Model Pipeline

### Model Structure

**Location**: Loaded from `models/audio_model.pkl`

```python
# Model is a dictionary containing full scikit-learn pipeline:
model_dict = {
    'model': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True),
    'scaler': StandardScaler(),
    'label_encoder': LabelEncoder(),
    'feature_selector': SelectFromModel(estimator=...)
}
```

### Pipeline Flow

**Location**: `ml_audio_model/audio_processor.py` (Lines 288-366)

```python
def classify_windows(self, audio_data: np.ndarray) -> Dict:
    """
    Complete windowed inference pipeline.
    
    Pipeline Steps:
    ┌─────────────────────────────────────────────────────────────┐
    │ 1. Audio Data (1,323,000 samples @ 60s)                     │
    │    ▼                                                         │
    │ 2. Create Windows (119 windows of 1s each)                  │
    │    ▼                                                         │
    │ 3. Extract Features (119 × 78 features)                     │
    │    ▼                                                         │
    │ 4. Feature Selection (select best features)                 │
    │    ▼                                                         │
    │ 5. Standardization (zero mean, unit variance)               │
    │    ▼                                                         │
    │ 6. SVM Classification (119 predictions)                     │
    │    ▼                                                         │
    │ 7. Aggregation (combine to single result)                   │
    │    ▼                                                         │
    │ 8. Final Result: queen_present/absent + confidence          │
    └─────────────────────────────────────────────────────────────┘
    """
    
    try:
        # Step 1: Create windows
        windows = self.create_windows(audio_data)
        if not windows:
            return {"classification": "error", "confidence": 0.0, "error": "No windows created"}
        
        # Step 2: Extract features from each window
        window_features = []
        for i, window in enumerate(windows):
            features = self.extract_features(window)
            if features is not None:
                window_features.append(features.flatten())
        
        if not window_features:
            return {"classification": "error", "confidence": 0.0, "error": "Feature extraction failed"}
        
        # Convert to matrix: Shape (n_windows, 78)
        features_matrix = np.array(window_features)
        logger.info(f"Extracted features from {len(window_features)} windows")
        
        # Step 3: Apply feature selector (if exists)
        if 'feature_selector' in self.model_dict and self.model_dict['feature_selector'] is not None:
            features_matrix = self.model_dict['feature_selector'].transform(features_matrix)
            logger.debug(f"Feature selection: {features_matrix.shape[1]} features selected")
        
        # Step 4: Apply scaler (standardization)
        if 'scaler' in self.model_dict and self.model_dict['scaler'] is not None:
            features_matrix = self.model_dict['scaler'].transform(features_matrix)
            logger.debug("Features scaled")
        
        # Step 5: Predict for each window
        predictions = self.model.predict(features_matrix)  # Shape: (119,)
        
        # Step 6: Get probabilities
        try:
            probabilities = self.model.predict_proba(features_matrix)  # Shape: (119, 2)
        except AttributeError:
            # Model doesn't support probabilities
            probabilities = np.zeros((len(predictions), 2))
            probabilities[np.arange(len(predictions)), predictions.astype(int)] = 1.0
        
        # Step 7: Aggregate predictions
        result = self._aggregate_predictions(predictions, probabilities)
        
        logger.info(f"Windowed classification: {result['classification']} (confidence: {result['confidence']:.3f})")
        return result
        
    except Exception as e:
        logger.error(f"❌ Windowed classification failed: {e}")
        return {"classification": "error", "confidence": 0.0, "error": str(e)}
```

### Aggregation Methods

**Location**: `ml_audio_model/audio_processor.py` (Lines 368-428)

```python
def _aggregate_predictions(self, predictions: np.ndarray, probabilities: np.ndarray) -> Dict:
    """
    Combine 119 window predictions into single final result.
    
    Three Methods:
    
    1. MAX_PROBA (default, most conservative):
       - Take the HIGHEST confidence across all windows
       - If ANY window has high confidence queen detection, flag it
       - Best for minimizing false negatives
       - Formula: final_confidence = max(window_confidences)
    
    2. MEAN_PROBA (balanced):
       - Average confidence across all windows
       - Balanced approach - needs consistent detection
       - Formula: final_confidence = mean(window_confidences)
    
    3. MAJORITY_VOTE (democratic):
       - Count how many windows predict each class
       - Majority class wins
       - Formula: final_prediction = most_common(window_predictions)
    """
    
    n_windows = len(predictions)
    
    # Get confidence scores for positive class (queen_present = 1)
    positive_probabilities = probabilities[:, 1]  # Shape: (119,)
    
    if self.aggregation_method == 'max_proba':
        # Conservative: Use maximum confidence
        final_confidence = np.max(positive_probabilities)
        final_prediction = 1 if final_confidence >= self.confidence_threshold else 0
    
    elif self.aggregation_method == 'mean_proba':
        # Balanced: Use average confidence
        final_confidence = np.mean(positive_probabilities)
        final_prediction = 1 if final_confidence >= self.confidence_threshold else 0
    
    elif self.aggregation_method == 'majority_vote':
        # Democratic: Use majority class
        final_prediction = 1 if np.sum(predictions) > len(predictions) / 2 else 0
        final_confidence = np.mean(positive_probabilities)
    
    # Decode label using label encoder
    if 'label_encoder' in self.model_dict:
        final_label = self.model_dict['label_encoder'].inverse_transform([final_prediction])[0]
    else:
        final_label = "queen_present" if final_prediction == 1 else "queen_absent"
    
    # Compile per-window results for debugging
    window_results = []
    for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
        window_results.append({
            'window': i + 1,
            'prediction': int(pred),
            'confidence': float(prob[int(pred)]),
            'queen_proba': float(prob[1])
        })
    
    return {
        'classification': final_label,        # "queen_present" or "queen_absent"
        'confidence': float(final_confidence),# 0.0 - 1.0
        'method': self.aggregation_method,    # "max_proba"
        'n_windows': n_windows,               # 119
        'window_results': window_results      # All 119 window details
    }
```

---

## Data Flow Diagram

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         AUDIO PROCESSING DATA FLOW                         │
└───────────────────────────────────────────────────────────────────────────┘

1. USER ACTION
   ┌──────────────────┐
   │ Browser          │
   │ Click "Record"   │
   └────────┬─────────┘
            │ Socket.IO: trigger_audio_recording
            ▼
   ┌──────────────────┐
   │ Dashboard Flask  │
   │ Backend          │
   └────────┬─────────┘
            │ MQTT Publish: hive/audio/control
            │ Payload: {command: "record_and_classify", duration_sec: 60}
            ▼

2. AUDIO SERVICE (Container: smart-hive-audio)
   ┌──────────────────────────────────────┐
   │ ml_audio_service.py                  │
   │ - Receives MQTT message               │
   │ - Sets recording_requested = True     │
   └───────────────┬──────────────────────┘
                   │ Call: audio_processor.record_and_classify(60)
                   ▼

3. AUDIO PROCESSOR (Core Logic)
   ┌──────────────────────────────────────────────────────────────┐
   │ AudioProcessor.record_and_classify()                          │
   │                                                               │
   │  Step 3.1: Record Audio                                      │
   │  ┌────────────────────────────────────┐                      │
   │  │ sounddevice.rec(duration=60s)      │                      │
   │  │ Returns: np.array([1,323,000])     │                      │
   │  └────────────────┬───────────────────┘                      │
   │                   ▼                                           │
   │  Step 3.2: Create Windows                                    │
   │  ┌────────────────────────────────────┐                      │
   │  │ create_windows()                   │                      │
   │  │ Input:  1,323,000 samples          │                      │
   │  │ Output: 119 windows × 22,050       │                      │
   │  └────────────────┬───────────────────┘                      │
   │                   ▼                                           │
   │  Step 3.3: Extract Features (per window)                     │
   │  ┌────────────────────────────────────┐                      │
   │  │ For each of 119 windows:           │                      │
   │  │   extract_features(window)         │                      │
   │  │   - 13 MFCC (mean + std)          │                      │
   │  │   - 13 Delta (mean + std)         │                      │
   │  │   - 13 Delta-Delta (mean + std)   │                      │
   │  │ Output: (119, 78) matrix           │                      │
   │  └────────────────┬───────────────────┘                      │
   │                   ▼                                           │
   │  Step 3.4: ML Pipeline                                       │
   │  ┌────────────────────────────────────┐                      │
   │  │ Feature Selection → (119, 60)      │                      │
   │  │ Standardization   → Z-score norm   │                      │
   │  │ SVM Predict       → 119 labels     │                      │
   │  │ Predict Proba     → (119, 2)       │                      │
   │  └────────────────┬───────────────────┘                      │
   │                   ▼                                           │
   │  Step 3.5: Aggregation                                       │
   │  ┌────────────────────────────────────┐                      │
   │  │ _aggregate_predictions()           │                      │
   │  │ Method: max_proba                  │                      │
   │  │ Result: {                          │                      │
   │  │   classification: "queen_present"  │                      │
   │  │   confidence: 0.87                 │                      │
   │  │   method: "max_proba"              │                      │
   │  │   n_windows: 119                   │                      │
   │  │   window_results: [...]            │                      │
   │  │ }                                  │                      │
   │  └────────────────┬───────────────────┘                      │
   └───────────────────┼────────────────────────────────────────  │
                       ▼

4. PUBLISH RESULTS
   ┌──────────────────────────────────────┐
   │ ml_audio_service.py                  │
   │ mqtt_client.publish(                 │
   │   topic: "hive/audio/results",       │
   │   payload: {                         │
   │     timestamp: "2025-10-19...",      │
   │     model_type: "audio_ml_...",      │
   │     results: {...}                   │
   │   }                                  │
   │ )                                    │
   └────────────────┬─────────────────────┘
                    │ MQTT: hive/audio/results
                    ▼

5. DASHBOARD RECEIVES RESULTS
   ┌──────────────────────────────────────┐
   │ Dashboard Backend                     │
   │ - Subscribed to: hive/audio/results   │
   │ - Receives MQTT message               │
   │ - Emits Socket.IO: audio_ml_update    │
   └────────────────┬─────────────────────┘
                    │ Socket.IO: audio_ml_update
                    ▼
   ┌──────────────────────────────────────┐
   │ Browser JavaScript                    │
   │ socket.on('audio_ml_update', data => {│
   │   updateAudioMLStatus(data);         │
   │ });                                  │
   │                                      │
   │ Updates UI:                          │
   │ - Classification: Queen Detected     │
   │ - Confidence: 87.0%                  │
   │ - Status: 👑 Queen Detected          │
   │ - Timestamp: 14:32:15               │
   └──────────────────────────────────────┘

Total Time: ~65 seconds (60s recording + 5s processing)
```

---

## Configuration & Parameters

### Configuration File

**Location**: `config.py` (Lines appended during audio fix)

```python
# Audio Processing Configuration (Added Oct 2025)
AUDIO_WINDOW_SECONDS = 1.0        # Window size for windowed inference
AUDIO_HOP_SECONDS = 0.5           # Hop size (50% overlap)
AUDIO_AGGREGATION_METHOD = 'max_proba'  # Aggregation: max_proba, mean_proba, majority_vote
AUDIO_MODEL_PATH = 'models/audio_model.pkl'  # Path to trained model
```

### Initialization Parameters

```python
AudioProcessor(
    model_path='models/audio_model.pkl',
    sample_rate=22050,                  # 22.05 kHz
    confidence_threshold=0.6,           # 60% minimum confidence
    save_recordings=False,              # Don't save by default
    recordings_dir="audio_recordings",
    window_seconds=1.0,                 # From config
    hop_seconds=0.5,                    # From config
    aggregation_method='max_proba'      # From config
)
```

### MQTT Topics

```python
# Control (Dashboard → Audio Service)
TOPIC_AUDIO_CONTROL = "hive/audio/control"

# Results (Audio Service → Dashboard)
TOPIC_AUDIO_RESULTS = "hive/audio/results"
```

---

## Error Handling & Edge Cases

### 1. Microphone Failures

```python
# audio_processor.py: record_audio()
try:
    audio_data = sd.rec(...)
    sd.wait()
except Exception as e:
    logger.error(f"❌ Recording failed: {e}")
    return None, None
```

**Handled**:
- Microphone not connected
- Permission denied
- Audio device busy

### 2. Feature Extraction Failures

```python
# audio_processor.py: extract_features()
try:
    mfcc = librosa.feature.mfcc(...)
except ImportError:
    logger.error("❌ librosa package not installed")
    return None
except Exception as e:
    logger.error(f"❌ Feature extraction failed: {e}")
    return None
```

**Handled**:
- Missing librosa dependency
- Corrupted audio data
- Invalid sample rates

### 3. Model Loading Failures

```python
# audio_processor.py: load_model()
try:
    self.model_dict = joblib.load(model_path)
    self.model = self.model_dict['model']
except FileNotFoundError:
    logger.error(f"❌ Model not found: {model_path}")
    self.enabled = False
except Exception as e:
    logger.error(f"❌ Model load failed: {e}")
    self.enabled = False
```

**Handled**:
- Model file missing
- Corrupted .pkl file
- Version mismatches

### 4. MQTT Connection Failures

```python
# ml_audio_service.py: setup_mqtt()
try:
    self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port)
    self.mqtt_client.loop_start()
except Exception as e:
    logger.error(f"❌ MQTT connection failed: {e}")
```

**Handled**:
- MQTT broker offline
- Network issues
- Authentication failures

### 5. Partial Windows

```python
# audio_processor.py: create_windows()
# Handle last partial window if >50% of window size
if start < len(audio_data):
    remaining = len(audio_data) - start
    if remaining >= window_samples * 0.5:
        window = audio_data[start:]
        window = np.pad(window, (0, window_samples - len(window)), mode='constant')
        windows.append(window)
```

**Handled**:
- Recording slightly shorter than expected
- Last window incomplete
- Zero-padding ensures consistent size

---

## Summary: Key Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Recording Duration** | 60 seconds | Configurable |
| **Sample Rate** | 22,050 Hz | Standard for audio ML |
| **Total Samples** | 1,323,000 | 60s × 22050 Hz |
| **Window Size** | 1.0 second | 22,050 samples |
| **Hop Size** | 0.5 seconds | 50% overlap |
| **Number of Windows** | 119 | From 60s recording |
| **Features per Window** | 312 | 52 MFCC × 3 × 2 (mean+std) |
| **Feature Matrix** | (119, 312) | All windows |
| **Model Type** | SVM (RBF kernel) | With probability |
| **Aggregation** | max_proba | Conservative |
| **Confidence Threshold** | 0.6 (60%) | Minimum for classification |
| **Total Processing Time** | ~65 seconds | 60s + 5s inference |
| **Memory Usage** | ~10 MB | Audio + features |

---

## File References

### Core Components
- **Audio Service**: `ml_audio_service.py` (183 lines)
- **Audio Processor**: `ml_audio_model/audio_processor.py` (555 lines)
- **Configuration**: `config.py` (with audio constants)
- **Dashboard Backend**: `dashboard/dashboard_app.py` (344 lines)
- **Dashboard Frontend**: `dashboard/static/app.js` (586 lines)
- **Dashboard UI**: `dashboard/templates/index.html`

### Supporting Files
- **Requirements**: `requirements-audio.txt`
- **Dockerfile**: `Dockerfile.audio`
- **Docker Compose**: `docker-compose.yml` (smart-hive-audio service)
- **Model**: `models/audio_model.pkl` (15.8 MB)
- **Documentation**: `AUDIO_FIX_COMPLETE.md`

---

## Conclusion

The audio processing pipeline is a sophisticated multi-stage system that:

1. **Receives user trigger** from web dashboard via Socket.IO
2. **Communicates via MQTT** between dashboard and audio service
3. **Records 60 seconds** of audio from Raspberry Pi microphone
4. **Creates 119 overlapping windows** (1s each, 0.5s hop)
5. **Extracts 78 MFCC features** from each window
6. **Applies ML pipeline** (feature selection → scaling → SVM)
7. **Aggregates predictions** using max_proba method
8. **Returns comprehensive results** with classification, confidence, and per-window details
9. **Publishes to MQTT** for dashboard consumption
10. **Updates UI in real-time** via Socket.IO WebSocket

The entire process takes approximately **65 seconds** and provides **high-confidence queen bee detection** with detailed windowed analysis.

---

**Created**: October 19, 2025  
**Author**: Smart Hive AI Team  
**Branch**: feature/audio-windowed-inference
