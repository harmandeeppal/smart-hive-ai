# Audio Service Guide

This guide explains how the audio service records hive activity, extracts features, performs machine-learning inference, and surfaces results in the dashboard. Use it to configure thresholds, understand logs, and troubleshoot problems.

## Architecture Overview
1. The dashboard (or another MQTT publisher) sends a control message such as `{"command": "record_and_classify", "duration_sec": 60}` on `hive/audio/control`.
2. The audio service records raw PCM audio from the configured microphone, automatically detecting a supported sample rate and resampling to 22 050 Hz.
3. The recording is split into overlapping windows (default: 1.0 s window with 0.5 s hop).
4. Each window is converted into MFCC-based feature statistics that match the training pipeline.
5. A scikit-learn pipeline scales, selects, and classifies the features, returning a probability that the queen is present.
6. Window-level probabilities are aggregated to produce a single result that is published on `hive/audio/classification` and displayed in the dashboard.

## Recording and Resampling
- The service probes a list of sample rates (22 050, 44 100, 48 000, 16 000 Hz). If the preferred rate is unsupported, it falls back without failing the recording.
- PortAudio (via `sounddevice`) handles capture. Typical errors such as `PaErrorCode -9997` (invalid sample rate) or `PaErrorCode -9996` (device unavailable) are reported with clear log messages.
- Multi-channel audio is converted to mono before resampling with `librosa.resample` to ensure compatibility with the trained model.

## Windowing and Feature Extraction
- `AUDIO_WINDOW_SECONDS` defines the window length; `AUDIO_HOP_SECONDS` controls overlap. These values must remain aligned with the training configuration.
- Each window produces 13 MFCC coefficients and eight statistics (mean, standard deviation, min, max, median, skew, kurtosis, energy), leading to a 104‑element vector.
- The persisted scikit-learn pipeline applies the same feature selection mask and scaling used during training, so feature ordering must remain unchanged.

## Classification and Aggregation
- The production model is a Random Forest classifier saved as `models/audio_model.pkl`.
- Supported aggregation methods:
  - `max_proba` (default): returns the highest window probability.
  - `mean_proba`: averages probabilities across windows.
- Add custom aggregation by extending `ml_audio_model/audio_processor.py`.
- Published MQTT payloads include the label, confidence, aggregation method, and timestamp so you can audit decisions.

## Configuration Reference (`config.py`)
| Setting | Description | Default |
| --- | --- | --- |
| `AUDIO_RECORD_DURATION_SEC` | Recording duration requested by dashboard actions. | `30` |
| `AUDIO_WINDOW_SECONDS` | Length of each inference window (seconds). | `1.0` |
| `AUDIO_HOP_SECONDS` | Step between windows (seconds). | `0.5` |
| `AUDIO_CONFIDENCE_THRESHOLD` | Minimum probability required to emit `queen_present`. | `0.6` |
| `AUDIO_AGGREGATION_METHOD` | Combines window probabilities (`max_proba`, `mean_proba`, …). | `max_proba` |
| `AUDIO_SAVE_RECORDINGS` | Persist WAV files for offline analysis. | `False` |
| `AUDIO_RECORDINGS_DIR` | Directory for saved recordings when enabled. | `audio_recordings/` |

After modifying configuration values, rebuild and restart the audio container:

```bash
docker compose build --no-cache smart-hive-audio
docker compose up -d smart-hive-audio
```

### Confidence Threshold Tuning
- `0.5` – maximises detections for exploratory analysis; expect more false positives.
- `0.6` – balanced default for production.
- `0.7` – conservative setting for alert-driven workflows.
- `0.8` – very conservative; only extremely confident detections pass.

Use the logs to monitor how often predictions fall below your threshold:

```bash
docker logs smart-hive-audio --tail 100 | grep "Windowed classification"
```

### Dashboard Behaviour
- Confidence-aware status indicators show green for confident `queen_present`, red for confident `queen_absent`, and amber for low-confidence outcomes.
- Audio waveform rendering uses multiple sine components and a realistic 40–90 dB range so the UI reflects small variations instead of a flat line.
- Sound level bars apply a sensitivity multiplier (`1.5` by default) to react to moderate hive activity.

## Troubleshooting Checklist
1. **Invalid sample rate** – ensure the microphone supports at least one of the probed rates; the service falls back automatically but still logs warnings.
2. **No input device found** – confirm the device appears in `lsusb`, `arecord -l`, and within the container via `sounddevice.query_devices()`. Add the `pi` user to the `audio` group and reboot if necessary.
3. **Low confidence** – lengthen recordings, reduce ambient noise, or adjust `AUDIO_CONFIDENCE_THRESHOLD`. Review the confidence history to avoid masking genuine issues.
4. **Model not found / load error** – verify that `models/audio_model.pkl` exists in the container and matches the expected scikit-learn version. Re-export the model if the pipeline changes.
5. **Need raw audio** – enable `AUDIO_SAVE_RECORDINGS`, rebuild, and retrieve WAV files from the configured directory for offline analysis.

## Useful Commands
```bash
# Follow logs with timestamps
docker logs -f --timestamps smart-hive-audio

# Inspect audio devices from inside the container
docker exec -it smart-hive-audio python -c "import sounddevice as sd; print(sd.query_devices())"

# Monitor MQTT results
mosquitto_sub -h localhost -t 'hive/audio/#' -v
```

Collect the commands above (and resulting output) when escalating issues—having device listings and recent logs drastically shortens debugging time.
