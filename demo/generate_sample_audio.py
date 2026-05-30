"""
Generate a 5-minute bee colony audio sample for demo playback.
Output: demo/sample_audio/bee_colony_demo.wav

Run once before starting the demo:
  conda activate smart-hive-demo
  python demo/generate_sample_audio.py
"""

import sys
import math
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "demo" / "sample_audio"
OUTPUT_FILE = OUTPUT_DIR / "bee_colony_demo.wav"

SAMPLE_RATE = 22050
DURATION = 300  # 5 minutes


def generate(duration: float, sr: int) -> np.ndarray:
    n = int(sr * duration)
    t = np.linspace(0, duration, n, dtype=np.float32)

    # Slow activity envelope — simulates forager return rhythm (~0.05 Hz)
    activity = 0.55 + 0.35 * np.sin(2 * math.pi * 0.05 * t + 0.8)

    # Base colony hum: fundamental ~230 Hz with slow pitch drift
    base_freq = 230 + 18 * np.sin(2 * math.pi * 0.008 * t)

    audio = np.zeros(n, dtype=np.float32)

    # Fundamental + harmonics
    for harmonic, amp in [(1, 0.40), (2, 0.22), (3, 0.13), (4, 0.07), (5, 0.03)]:
        phase = np.random.uniform(0, 2 * math.pi)
        audio += amp * activity * np.sin(2 * math.pi * base_freq * harmonic * t + phase)

    # Individual bee bursts — random short-duration contributions
    rng = np.random.default_rng(42)
    for _ in range(25):
        f = rng.uniform(180, 420)
        start = rng.uniform(0, duration - 6)
        end = start + rng.uniform(1.5, 6.0)
        mask = (t >= start) & (t <= end)
        env = np.sin(math.pi * (t[mask] - start) / (end - start))  # fade in/out
        audio[mask] += 0.035 * rng.uniform(0.4, 1.0) * env * np.sin(2 * math.pi * f * t[mask])

    # Wing-beat amplitude modulation (~1.3 Hz)
    am = 0.88 + 0.12 * np.sin(2 * math.pi * 1.3 * t)
    audio *= am

    # Microphone noise floor
    audio += 0.018 * rng.standard_normal(n).astype(np.float32)

    # Normalise with headroom
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.88

    return audio


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating {DURATION // 60}-minute bee colony audio at {SAMPLE_RATE} Hz...")
    audio = generate(DURATION, SAMPLE_RATE)

    try:
        import soundfile as sf
        sf.write(str(OUTPUT_FILE), audio, SAMPLE_RATE, subtype="PCM_16")
    except ImportError:
        import scipy.io.wavfile as wav
        wav.write(str(OUTPUT_FILE), SAMPLE_RATE, (audio * 32767).astype(np.int16))

    size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"Saved: {OUTPUT_FILE}  ({size_mb:.1f} MB)")
    print("Done — restart the demo to use the audio file.")


if __name__ == "__main__":
    main()
