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
        sound: { val: document.getElementById('sound-value'), volume: document.querySelector('#sound-volume'), status: document.getElementById('sound-status'), action: document.getElementById('sound-action') },
        ai: { status: document.getElementById('ai-status-text'), snapshotTime: document.getElementById('ai-snapshot-time') }
    };

    // --- SOCKET.IO LISTENERS ---
    socket.on('connect', () => console.log('Connected to dashboard server!'));

    socket.on('telemetry_update', data => {
        console.log('Received telemetry:', data);
        updateTimestamp(data.timestamp);
        updateTemperature(data.temperature);
        updateHumidity(data.humidity);
        updateVibration(data.vibration_rms);
        updateSound(data.sound_db);
    });

    socket.on('vision_update', data => {
        console.log('Received vision data:', data);
        updateAiStatus(data);
    });

    // --- UI UPDATE FUNCTIONS ---
    function updateTimestamp(timestamp) {
        elements.lastUpdated.textContent = `Last Updated: ${new Date(timestamp * 1000).toLocaleTimeString()}`;
    }

    function updateTemperature(temp) {
        if (temp === undefined || temp === null) return;
        elements.temp.val.textContent = `${temp.toFixed(1)} °C`;
        let status, action, percent;
        if (temp <= 32) { 
            status = 'Too Cold'; 
            action = 'LOW TEMP ALERT: Investigate colony strength or insulation.'; 
            percent = (temp / 32) * 33; 
        } else if (temp >= 37) { 
            status = 'Too Hot'; 
            action = 'HIGH TEMP ALERT: Consider ventilation or shade.'; 
            percent = 67 + ((temp - 37) / 13) * 33; // Adjusted range
        } else { 
            status = 'Optimal'; 
            action = 'None required.'; 
            percent = 33 + ((temp - 32) / 5) * 34; // Adjusted range
        }
        elements.temp.status.textContent = status;
        elements.temp.action.textContent = action;
        elements.temp.bar.style.setProperty('--marker-pos', `${Math.min(100, Math.max(0, percent))}%`);
    }

    function updateHumidity(hum) {
        if (hum === undefined || hum === null) return;
        elements.hum.val.textContent = `${hum.toFixed(1)} %`;
        let status, action, percent;
        if (hum <= 45) { 
            status = 'Too Dry'; 
            action = 'LOW HUMIDITY ALERT: Consider supplemental water.'; 
            percent = (hum / 45) * 33; 
        } else if (hum >= 75) { 
            status = 'Too Wet'; 
            action = 'HIGH HUMIDITY ALERT: Check for moisture and poor ventilation.'; 
            percent = 67 + ((hum - 75) / 25) * 33; // Adjusted range
        } else { 
            status = 'Optimal'; 
            action = 'None required.'; 
            percent = 33 + ((hum - 45) / 30) * 34; // Adjusted range
        }
        elements.hum.status.textContent = status;
        elements.hum.action.textContent = action;
        elements.hum.bar.style.setProperty('--marker-pos', `${Math.min(100, Math.max(0, percent))}%`);
    }

    function updateVibration(rms) {
        if (rms === undefined || rms === null) return;
        elements.vib.val.textContent = `${rms.toFixed(4)} RMS`;
        let status, action;
        if (rms > 0.15) { // Threshold for 'Agitated'
            status = 'Agitation Alert'; 
            action = 'Hive disturbed or under attack.'; 
        } else if (rms < 0.02) { // Threshold for 'Low Activity'
            status = 'Low Activity Alert';
            action = 'Possible cluster immobilization or weakness.';
        } else {
            status = 'Normal Activity';
            action = 'None required.';
        }
        elements.vib.status.textContent = status;
        elements.vib.action.textContent = action;
        elements.vib.magnitude.style.setProperty('--magnitude', `${Math.min(100, (rms / 0.3) * 100)}%`);
        
        vibrationHistory.push(rms);
        if (vibrationHistory.length > 10) vibrationHistory.shift();
        elements.vib.trend.textContent = generateSparkline(vibrationHistory);
    }

    function updateSound(db) {
        if (db === undefined || db === null) return;
        elements.sound.val.textContent = `${db.toFixed(1)} dB`;
        // NOTE: This is a placeholder. Real implementation requires frequency analysis.
        elements.sound.status.textContent = 'Queen Status Alert'; 
        elements.sound.action.textContent = 'Abnormal sound detected. Schedule inspection.';
        elements.sound.volume.style.setProperty('--magnitude', `${Math.min(100, ((db + 60) / 80) * 100)}%`); // Offset for better visualization of dB
    }

    function updateAiStatus(data) {
        if (data.queen_detected) {
            elements.ai.status.textContent = `QUEEN DETECTED (${(data.confidence * 100).toFixed(0)}%)`;
            elements.ai.status.classList.add('detected');
            elements.ai.snapshotTime.textContent = new Date(data.timestamp * 1000).toLocaleTimeString();
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
