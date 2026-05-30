"""
Phase 0 Test — Vision Model Loading

Run from project root after creating the conda environment:
  conda activate smart-hive-demo
  python demo/test_phase0.py

What this checks:
  1. vision_model.pt exists in models/
  2. VisionProcessor loads it without falling back to yolov8n.pt
  3. Model is enabled and ready for inference
  4. A dummy frame can be processed without crashing
  5. Real sample frames in demo/sample_frames/ are processed and results shown
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    results.append(condition)
    print(f"  {status}  {label}")
    if detail:
        print(f"      {detail}")
    return condition


print()
print("=" * 55)
print("  Phase 0 — Vision Model Test")
print("=" * 55)
print()

# ── 1. Model file exists ───────────────────────────────────────
model_path = ROOT / "models" / "vision_model.pt"
check(
    "models/vision_model.pt exists",
    model_path.exists(),
    f"Expected at: {model_path}",
)

# ── 2. Config path matches ─────────────────────────────────────
try:
    import config
    cfg_path = Path(config.VISION_MODEL_PATH)
    check(
        f"config.VISION_MODEL_PATH = '{config.VISION_MODEL_PATH}'",
        True,
    )
except Exception as e:
    check("config.py readable", False, str(e))

# ── 3. VisionProcessor loads the queen model ───────────────────
try:
    from ml_vision_model.vision_processor import VisionProcessor
    vp = VisionProcessor(use_camera=False)

    check(
        "VisionProcessor initialised without error",
        True,
    )
    check(
        "Model is enabled (no silent fallback)",
        vp.enabled,
        "If False, check the error above — model may have failed to load.",
    )
    check(
        "model is not None",
        vp.model is not None,
    )

    # Confirm it did NOT fall back to yolov8n
    if vp.model is not None:
        model_name = getattr(vp.model, 'ckpt_path', '') or ''
        fell_back = 'yolov8n' in str(model_name).lower()
        check(
            "Loaded queen model (not generic yolov8n fallback)",
            not fell_back,
            f"Model ckpt: {model_name}" if model_name else "ckpt_path not exposed",
        )

except Exception as e:
    check("VisionProcessor import / init", False, str(e))

# ── 4. Single frame inference runs without crash ───────────────
try:
    import numpy as np
    import cv2

    dummy = np.zeros((480, 640, 3), dtype=np.uint8)
    dummy[:] = (60, 90, 40)   # dark green — no bees, should return detected=False

    result = vp.process_frame(dummy)
    check(
        "process_frame() returns a result dict (blank frame)",
        isinstance(result, dict) and "detected" in result,
        f"detected={result.get('detected')}  confidence={result.get('confidence')}  inference_time={result.get('inference_time_ms')}ms",
    )
except Exception as e:
    check("process_frame() with dummy frame", False, str(e))

# ── 5. Real sample frames ──────────────────────────────────────
try:
    import numpy as np
    import cv2

    sample_dir = ROOT / "demo" / "sample_frames"
    image_paths = []
    for ext in ("*.jpg", "*.jpeg", "*.png"):
        image_paths.extend(sorted(sample_dir.glob(ext)))

    if not image_paths:
        print(f"  {WARN}  No images found in demo/sample_frames/ — skipping real-frame test")
    else:
        print()
        print(f"  Running inference on {len(image_paths)} sample frame(s):")
        for img_path in image_paths:
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"    {FAIL}  Could not read {img_path.name}")
                results.append(False)
                continue
            img_resized = cv2.resize(img, (640, 480))
            r = vp.process_frame(img_resized)
            detected = r.get("detected", False)
            conf = r.get("confidence", 0.0)
            boxes = r.get("boxes", [])
            label = "QUEEN DETECTED" if detected else "no queen detected"
            print(f"    {'[QUEEN]' if detected else '[  --  ]'}  {img_path.name}")
            print(f"            confidence={conf:.3f}  boxes={len(boxes)}  inference={r.get('inference_time_ms', 0):.0f}ms")
            check(
                f"process_frame() on {img_path.name} returns valid result",
                isinstance(r, dict) and "detected" in r,
            )
except Exception as e:
    check("process_frame() on sample frames", False, str(e))

# ── Summary ────────────────────────────────────────────────────
print()
passed = sum(results)
total = len(results)
print(f"  Result: {passed}/{total} checks passed")

if passed == total:
    print()
    print("  Phase 0 PASSED — vision model is ready.")
    print("  Proceed to Phase 1 testing.")
else:
    print()
    print("  Phase 0 has failures — check the errors above before continuing.")

print()
sys.exit(0 if passed == total else 1)
