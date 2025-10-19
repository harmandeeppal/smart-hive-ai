document.addEventListener('DOMContentLoaded', () => {
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // --- STATE MANAGEMENT ---
    const sensorStates = { temperature: true, humidity: true, vibration: true, sound: true, vision: true };
    let vibrationHistory = [];

    // --- DOM ELEMENTS ---
    const elements = {
        lastUpdated: document.getElementById('last-updated'),
        temp: { val: document.getElementById('temp-value'), bar: document.querySelector('#temp-bar'), status: document.getElementById('temp-status'), action: document.getElementById('temp-action') },
        hum: { val: document.getElementById('hum-value'), bar: document.querySelector('#hum-bar'), status: document.getElementById('hum-status'), action: document.getElementById('hum-action') },
        vib: { val: document.getElementById('vib-value'), magnitude: document.querySelector('#vib-magnitude'), trend: document.getElementById('vib-trend'), status: document.getElementById('vib-status'), action: document.getElementById('vib-action') },
        sound: { val: document.getElementById('sound-value'), volume: document.querySelector('#sound-volume'), frequency: document.querySelector('#sound-frequency'), status: document.getElementById('sound-status'), action: document.getElementById('sound-action') },
        ai: { status: document.getElementById('ai-status-text'), snapshotTime: document.getElementById('ai-snapshot-time') }
    };

    // --- SOCKET.IO LISTENERS ---
    socket.on('connect', () => console.log('Connected to dashboard server!'));

    socket.on('telemetry_update', data => {
        console.log('Received telemetry:', data);
        updateTimestamp(data.timestamp);
        
        // Only update if sensor is enabled
        if (sensorStates.temperature && data.temperature !== undefined) {
            updateTemperature(data.temperature);
        }
        if (sensorStates.humidity && data.humidity !== undefined) {
            updateHumidity(data.humidity);
        }
        if (sensorStates.vibration && data.vibration_rms !== undefined) {
            updateVibration(data.vibration_rms);
        }
        if (sensorStates.sound && (data.sound_db !== undefined || data.sound_freq !== undefined)) {
            updateSound(data.sound_db, data.sound_freq);
        }
    });

    socket.on('vision_update', data => {
        console.log('Received vision data:', data);
        // Only update if vision is enabled
        if (sensorStates.vision) {
            updateAiStatus(data);
        }
    });

    socket.on('audio_ml_update', data => {
        console.log('Received audio ML data:', data);
        updateAudioMLStatus(data);
    });

    socket.on('recording_started', data => {
        console.log('Recording started:', data);
        startRecordingProgress(data.duration);
    });

    // --- UI UPDATE FUNCTIONS ---
    function updateTimestamp(timestamp) {
        const nzTime = new Date(timestamp * 1000).toLocaleString('en-NZ', {
            timeZone: 'Pacific/Auckland',
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        elements.lastUpdated.textContent = `Last Updated: ${nzTime} NZDT/NZST`;
    }

    function updateTemperature(temp) {
        if (temp === undefined || temp === null) return;
        elements.temp.val.textContent = `${temp.toFixed(1)} °C`;
        let status, action, percent;
        
        // Bar range: 28°C to 41°C (optimal 33-36°C ±5°C)
        const TEMP_MIN = 28;
        const TEMP_MAX = 41;
        const TEMP_OPTIMAL_MIN = 33;
        const TEMP_OPTIMAL_MAX = 36;
        
        if (temp < TEMP_OPTIMAL_MIN) { 
            status = '❄️ Too Cold'; 
            action = 'LOW TEMP ALERT: Check food stores (honey/pollen). Install entrance reducer. Consider external insulation.'; 
        } else if (temp > TEMP_OPTIMAL_MAX) { 
            status = '☀️ Too Hot'; 
            action = 'HIGH TEMP ALERT: Open entrance fully. Prop outer cover for ventilation. Provide shade cloth.'; 
        } else { 
            status = '✓ Optimal'; 
            action = 'None required.'; 
        }
        
        // Calculate position on bar (0-100%)
        percent = ((temp - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)) * 100;
        percent = Math.min(100, Math.max(0, percent));
        
        elements.temp.status.textContent = status;
        elements.temp.action.textContent = action;
        elements.temp.bar.style.setProperty('--marker-pos', `${percent}%`);
    }

    function updateHumidity(hum) {
        if (hum === undefined || hum === null) return;
        elements.hum.val.textContent = `${hum.toFixed(1)} %`;
        let status, action, percent;
        
        // Bar range: 40% to 80% (optimal 50-70% ±10%)
        const HUM_MIN = 40;
        const HUM_MAX = 80;
        const HUM_OPTIMAL_MIN = 50;
        const HUM_OPTIMAL_MAX = 70;
        
        if (hum < HUM_OPTIMAL_MIN) { 
            status = '💦 Too Dry'; 
            action = 'LOW HUMIDITY ALERT: Provide water source with landing spots (pebbles). Check syrup concentration.'; 
        } else if (hum > HUM_OPTIMAL_MAX) { 
            status = '💧 Too Wet'; 
            action = 'HIGH HUMIDITY ALERT: Clear all vents. Check roof/bottom board for water trapping. Improve ventilation.'; 
        } else { 
            status = '✓ Optimal'; 
            action = 'None required.'; 
        }
        
        // Calculate position on bar (0-100%)
        percent = ((hum - HUM_MIN) / (HUM_MAX - HUM_MIN)) * 100;
        percent = Math.min(100, Math.max(0, percent));
        
        elements.hum.status.textContent = status;
        elements.hum.action.textContent = action;
        elements.hum.bar.style.setProperty('--marker-pos', `${percent}%`);
    }

    function updateVibration(rms) {
        if (rms === undefined || rms === null) return;
        elements.vib.val.textContent = `${rms.toFixed(4)} RMS`;
        let status, action;
        if (rms > 0.15) {
            status = '🚨 Agitation Alert'; 
            action = 'Hive disturbed or under attack. Check visual feed for pests. Avoid opening hive for 2+ hours.'; 
        } else if (rms < 0.02) {
            status = '🛑 Low Activity Alert';
            action = 'Possible cluster immobilization. Check weather history. Inspect for weakness or pesticide exposure.';
        } else {
            status = '✓ Normal Activity';
            action = 'None required.';
        }
        elements.vib.status.textContent = status;
        elements.vib.action.textContent = action;
        elements.vib.magnitude.style.setProperty('--magnitude', `${Math.min(100, (rms / 0.3) * 100)}%`);
        
        vibrationHistory.push(rms);
        if (vibrationHistory.length > 10) vibrationHistory.shift();
        elements.vib.trend.textContent = generateSparkline(vibrationHistory);
    }

    function updateSound(db, freq) {
        if (db === undefined || db === null) return;
        
        elements.sound.val.textContent = `${db.toFixed(1)} dB`;
        
        // Volume bar (40-70 dB range for normal hive sounds)
        const volumePercent = Math.min(100, Math.max(0, ((db - 40) / 30) * 100));
        elements.sound.volume.style.setProperty('--magnitude', `${volumePercent}%`);
        
        // Frequency bar (200-600 Hz range for bee sounds)
        if (freq !== undefined && freq !== null) {
            const freqPercent = Math.min(100, Math.max(0, ((freq - 200) / 400) * 100));
            elements.sound.frequency.style.setProperty('--magnitude', `${freqPercent}%`);
            
            // Intelligent status and action based on frequency analysis
            if (freq >= 450 && freq <= 600) {
                // Swarming signals (piping/quacking ~500Hz)
                elements.sound.status.textContent = '🏃 SWARM PREDICTION ALERT';
                elements.sound.action.textContent = 'Imminent swarming. Schedule colony split immediately to relieve congestion during swarming season.';
            } else if (freq >= 350 && freq < 450) {
                // Queenless roar (high-pitched distressed sound)
                elements.sound.status.textContent = '👑 QUEEN STATUS ALERT';
                elements.sound.action.textContent = 'Abnormal sound detected. Check brood frames for eggs/larvae. Introduce new queen or frame of young brood if queenless.';
            } else if (freq < 150 && db < 42) {
                // Sudden silence (dramatic drop in acoustic energy)
                elements.sound.status.textContent = '💀 DISTRESS/MORTALITY ALERT';
                elements.sound.action.textContent = 'Sudden silence. Check for local pesticide use. Inspect for dead/paralyzed bees at entrance.';
            } else if (freq >= 200 && freq < 350) {
                // Normal healthy hum (200-300 Hz)
                elements.sound.status.textContent = '✓ Healthy Hum';
                elements.sound.action.textContent = 'None required.';
            } else {
                // Edge cases
                elements.sound.status.textContent = 'Monitoring';
                elements.sound.action.textContent = 'Continue observation.';
            }
        } else {
            // Fallback if frequency is not available
            elements.sound.status.textContent = 'Volume Only';
            elements.sound.action.textContent = 'Frequency analysis unavailable.';
        }
    }

    function updateAiStatus(data) {
        if (data.queen_detected) {
            elements.ai.status.textContent = `QUEEN DETECTED (${(data.confidence * 100).toFixed(0)}%)`;
            elements.ai.status.classList.add('detected');
            
            const nzTime = new Date(data.timestamp * 1000).toLocaleString('en-NZ', {
                timeZone: 'Pacific/Auckland',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
            });
            elements.ai.snapshotTime.textContent = nzTime;
            
            setTimeout(() => elements.ai.status.classList.remove('detected'), 5000);
        } else {
            elements.ai.status.textContent = 'Actively Scanning';
        }
    }

    function updateAudioMLStatus(data) {
        const classification = data.results?.classification || data.classification || 'Unknown';
        const confidence = data.results?.confidence || data.confidence || 0;
        
        // Update display elements
        document.getElementById('audio-classification').textContent = classification;
        document.getElementById('audio-confidence').textContent = `${(confidence * 100).toFixed(1)}%`;
        
        // Update status based on classification
        const statusEl = document.getElementById('audio-ml-status');
        const valueEl = document.getElementById('audio-ml-value');
        
        const classLower = classification.toLowerCase();
        
        if (classLower === 'queen_present' || classLower.includes('queen present')) {
            statusEl.textContent = '👑 Queen Detected';
            valueEl.textContent = 'Queen bee sounds identified';
        } else if (classLower === 'queen_absent' || classLower.includes('queen absent')) {
            statusEl.textContent = '⚠️ Queen Absent';
            valueEl.textContent = 'No queen bee sounds detected';
        } else if (classLower.includes('queenless')) {
            statusEl.textContent = '⚠️ Queenless Colony';
            valueEl.textContent = 'No queen bee sounds detected';
        } else {
            statusEl.textContent = 'Analysis Complete';
            valueEl.textContent = classification;
        }
        
        // Update last analysis time
        const nzTime = new Date().toLocaleString('en-NZ', {
            timeZone: 'Pacific/Auckland',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        document.getElementById('audio-last-analysis').textContent = nzTime;
        
        // Hide progress bar
        document.getElementById('recording-progress').style.display = 'none';
        document.getElementById('record-audio-btn').disabled = false;
    }

    function startRecordingProgress(duration) {
        const progressContainer = document.getElementById('recording-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const recordBtn = document.getElementById('record-audio-btn');
        
        progressContainer.style.display = 'block';
        recordBtn.disabled = true;
        
        let elapsed = 0;
        const interval = setInterval(() => {
            elapsed++;
            const percent = (elapsed / duration) * 100;
            progressFill.style.width = `${percent}%`;
            progressText.textContent = `Recording: ${elapsed}s / ${duration}s`;
            
            if (elapsed >= duration) {
                clearInterval(interval);
                progressText.textContent = 'Processing audio...';
            }
        }, 1000);
    }

    // --- HELPER FUNCTIONS ---
    function generateSparkline(data) {
        const sparklineChars = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
        if (data.length < 2) return '';
        const max = Math.max(...data);
        return data.map(d => sparklineChars[Math.floor((d / (max || 1)) * (sparklineChars.length - 1))]).join('');
    }

    // --- TOGGLE BUTTONS ---
    document.querySelectorAll('.toggle-btn').forEach(button => {
        const sensor = button.dataset.sensor;
        updateButtonAppearance(button, sensor);

        button.addEventListener('click', () => {
            sensorStates[sensor] = !sensorStates[sensor];
            const newState = sensorStates[sensor] ? 'on' : 'off';
            socket.emit('toggle_sensor', { sensor: sensor, state: newState });
            updateButtonAppearance(button, sensor);
        });
    });

    function updateButtonAppearance(button, sensor) {
        const state = sensorStates[sensor];
        button.textContent = `Toggle: ${state ? 'ON' : 'OFF'}`;
        state ? button.classList.remove('off') : button.classList.add('off');
    }

    // --- VIDEO AND AI VISION TOGGLE HANDLERS ---
    const videoToggleBtn = document.getElementById('video-toggle-btn');
    const aiVisionToggleBtn = document.getElementById('ai-vision-toggle-btn');
    const videoFeed = document.getElementById('video-feed');

    if (videoToggleBtn) {
        videoToggleBtn.addEventListener('click', () => {
            const currentState = videoToggleBtn.dataset.state;
            const newState = currentState === 'on' ? 'off' : 'on';
            
            // Send MQTT message
            fetch('/mqtt/publish', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    topic: 'hive/control/video',
                    message: JSON.stringify({state: newState})
                })
            });
            
            // Update button UI
            videoToggleBtn.dataset.state = newState;
            videoToggleBtn.querySelector('.toggle-state').textContent = newState.toUpperCase();
            document.getElementById('video-status-text').textContent = newState.toUpperCase();
            
            // Visual feedback on video feed
            if (videoFeed) {
                if (newState === 'off') {
                    videoFeed.style.opacity = '0.3';
                    videoFeed.style.filter = 'grayscale(100%)';
                } else {
                    videoFeed.style.opacity = '1';
                    videoFeed.style.filter = 'none';
                }
            }
        });
    }

    if (aiVisionToggleBtn) {
        aiVisionToggleBtn.addEventListener('click', () => {
            const currentState = aiVisionToggleBtn.dataset.state;
            const newState = currentState === 'on' ? 'off' : 'on';
            
            // Send MQTT message
            fetch('/mqtt/publish', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    topic: 'hive/control/ai_vision',
                    message: JSON.stringify({state: newState})
                })
            });
            
            // Update button UI
            aiVisionToggleBtn.dataset.state = newState;
            aiVisionToggleBtn.querySelector('.toggle-state').textContent = newState.toUpperCase();
            document.getElementById('ai-vision-status-text').textContent = newState.toUpperCase();
            
            // Change button appearance
            if (newState === 'on') {
                aiVisionToggleBtn.classList.add('ai-active');
            } else {
                aiVisionToggleBtn.classList.remove('ai-active');
            }
        });
    }

    // Listen for status updates from edge-app
    socket.on('video_status', data => {
        if (videoToggleBtn) {
            const status = data.enabled ? 'ON' : 'OFF';
            const state = data.enabled ? 'on' : 'off';
            document.getElementById('video-status-text').textContent = status;
            videoToggleBtn.dataset.state = state;
            videoToggleBtn.querySelector('.toggle-state').textContent = status;
        }
    });

    socket.on('ai_vision_status', data => {
        if (aiVisionToggleBtn) {
            const status = data.enabled ? 'ON' : 'OFF';
            const state = data.enabled ? 'on' : 'off';
            document.getElementById('ai-vision-status-text').textContent = status;
            aiVisionToggleBtn.dataset.state = state;
            aiVisionToggleBtn.querySelector('.toggle-state').textContent = status;
            if (data.enabled) {
                aiVisionToggleBtn.classList.add('ai-active');
            } else {
                aiVisionToggleBtn.classList.remove('ai-active');
            }
        }
    });

    // --- AUDIO WAVEFORM VISUALIZATION ---
    const audioCanvas = document.getElementById('audio-waveform');
    const audioCtx = audioCanvas ? audioCanvas.getContext('2d') : null;
    let waveformData = new Array(100).fill(0); // 100 data points
    let animationFrameId = null;

    function drawWaveform() {
        if (!audioCtx || !audioCanvas) return;

        const width = audioCanvas.width;
        const height = audioCanvas.height;
        const centerY = height / 2;

        // Clear canvas
        audioCtx.fillStyle = '#0f0f1e';
        audioCtx.fillRect(0, 0, width, height);

        // Draw grid lines
        audioCtx.strokeStyle = '#1a1a3e';
        audioCtx.lineWidth = 1;
        for (let i = 0; i <= 4; i++) {
            const y = (height / 4) * i;
            audioCtx.beginPath();
            audioCtx.moveTo(0, y);
            audioCtx.lineTo(width, y);
            audioCtx.stroke();
        }

        // Draw waveform
        audioCtx.strokeStyle = '#00ff88';
        audioCtx.lineWidth = 2;
        audioCtx.beginPath();

        const step = width / waveformData.length;
        for (let i = 0; i < waveformData.length; i++) {
            const x = i * step;
            const amplitude = waveformData[i] * (height / 2) * 0.8; // Scale amplitude
            const y = centerY + amplitude;

            if (i === 0) {
                audioCtx.moveTo(x, y);
            } else {
                audioCtx.lineTo(x, y);
            }
        }
        audioCtx.stroke();

        // Draw center line
        audioCtx.strokeStyle = '#2a2a4e';
        audioCtx.lineWidth = 1;
        audioCtx.beginPath();
        audioCtx.moveTo(0, centerY);
        audioCtx.lineTo(width, centerY);
        audioCtx.stroke();
    }

    function updateAudioLevel(soundDb) {
        // Update waveform data with simulated wave based on sound level
        waveformData.shift();
        const normalizedDb = Math.min(Math.max(soundDb || 0, 0), 100) / 100;
        const waveValue = Math.sin(Date.now() / 100) * normalizedDb;
        waveformData.push(waveValue);

        // Update level bars
        const levelBars = document.querySelectorAll('.level-bar');
        const activeBarCount = Math.floor(normalizedDb * levelBars.length);
        
        levelBars.forEach((bar, index) => {
            if (index < activeBarCount) {
                bar.classList.add('active');
                bar.style.height = `${10 + (index * 9)}%`;
            } else {
                bar.classList.remove('active');
                bar.style.height = '5%';
            }
        });

        // Update dB value
        const dbValue = document.getElementById('audio-db-value');
        if (dbValue && soundDb !== undefined) {
            dbValue.textContent = `${soundDb.toFixed(1)} dB`;
        }

        drawWaveform();
    }

    // Animate waveform continuously
    function animateWaveform() {
        drawWaveform();
        animationFrameId = requestAnimationFrame(animateWaveform);
    }

    // Start animation if canvas exists
    if (audioCanvas) {
        animateWaveform();
    }

    // Update sound visualization when telemetry arrives
    socket.on('telemetry_update', data => {
        if (data.sound_db !== undefined) {
            updateAudioLevel(data.sound_db);
        }
    });

    // --- AUDIO RECORDING BUTTON ---
    document.getElementById('record-audio-btn')?.addEventListener('click', () => {
        console.log('Audio recording button clicked');
        
        const recordBtn = document.getElementById('record-audio-btn');
        const progressDiv = document.getElementById('recording-progress');
        const progressFill = document.getElementById('progress-fill');
        const progressText = document.getElementById('progress-text');
        const statusSpan = document.getElementById('audio-ml-status');
        
        // Disable button and show progress
        recordBtn.disabled = true;
        recordBtn.textContent = '🎙️ Recording...';
        progressDiv.style.display = 'block';
        statusSpan.textContent = 'Recording in progress...';
        
        // Trigger recording via Socket.IO
        socket.emit('trigger_audio_recording', { duration: 60 });
        
        // Animate progress bar
        let elapsed = 0;
        const duration = 60; // seconds
        const interval = setInterval(() => {
            elapsed += 1;
            const percentage = (elapsed / duration) * 100;
            progressFill.style.width = `${percentage}%`;
            progressText.textContent = `Recording: ${elapsed}s / ${duration}s`;
            
            if (elapsed >= duration) {
                clearInterval(interval);
                statusSpan.textContent = 'Processing...';
                progressText.textContent = 'Processing audio...';
            }
        }, 1000);
        
        // Reset after 65 seconds (60s recording + 5s processing buffer)
        setTimeout(() => {
            recordBtn.disabled = false;
            recordBtn.textContent = '🎤 Record 1 Minute & Analyze';
            progressDiv.style.display = 'none';
            progressFill.style.width = '0%';
        }, 65000);
    });

    // --- AUDIO CLASSIFICATION UPDATE ---
    socket.on('audio_classification_update', data => {
        console.log('Received audio classification:', data);
        
        const classificationSpan = document.getElementById('audio-classification');
        const confidenceSpan = document.getElementById('audio-confidence');
        const statusSpan = document.getElementById('audio-ml-status');
        const lastAnalysisSpan = document.getElementById('audio-last-analysis');
        
        if (data.results) {
            const { classification, confidence, status } = data.results;
            
            // Update classification with color coding
            if (classification) {
                classificationSpan.textContent = classification === 'queen_present' 
                    ? 'Queen Present' 
                    : 'Queen Absent';
                classificationSpan.className = 'result-value ' + classification.replace('_', '-');
            }
            
            // Update confidence
            if (confidence !== undefined) {
                confidenceSpan.textContent = `${(confidence * 100).toFixed(1)}%`;
            }
            
            // Update status
            if (status) {
                statusSpan.textContent = status === 'complete' ? 'Analysis Complete' : status;
            }
            
            // Update last analysis time
            lastAnalysisSpan.textContent = 'Just now';
        }
    });
});

