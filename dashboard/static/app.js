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
});
