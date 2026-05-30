"""
Phase 1 Test — Simulator + Audio Demo Pipeline

Tests the core demo components in isolation (no MQTT broker, no microphone,
no Docker required).  Run from the project root:

  conda activate smart-hive-demo
  python demo/test_phase1.py

What is checked:
  Simulator
    1. BeehiveSimulator._telemetry() returns all expected keys with sane values
    2. Temperature is within beehive thermoregulation range (28–42 °C)
    3. Humidity is clamped to 55–80 %
    4. _placeholder_frame() produces a valid H×W×3 array encodable as JPEG

  Audio pipeline
    5. models/audio_model.pkl exists
    6. AudioProcessor loads the model without error
    7. extract_features() returns the right shape on synthetic audio
    8. classify() returns a dict with 'classification' and 'confidence' keys
    9. classification is one of the expected labels
   10. The full synthetic demo cycle (generate → extract → classify) runs end-to-end
"""

import sys
import os
import math
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASS = "[PASS]"
FAIL = "[FAIL]"

results = []


def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append(condition)
    print(f"  {status}  {label}")
    if detail:
        print(f"        {detail}")
    return condition


print()
print("=" * 60)
print("  Phase 1 — Simulator + Audio Demo Pipeline Test")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────
# Block A: Simulator data generation (no MQTT connection needed)
# ─────────────────────────────────────────────────────────────────
print()
print("  [Simulator]")

try:
    # Patch MQTT so BeehiveSimulator.__init__ doesn't try to connect
    import unittest.mock as mock
    import paho.mqtt.client as _real_mqtt

    with mock.patch.object(_real_mqtt.Client, "connect", return_value=None), \
         mock.patch.object(_real_mqtt.Client, "loop_start", return_value=None), \
         mock.patch.object(_real_mqtt.Client, "subscribe", return_value=(0, 1)):

        sys.path.insert(0, str(ROOT / "demo"))
        from simulator import BeehiveSimulator
        sim = BeehiveSimulator()

    # ── Check 1: telemetry keys ────────────────────────────────────
    data = sim._telemetry()
    expected_keys = {"timestamp", "temperature", "humidity", "vibration", "sound_db", "source"}
    check(
        "telemetry() returns all expected keys",
        expected_keys.issubset(data.keys()),
        f"keys: {set(data.keys())}",
    )

    # ── Check 2: temperature in beehive range ─────────────────────
    temp = data["temperature"]
    check(
        f"temperature {temp} °C is within beehive range (28–42 °C)",
        28.0 <= temp <= 42.0,
        f"got {temp}",
    )

    # ── Check 3: humidity clamped ─────────────────────────────────
    hum = data["humidity"]
    check(
        f"humidity {hum} % is clamped to 55–80 %",
        55.0 <= hum <= 80.0,
        f"got {hum}",
    )

    # ── Check 4: placeholder frame encodes to JPEG ────────────────
    import numpy as np
    import cv2

    frame = sim._placeholder_frame()
    shape_ok = (
        isinstance(frame, np.ndarray)
        and frame.ndim == 3
        and frame.shape[2] == 3
    )
    check(
        "placeholder_frame() returns H×W×3 numpy array",
        shape_ok,
        f"shape: {frame.shape if isinstance(frame, np.ndarray) else type(frame)}",
    )

    ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    check(
        "placeholder_frame() encodes to JPEG without error",
        ok and len(buf) > 0,
        f"JPEG bytes: {len(buf)}",
    )

except Exception as exc:
    check("Simulator block", False, str(exc))
    import traceback; traceback.print_exc()

# ─────────────────────────────────────────────────────────────────
# Block B: Audio demo pipeline (no microphone, no MQTT)
# ─────────────────────────────────────────────────────────────────
print()
print("  [Audio]")

audio_model_path = ROOT / "models" / "audio_model.pkl"

# ── Check 5: model file exists ────────────────────────────────────
check(
    "models/audio_model.pkl exists",
    audio_model_path.exists(),
    f"Expected at: {audio_model_path}",
)

try:
    from ml_audio_model.audio_processor import AudioProcessor

    ap = AudioProcessor(str(audio_model_path))

    # ── Check 6: model loaded ─────────────────────────────────────
    check(
        "AudioProcessor loaded model without error",
        ap.model is not None,
        "If False, models/audio_model.pkl may be missing or corrupted.",
    )

    # ── Check 7: feature extraction ───────────────────────────────
    sr = ap.sample_rate
    t = np.linspace(0, 3.0, int(sr * 3.0))
    freq = 300.0
    synthetic = (
        0.4 * np.sin(2 * math.pi * freq * t)
        + 0.2 * np.sin(2 * math.pi * freq * 2 * t)
        + 0.1 * np.random.normal(0, 0.1, len(t))
    ).astype(np.float32)
    synthetic /= np.max(np.abs(synthetic))

    features = ap.extract_features(synthetic)
    check(
        "extract_features() returns a 2-D feature array",
        features is not None and features.ndim == 2,
        f"shape: {features.shape if features is not None else None}",
    )

    # ── Check 8: classify returns expected keys ───────────────────
    if features is not None:
        result = ap.classify(features)
        check(
            "classify() returns dict with 'classification' and 'confidence'",
            isinstance(result, dict)
            and "classification" in result
            and "confidence" in result,
            f"result: {result}",
        )

        # ── Check 9: label is valid ───────────────────────────────
        valid_labels = {"queen_present", "queen_absent", "error"}
        check(
            f"classification label '{result.get('classification')}' is valid",
            result.get("classification") in valid_labels,
            f"valid labels: {valid_labels}",
        )
    else:
        check("classify() — skipped (features were None)", False)
        check("classification label — skipped (features were None)", False)

    # ── Check 10: full synthetic demo cycle ───────────────────────
    try:
        hour = 12.0  # solar noon — high activity
        activity = max(0.1, math.sin((hour - 6) * math.pi / 12))
        freq2 = 250 + activity * 150
        t2 = np.linspace(0, 3.0, int(sr * 3.0))
        audio2 = (
            0.4 * np.sin(2 * math.pi * freq2 * t2)
            + 0.2 * np.sin(2 * math.pi * freq2 * 2 * t2)
            + 0.1 * np.sin(2 * math.pi * freq2 * 3 * t2)
            + 0.1 * np.random.normal(0, 0.1, len(t2))
        ).astype(np.float32)
        audio2 /= np.max(np.abs(audio2))

        feats2 = ap.extract_features(audio2)
        result2 = ap.classify(feats2) if feats2 is not None else None
        cycle_ok = (
            result2 is not None
            and result2.get("classification") in {"queen_present", "queen_absent"}
            and 0.0 <= result2.get("confidence", -1) <= 1.0
        )
        check(
            "Full synthetic demo cycle (generate → extract → classify) runs end-to-end",
            cycle_ok,
            f"result: {result2}",
        )
    except Exception as exc2:
        check("Full synthetic demo cycle", False, str(exc2))

except Exception as exc:
    check("AudioProcessor import / init", False, str(exc))
    import traceback; traceback.print_exc()

# ─────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────
print()
passed = sum(results)
total = len(results)
print(f"  Result: {passed}/{total} checks passed")

if passed == total:
    print()
    print("  Phase 1 PASSED — simulator and audio pipeline are ready.")
    print("  Proceed to Phase 2 (dashboard auth) or run the full demo stack.")
else:
    failed = [i + 1 for i, ok in enumerate(results) if not ok]
    print()
    print(f"  Phase 1 has failures — check items: {failed}")

print()
sys.exit(0 if passed == total else 1)
