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
        elements.temp.val.textContent = `${temp.toFixed(1)} °C`;
        let status, action, percent;
        if (temp < 32) { status = 'Too Cold'; action = 'Check for drafts or insulation.'; percent = (temp / 32) * 33; }
        else if (temp > 36) { status = 'Too Hot'; action = 'Consider ventilation or shade.'; percent = 67 + ((temp - 36) / 14) * 33; }
        else { status = 'Optimal'; action = 'None required.'; percent = 33 + ((temp - 32) / 4) * 34; }
        elements.temp.status.textContent = status;
        elements.temp.action.textContent = action;
        elements.temp.bar.style.setProperty('--marker-pos', `${Math.min(100, Math.max(0, percent))}%`);
    }

    function updateHumidity(hum) {
        elements.hum.val.textContent = `${hum.toFixed(1)} %`;
        let status, action, percent;
        if (hum < 50) { status = 'Too Dry'; action = 'Check water source.'; percent = (hum / 50) * 33; }
        else if (hum > 70) { status = 'Too Wet'; action = 'Increase ventilation.'; percent = 67 + ((hum - 70) / 30) * 33; }
        else { status = 'Optimal'; action = 'None required.'; percent = 33 + ((hum - 50) / 20) * 34; }
        elements.hum.status.textContent = status;
        elements.hum.action.textContent = action;
        elements.hum.bar.style.setProperty('--marker-pos', `${Math.min(100, Math.max(0, percent))}%`);
    }

    function updateVibration(rms) {
        elements.vib.val.textContent = `${rms.toFixed(4)} RMS`;
        let status = 'Normal Activity', action = 'None required.';
        if (rms > 0.2) { status = 'High Activity'; action = 'Possible disturbance or swarm prep.'; }
        elements.vib.status.textContent = status;
        elements.vib.action.textContent = action;
        elements.vib.magnitude.style.setProperty('--magnitude', `${Math.min(100, (rms / 0.3) * 100)}%`);
        
        // Update trend sparkline
        vibrationHistory.push(rms);
        if (vibrationHistory.length > 10) vibrationHistory.shift();
        elements.vib.trend.textContent = generateSparkline(vibrationHistory);
    }

    function updateSound(db) {
        elements.sound.val.textContent = `${db.toFixed(1)} dB`;
        elements.sound.status.textContent = 'Healthy Hum'; // Placeholder
        elements.sound.action.textContent = 'None required.'; // Placeholder
        elements.sound.volume.style.setProperty('--magnitude', `${Math.min(100, (db / 80) * 100)}%`);
        // NOTE: Frequency bar is not updated as this data is not available from the sensor.
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
        return data.map(d => sparklineChars[Math.floor((d / max) * (sparklineChars.length - 1))]).join('');
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