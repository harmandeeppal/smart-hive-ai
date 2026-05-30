document.addEventListener('DOMContentLoaded', () => {
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // --- STATE ---
    const sensorStates = { temperature: true, humidity: true, vibration: true, sound: true, vision: true, audio: true };
    let vibrationHistory = [];

    // --- DOM ---
    const elements = {
        lastUpdated: document.getElementById('last-updated'),
        temp:  { val: document.getElementById('temp-value'),  bar: document.querySelector('#temp-bar'),  status: document.getElementById('temp-status'),  action: document.getElementById('temp-action') },
        hum:   { val: document.getElementById('hum-value'),   bar: document.querySelector('#hum-bar'),   status: document.getElementById('hum-status'),   action: document.getElementById('hum-action') },
        vib:   { val: document.getElementById('vib-value'),   magnitude: document.querySelector('#vib-magnitude'), trend: document.getElementById('vib-trend'), status: document.getElementById('vib-status'), action: document.getElementById('vib-action') },
        sound: { val: document.getElementById('sound-value'), volume: document.querySelector('#sound-volume'), frequency: document.querySelector('#sound-frequency'), status: document.getElementById('sound-status'), action: document.getElementById('sound-action') },
        ai:    { snapshotTime: document.getElementById('ai-snapshot-time') }
    };

    // --- HELPERS ---
    function parseTimestamp(ts) {
        // Handles both ISO strings ("2026-05-29T20:38:14") and Unix seconds (1780043896)
        if (typeof ts === 'string') return new Date(ts);
        return new Date(ts * 1000);
    }

    function toNZTime(date, opts) {
        return date.toLocaleString('en-NZ', { timeZone: 'Pacific/Auckland', ...opts });
    }

    function generateSparkline(data) {
        const chars = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
        if (data.length < 2) return '';
        const max = Math.max(...data);
        return data.map(d => chars[Math.floor((d / (max || 1)) * (chars.length - 1))]).join('');
    }

    // --- SOCKET LISTENERS ---
    socket.on('connect', () => console.log('Connected to dashboard'));

    socket.on('telemetry_update', data => {
        updateTimestamp(data.timestamp);
        if (sensorStates.temperature && data.temperature !== undefined) updateTemperature(data.temperature);
        if (sensorStates.humidity    && data.humidity    !== undefined) updateHumidity(data.humidity);
        // Accept either vibration_rms (hardware) or vibration (simulator)
        const vib = data.vibration_rms !== undefined ? data.vibration_rms : data.vibration;
        if (sensorStates.vibration   && vib            !== undefined) updateVibration(vib);
        if (sensorStates.sound       && data.sound_db  !== undefined) updateSound(data.sound_db, data.sound_freq);
        if (data.sound_db !== undefined) {
            currentSoundDb = data.sound_db;
            const dbEl = document.getElementById('audio-db-value');
            if (dbEl && sensorStates.audio) dbEl.textContent = `${data.sound_db.toFixed(1)} dB`;
        }
    });

    // Vision ML results (from YOLO service via hive/vision/detection)
    socket.on('vision_ml_update', data => {
        if (sensorStates.vision) updateVisionDetection(data);
    });

    // Legacy vision update (from edge-app)
    socket.on('vision_update', data => {
        if (sensorStates.vision) updateVisionDetection(data);
    });

    socket.on('audio_ml_update', data => updateAudioMLStatus(data));
    socket.on('recording_started', data => startRecordingProgress(data.duration));
    socket.on('video_status',     data => syncVideoToggle(data));
    socket.on('ai_vision_status', data => syncAiVisionToggle(data));

    // --- TIMESTAMP ---
    function updateTimestamp(timestamp) {
        const date = parseTimestamp(timestamp);
        if (isNaN(date)) { elements.lastUpdated.textContent = 'Last Updated: --'; return; }
        elements.lastUpdated.textContent = 'Last Updated: ' + toNZTime(date, {
            year: 'numeric', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
        });
    }

    // --- TEMPERATURE ---
    function updateTemperature(temp) {
        elements.temp.val.textContent = `${temp.toFixed(1)} °C`;
        const MIN = 28, MAX = 41, OPT_MIN = 33, OPT_MAX = 36;
        let status, action;
        if (temp < OPT_MIN)      { status = '❄️ Too Cold'; action = 'LOW TEMP ALERT: Check food stores. Install entrance reducer. Consider insulation.'; }
        else if (temp > OPT_MAX) { status = '☀️ Too Hot';  action = 'HIGH TEMP ALERT: Open entrance fully. Provide shade cloth and ventilation.'; }
        else                     { status = '✓ Optimal';   action = 'None required.'; }
        elements.temp.status.textContent = status;
        elements.temp.action.textContent = action;
        const pct = Math.min(100, Math.max(0, ((temp - MIN) / (MAX - MIN)) * 100));
        elements.temp.bar.style.setProperty('--marker-pos', `${pct}%`);
    }

    // --- HUMIDITY ---
    function updateHumidity(hum) {
        elements.hum.val.textContent = `${hum.toFixed(1)} %`;
        const MIN = 40, MAX = 80, OPT_MIN = 50, OPT_MAX = 70;
        let status, action;
        if (hum < OPT_MIN)      { status = '💦 Too Dry'; action = 'LOW HUMIDITY: Provide water source. Check syrup concentration.'; }
        else if (hum > OPT_MAX) { status = '💧 Too Wet'; action = 'HIGH HUMIDITY: Clear all vents. Improve bottom-board ventilation.'; }
        else                    { status = '✓ Optimal';  action = 'None required.'; }
        elements.hum.status.textContent = status;
        elements.hum.action.textContent = action;
        const pct = Math.min(100, Math.max(0, ((hum - MIN) / (MAX - MIN)) * 100));
        elements.hum.bar.style.setProperty('--marker-pos', `${pct}%`);
    }

    // --- VIBRATION ---
    function updateVibration(rms) {
        elements.vib.val.textContent = `${rms.toFixed(4)} RMS`;
        let status, action;
        if (rms > 0.15)     { status = '🚨 Agitation Alert';   action = 'Hive disturbed or under attack. Avoid opening for 2+ hours.'; }
        else if (rms < 0.02){ status = '🛑 Low Activity Alert'; action = 'Possible cluster issue. Inspect for weakness.'; }
        else                { status = '✓ Normal Activity';     action = 'None required.'; }
        elements.vib.status.textContent = status;
        elements.vib.action.textContent = action;
        elements.vib.magnitude.style.setProperty('--magnitude', `${Math.min(100, (rms / 0.3) * 100)}%`);
        vibrationHistory.push(rms);
        if (vibrationHistory.length > 10) vibrationHistory.shift();
        elements.vib.trend.textContent = generateSparkline(vibrationHistory);
    }

    // --- SOUND ---
    function updateSound(db, freq) {
        if (db === undefined || db === null) return;
        elements.sound.val.textContent = `${db.toFixed(1)} dB`;
        const volPct = Math.min(100, Math.max(0, ((db - 40) / 30) * 100));
        elements.sound.volume.style.setProperty('--magnitude', `${volPct}%`);
        if (freq !== undefined && freq !== null) {
            const freqPct = Math.min(100, Math.max(0, ((freq - 200) / 400) * 100));
            elements.sound.frequency.style.setProperty('--magnitude', `${freqPct}%`);
            let status, action;
            if (freq >= 450)                     { status = '🏃 SWARM PREDICTION'; action = 'Imminent swarming. Schedule colony split.'; }
            else if (freq >= 350)                { status = '👑 QUEEN STATUS ALERT'; action = 'Abnormal sound. Check for eggs/larvae.'; }
            else if (freq < 150 && db < 42)      { status = '💀 DISTRESS ALERT';    action = 'Sudden silence. Check for pesticide exposure.'; }
            else                                 { status = '✓ Healthy Hum';         action = 'None required.'; }
            elements.sound.status.textContent = status;
            elements.sound.action.textContent = action;
        } else {
            elements.sound.status.textContent = 'Volume Only';
            elements.sound.action.textContent = 'Frequency analysis unavailable.';
        }
    }

    // --- VISION DETECTION + BOUNDING BOXES ---
    const detectionOverlay = document.getElementById('detection-overlay');
    const overlayCtx = detectionOverlay ? detectionOverlay.getContext('2d') : null;
    let boxClearTimer = null;

    function drawBoundingBoxes(boxes, confidence) {
        if (!overlayCtx || !detectionOverlay) return;
        const W = detectionOverlay.offsetWidth  || detectionOverlay.width;
        const H = detectionOverlay.offsetHeight || detectionOverlay.height;
        detectionOverlay.width  = W;
        detectionOverlay.height = H;
        overlayCtx.clearRect(0, 0, W, H);
        const scaleX = W / 640, scaleY = H / 480;
        boxes.forEach(box => {
            const [x1, y1, x2, y2] = box;
            const bx = x1 * scaleX, by = y1 * scaleY, bw = (x2 - x1) * scaleX, bh = (y2 - y1) * scaleY;
            overlayCtx.strokeStyle = '#ff4444';
            overlayCtx.lineWidth = 2;
            overlayCtx.strokeRect(bx, by, bw, bh);
            overlayCtx.fillStyle = 'rgba(255,68,68,0.7)';
            overlayCtx.fillRect(bx, by - 18, 110, 18);
            overlayCtx.fillStyle = '#fff';
            overlayCtx.font = 'bold 12px sans-serif';
            overlayCtx.fillText(`👑 Queen ${(confidence * 100).toFixed(0)}%`, bx + 4, by - 4);
        });
        if (boxClearTimer) clearTimeout(boxClearTimer);
        boxClearTimer = setTimeout(() => overlayCtx && overlayCtx.clearRect(0, 0, detectionOverlay.width, detectionOverlay.height), 3000);
    }

    function updateVisionDetection(data) {
        // Handle both 'detected' (YOLO service) and 'queen_detected' (legacy edge-app)
        const detected    = data.detected ?? data.queen_detected ?? false;
        const confidence  = data.confidence ?? 0;
        const boxes       = data.boxes ?? [];
        const snapshotEl  = elements.ai.snapshotTime;

        if (detected) {
            if (boxes.length > 0) drawBoundingBoxes(boxes, confidence);
            const t = parseTimestamp(data.timestamp);
            snapshotEl.textContent = isNaN(t) ? 'Just now' : toNZTime(t, { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
        }
    }

    // --- AUDIO ML STATUS ---
    function updateAudioMLStatus(data) {
        const classification = data.results?.classification ?? data.classification ?? 'Unknown';
        const confidence     = data.results?.confidence     ?? data.confidence     ?? 0;

        const clEl  = document.getElementById('audio-classification');
        const cfEl  = document.getElementById('audio-confidence');
        const stEl  = document.getElementById('audio-ml-status');
        const laEl  = document.getElementById('audio-last-analysis');

        // Human-readable label
        const label = classification === 'queen_present' ? '👑 Queen Present'
                    : classification === 'queen_absent'  ? 'Queen Absent'
                    : classification;
        clEl.textContent = label;
        cfEl.textContent = `${(confidence * 100).toFixed(1)}%`;
        stEl.textContent = classification === 'queen_present' ? '👑 Queen Detected' : 'Analysis Complete';

        const now = new Date();
        laEl.textContent = toNZTime(now, { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });

        document.getElementById('recording-progress').style.display = 'none';
        document.getElementById('record-audio-btn').disabled = false;
    }

    // --- RECORDING PROGRESS ---
    function startRecordingProgress(duration) {
        const prog = document.getElementById('recording-progress');
        const fill = document.getElementById('progress-fill');
        const text = document.getElementById('progress-text');
        const btn  = document.getElementById('record-audio-btn');
        prog.style.display = 'block';
        btn.disabled = true;
        let elapsed = 0;
        const iv = setInterval(() => {
            elapsed++;
            fill.style.width = `${(elapsed / duration) * 100}%`;
            text.textContent = `Recording: ${elapsed}s / ${duration}s`;
            if (elapsed >= duration) { clearInterval(iv); text.textContent = 'Processing audio...'; }
        }, 1000);
    }

    // --- CLEAR HELPERS (called when sensor is toggled off) ---
    function clearTemperature() {
        elements.temp.val.textContent = '-- °C';
        elements.temp.status.textContent = '--';
        elements.temp.action.textContent = '--';
        elements.temp.bar.style.setProperty('--marker-pos', '0%');
    }
    function clearHumidity() {
        elements.hum.val.textContent = '-- %';
        elements.hum.status.textContent = '--';
        elements.hum.action.textContent = '--';
        elements.hum.bar.style.setProperty('--marker-pos', '0%');
    }
    function clearVibration() {
        elements.vib.val.textContent = '-- RMS';
        elements.vib.status.textContent = '--';
        elements.vib.action.textContent = '--';
        elements.vib.magnitude.style.setProperty('--magnitude', '0%');
        elements.vib.trend.textContent = '--';
        vibrationHistory = [];
    }
    function clearSound() {
        elements.sound.val.textContent = '-- dB';
        elements.sound.status.textContent = '--';
        elements.sound.action.textContent = '--';
        elements.sound.volume.style.setProperty('--magnitude', '0%');
        elements.sound.frequency.style.setProperty('--magnitude', '0%');
    }
    const clearFns = { temperature: clearTemperature, humidity: clearHumidity, vibration: clearVibration, sound: clearSound };

    // --- TOGGLE BUTTONS (sensor cards) ---
    document.querySelectorAll('.toggle-btn[data-sensor]').forEach(btn => {
        const sensor = btn.dataset.sensor;
        btn.addEventListener('click', () => {
            sensorStates[sensor] = !sensorStates[sensor];
            const state = sensorStates[sensor] ? 'on' : 'off';
            socket.emit('toggle_sensor', { sensor, state });
            btn.textContent = `Toggle: ${state.toUpperCase()}`;
            sensorStates[sensor] ? btn.classList.remove('off') : btn.classList.add('off');
            if (!sensorStates[sensor] && clearFns[sensor]) clearFns[sensor]();
        });
    });

    // --- VIDEO TOGGLE ---
    const videoToggleBtn  = document.getElementById('video-toggle-btn');
    const aiVisionToggleBtn = document.getElementById('ai-vision-toggle-btn');
    const videoFeed = document.getElementById('video-feed');

    function setVideoOff() {
        if (videoFeed) { videoFeed.style.display = 'none'; }
        // Show black placeholder
        const container = videoFeed ? videoFeed.parentElement : null;
        if (container && !document.getElementById('video-blank')) {
            const blank = document.createElement('div');
            blank.id = 'video-blank';
            blank.style.cssText = 'width:100%;background:#000;aspect-ratio:4/3;display:flex;align-items:center;justify-content:center;color:#444;font-size:0.9rem;';
            blank.textContent = 'Video OFF';
            container.insertBefore(blank, videoFeed);
        }
        // Force AI Vision off too
        setAiVisionOff();
    }

    function setVideoOn() {
        if (videoFeed) { videoFeed.style.display = 'block'; }
        const blank = document.getElementById('video-blank');
        if (blank) blank.remove();
    }

    function setAiVisionOff() {
        if (!aiVisionToggleBtn) return;
        aiVisionToggleBtn.dataset.state = 'off';
        aiVisionToggleBtn.querySelector('.toggle-state').textContent = 'OFF';
        document.getElementById('ai-vision-status-text').textContent = 'OFF';
        aiVisionToggleBtn.classList.remove('ai-active');
        aiVisionToggleBtn.disabled = true;
        // Clear any drawn bounding boxes
        if (overlayCtx && detectionOverlay) overlayCtx.clearRect(0, 0, detectionOverlay.width, detectionOverlay.height);
        elements.ai.snapshotTime.textContent = '--';
        socket.emit('toggle_ml_sensor', { sensor: 'ml_vision', state: 'off' });
    }

    if (videoToggleBtn) {
        videoToggleBtn.addEventListener('click', () => {
            const newState = videoToggleBtn.dataset.state === 'on' ? 'off' : 'on';
            videoToggleBtn.dataset.state = newState;
            videoToggleBtn.querySelector('.toggle-state').textContent = newState.toUpperCase();
            document.getElementById('video-status-text').textContent = newState.toUpperCase();
            socket.emit('toggle_ml_sensor', { sensor: 'video', state: newState });
            if (newState === 'off') { setVideoOff(); }
            else { setVideoOn(); if (aiVisionToggleBtn) aiVisionToggleBtn.disabled = false; }
        });
    }

    if (aiVisionToggleBtn) {
        aiVisionToggleBtn.addEventListener('click', () => {
            if (videoToggleBtn && videoToggleBtn.dataset.state === 'off') return; // can't enable when video is off
            const newState = aiVisionToggleBtn.dataset.state === 'on' ? 'off' : 'on';
            aiVisionToggleBtn.dataset.state = newState;
            aiVisionToggleBtn.querySelector('.toggle-state').textContent = newState.toUpperCase();
            document.getElementById('ai-vision-status-text').textContent = newState.toUpperCase();
            socket.emit('toggle_ml_sensor', { sensor: 'ml_vision', state: newState });
            if (newState === 'on') { aiVisionToggleBtn.classList.add('ai-active'); }
            else {
                aiVisionToggleBtn.classList.remove('ai-active');
                if (overlayCtx && detectionOverlay) overlayCtx.clearRect(0, 0, detectionOverlay.width, detectionOverlay.height);
                elements.ai.snapshotTime.textContent = '--';
            }
        });
    }

    function syncVideoToggle(data) {
        if (!videoToggleBtn) return;
        const state = data.enabled ? 'on' : 'off';
        videoToggleBtn.dataset.state = state;
        videoToggleBtn.querySelector('.toggle-state').textContent = state.toUpperCase();
        document.getElementById('video-status-text').textContent = state.toUpperCase();
    }

    function syncAiVisionToggle(data) {
        if (!aiVisionToggleBtn) return;
        const state = data.enabled ? 'on' : 'off';
        aiVisionToggleBtn.dataset.state = state;
        aiVisionToggleBtn.querySelector('.toggle-state').textContent = state.toUpperCase();
        document.getElementById('ai-vision-status-text').textContent = state.toUpperCase();
        data.enabled ? aiVisionToggleBtn.classList.add('ai-active') : aiVisionToggleBtn.classList.remove('ai-active');
    }

    // --- AUDIO TOGGLE ---
    const audioToggleBtn  = document.getElementById('audio-toggle-btn');
    const recordAudioBtn  = document.getElementById('record-audio-btn');

    if (audioToggleBtn) {
        audioToggleBtn.addEventListener('click', () => {
            const newState = audioToggleBtn.dataset.state === 'on' ? 'off' : 'on';
            audioToggleBtn.dataset.state = newState;
            audioToggleBtn.textContent = `🎤 Audio: ${newState.toUpperCase()}`;
            sensorStates.audio = newState === 'on';
            newState === 'on' ? audioToggleBtn.classList.remove('off') : audioToggleBtn.classList.add('off');
            // Disable record button and clear display when audio is OFF
            if (newState === 'off') {
                flatlineWaveform();
                if (recordAudioBtn) { recordAudioBtn.disabled = true; recordAudioBtn.style.opacity = '0.4'; }
                document.getElementById('audio-classification').textContent = '--';
                document.getElementById('audio-confidence').textContent = '--';
                document.getElementById('audio-ml-status').textContent = 'Paused';
                document.getElementById('audio-db-value').textContent = '-- dB';
            } else {
                if (recordAudioBtn) { recordAudioBtn.disabled = false; recordAudioBtn.style.opacity = '1'; }
                document.getElementById('audio-ml-status').textContent = 'Waiting...';
            }
            socket.emit('toggle_ml_sensor', { sensor: 'audio', state: newState });
        });
    }

    // --- AUDIO WAVEFORM (real samples from audio service) ---
    const audioCanvas = document.getElementById('audio-waveform');
    const audioCtx    = audioCanvas ? audioCanvas.getContext('2d') : null;
    const WAVEFORM_LEN = 240;            // rolling buffer — ~2 seconds of 0.5s packets × 60 pts
    let waveformData   = new Array(WAVEFORM_LEN).fill(0);
    let currentSoundDb = 0;

    function drawWaveform() {
        if (!audioCtx || !audioCanvas) return;
        const W = audioCanvas.width, H = audioCanvas.height, mid = H / 2;
        audioCtx.fillStyle = '#0d0d1a';
        audioCtx.fillRect(0, 0, W, H);
        audioCtx.strokeStyle = '#1a1a3e'; audioCtx.lineWidth = 1;
        for (let i = 1; i < 4; i++) { audioCtx.beginPath(); audioCtx.moveTo(0, (H / 4) * i); audioCtx.lineTo(W, (H / 4) * i); audioCtx.stroke(); }
        audioCtx.strokeStyle = '#00ff88'; audioCtx.lineWidth = 2;
        audioCtx.beginPath();
        const step = W / waveformData.length;
        waveformData.forEach((v, i) => {
            const x = i * step, y = mid + v * mid * 0.85;
            i === 0 ? audioCtx.moveTo(x, y) : audioCtx.lineTo(x, y);
        });
        audioCtx.stroke();
        audioCtx.strokeStyle = '#2a2a5e'; audioCtx.lineWidth = 1;
        audioCtx.beginPath(); audioCtx.moveTo(0, mid); audioCtx.lineTo(W, mid); audioCtx.stroke();
    }

    // Receive real waveform packets from the audio service
    socket.on('audio_waveform', data => {
        if (!sensorStates.audio) return;
        const samples = data.samples || [];
        if (samples.length === 0) return;
        // Scroll old data left, append new packet
        waveformData.splice(0, samples.length);
        waveformData.push(...samples);
        drawWaveform();

        // Level bars driven by RMS of the packet
        const rms = Math.sqrt(samples.reduce((s, v) => s + v * v, 0) / samples.length);
        const levelBars = document.querySelectorAll('.level-bar');
        const activeBars = Math.floor(Math.min(rms * 3, 1) * levelBars.length);
        levelBars.forEach((bar, i) => {
            if (i < activeBars) { bar.classList.add('active'); bar.style.height = `${10 + i * 9}%`; }
            else                { bar.classList.remove('active'); bar.style.height = '5%'; }
        });
    });

    // When audio is toggled off, flatline immediately
    function flatlineWaveform() {
        waveformData = new Array(WAVEFORM_LEN).fill(0);
        drawWaveform();
        document.querySelectorAll('.level-bar').forEach(b => { b.classList.remove('active'); b.style.height = '5%'; });
        const dbEl = document.getElementById('audio-db-value');
        if (dbEl) dbEl.textContent = '-- dB';
    }

    // Draw initial flatline
    if (audioCanvas) drawWaveform();

    // --- RECORD BUTTON ---
    document.getElementById('record-audio-btn')?.addEventListener('click', () => {
        const btn  = document.getElementById('record-audio-btn');
        const prog = document.getElementById('recording-progress');
        const fill = document.getElementById('progress-fill');
        const text = document.getElementById('progress-text');
        const stat = document.getElementById('audio-ml-status');
        const DURATION = 30;

        btn.disabled = true; btn.textContent = '🎙️ Recording...';
        prog.style.display = 'block'; stat.textContent = 'Recording in progress...';
        socket.emit('trigger_audio_recording', { duration: DURATION });

        let elapsed = 0;
        const iv = setInterval(() => {
            elapsed++;
            fill.style.width = `${(elapsed / DURATION) * 100}%`;
            text.textContent = `Recording: ${elapsed}s / ${DURATION}s`;
            if (elapsed >= DURATION) { clearInterval(iv); stat.textContent = 'Processing...'; text.textContent = 'Processing audio...'; }
        }, 1000);

        setTimeout(() => {
            btn.disabled = false;
            btn.textContent = '🎤 Record 30 Seconds & Analyze';
            prog.style.display = 'none'; fill.style.width = '0%';
        }, (DURATION + 5) * 1000);
    });

    // --- SESSION KEEPALIVE ---
    setInterval(() => fetch('/heartbeat', { method: 'POST' }).catch(() => {}), 60000);
    window.addEventListener('beforeunload', () => navigator.sendBeacon('/session/end'));
});
