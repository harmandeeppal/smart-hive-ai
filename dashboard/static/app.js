document.addEventListener('DOMContentLoaded', () => {
    // Connect to the Socket.IO server
    const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    socket.on('connect', () => {
        console.log('Connected to dashboard server!');
    });

    // Helper function to create a gauge chart
    function createGauge(ctx, label, color, max) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [label, ''],
                datasets: [{
                    data: [0, max],
                    backgroundColor: [color, '#e9ecef'],
                    borderColor: [color, '#e9ecef'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                circumference: 180,
                rotation: -90,
                cutout: '80%',
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false }
                }
            }
        });
    }

    // Create gauges for each sensor
    const tempGauge = createGauge(document.getElementById('temp-gauge').getContext('2d'), 'Temp', '#ff6384', 50);
    const humGauge = createGauge(document.getElementById('hum-gauge').getContext('2d'), 'Hum', '#36a2eb', 100);
    const vibGauge = createGauge(document.getElementById('vib-gauge').getContext('2d'), 'Vib', '#cc65fe', 1);
    const soundGauge = createGauge(document.getElementById('sound-gauge').getContext('2d'), 'Sound', '#ffce56', 100);

    // Function to update a gauge's value
    function updateGauge(gauge, value) {
        gauge.data.datasets[0].data[0] = value;
        gauge.data.datasets[0].data[1] = gauge.config.data.datasets[0].data[1] - value; // Update the 'empty' part
        gauge.update('none'); // 'none' for no animation
    }

    // Listen for telemetry updates from the server
    socket.on('telemetry_update', function(data) {
        console.log('Received telemetry:', data);
        document.getElementById('temp-value').textContent = `${data.temperature.toFixed(1)} °C`;
        document.getElementById('hum-value').textContent = `${data.humidity.toFixed(1)} %`;
        document.getElementById('vib-value').textContent = data.vibration_rms.toFixed(4);
        document.getElementById('sound-value').textContent = `${data.sound_db.toFixed(1)} dB`;

        // Update the gauges
        updateGauge(tempGauge, data.temperature);
        updateGauge(humGauge, data.humidity);
        updateGauge(vibGauge, data.vibration_rms);
        updateGauge(soundGauge, data.sound_db);
    });

    // Listen for vision updates
    socket.on('vision_update', function(data) {
        console.log('Received vision data:', data);
        const visionStatus = document.getElementById('vision-status');
        if (data.queen_detected) {
            visionStatus.textContent = `QUEEN DETECTED! (Confidence: ${data.confidence * 100}%)`;
            visionStatus.classList.add('detected');
            // Remove the highlight after a few seconds
            setTimeout(() => visionStatus.classList.remove('detected'), 5000);
        }
    });
    
    // Add event listeners for toggle buttons
    document.querySelectorAll('.toggle-btn').forEach(button => {
        button.addEventListener('click', () => {
            const sensor = button.dataset.sensor;
            // This is a simple toggle; a real app might track state
            console.log(`Toggling sensor: ${sensor}`);
            socket.emit('toggle_sensor', { sensor: sensor, state: 'off' }); // Example command
        });
    });
});
