"""
Generate a synthetic 1-minute beehive demo video.
Output: demo/sample_video/beehive_demo.mp4

Renders an animated honeycomb with moving worker bees and a queen bee.

Run once before starting the demo:
  conda activate smart-hive-demo
  python demo/generate_sample_video.py
"""

import math
import sys
import numpy as np
import cv2
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "demo" / "sample_video"
OUTPUT_FILE = OUTPUT_DIR / "beehive_demo.mp4"

WIDTH, HEIGHT = 640, 480
FPS = 15
DURATION = 60  # seconds
TOTAL_FRAMES = FPS * DURATION

# BGR colours
BG = (18, 28, 45)
HEX_LINE = (40, 130, 210)
HEX_FILL = (22, 55, 95)
WORKER_BODY = (0, 165, 255)       # amber
WORKER_STRIPE = (0, 60, 120)
QUEEN_BODY = (60, 80, 220)        # warm red
QUEEN_STRIPE = (20, 30, 140)
TEXT_COL = (200, 220, 240)
DIM_COL = (100, 110, 125)


# ── Honeycomb geometry ────────────────────────────────────────────────────────

HEX_SIZE = 28


def hex_corners(cx, cy, size):
    return [
        (int(cx + size * math.cos(math.radians(60 * i - 30))),
         int(cy + size * math.sin(math.radians(60 * i - 30))))
        for i in range(6)
    ]


def build_honeycomb():
    """Return list of (cx, cy) for all visible hex cells."""
    cells = []
    w = size = HEX_SIZE
    h_step = int(size * math.sqrt(3))
    v_step = int(size * 1.5)
    for row in range(-1, HEIGHT // v_step + 2):
        for col in range(-1, WIDTH // (h_step) + 2):
            cx = col * h_step + (h_step // 2 if row % 2 else 0)
            cy = row * v_step
            cells.append((cx, cy))
    return cells


CELLS = build_honeycomb()


def draw_honeycomb(canvas):
    for cx, cy in CELLS:
        pts = np.array(hex_corners(cx, cy, HEX_SIZE - 2), dtype=np.int32)
        cv2.fillPoly(canvas, [pts], HEX_FILL)
        cv2.polylines(canvas, [pts], True, HEX_LINE, 1)


# ── Bee simulation ────────────────────────────────────────────────────────────

class Bee:
    def __init__(self, x, y, size, speed, is_queen=False):
        self.x = float(x)
        self.y = float(y)
        self.size = size
        self.speed = speed
        self.is_queen = is_queen
        self.angle = np.random.uniform(0, 2 * math.pi)
        self.turn_rate = np.random.uniform(0.04, 0.12)
        self.body_col = QUEEN_BODY if is_queen else WORKER_BODY
        self.stripe_col = QUEEN_STRIPE if is_queen else WORKER_STRIPE

    def step(self, rng):
        # Smooth random walk
        self.angle += rng.uniform(-self.turn_rate, self.turn_rate)
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        # Soft boundary bounce
        margin = 30
        if self.x < margin:
            self.angle = rng.uniform(-math.pi / 4, math.pi / 4)
            self.x = max(self.x, margin)
        if self.x > WIDTH - margin:
            self.angle = rng.uniform(3 * math.pi / 4, 5 * math.pi / 4)
            self.x = min(self.x, WIDTH - margin)
        if self.y < margin:
            self.angle = rng.uniform(math.pi / 4, 3 * math.pi / 4)
            self.y = max(self.y, margin)
        if self.y > HEIGHT - margin:
            self.angle = rng.uniform(-3 * math.pi / 4, -math.pi / 4)
            self.y = min(self.y, HEIGHT - margin)

    def draw(self, canvas):
        cx, cy = int(self.x), int(self.y)
        s = self.size
        # Body (ellipse)
        cv2.ellipse(canvas, (cx, cy), (s, int(s * 0.65)),
                    int(math.degrees(self.angle)), 0, 360, self.body_col, -1)
        # Stripes
        for i in range(1, 3):
            sx = int(cx - s * 0.5 + i * s * 0.35)
            sy = cy
            cv2.line(canvas, (sx - 1, sy - int(s * 0.55)),
                     (sx - 1, sy + int(s * 0.55)), self.stripe_col, max(1, s // 6))
        # Head
        hx = int(cx + s * math.cos(self.angle))
        hy = int(cy + s * math.sin(self.angle))
        cv2.circle(canvas, (hx, hy), max(2, s // 3), self.body_col, -1)
        # Wings
        for sign in (-1, 1):
            wx = int(cx - s * 0.3 * math.cos(self.angle) + sign * s * 0.9 * math.sin(self.angle))
            wy = int(cy - s * 0.3 * math.sin(self.angle) - sign * s * 0.9 * math.cos(self.angle))
            cv2.ellipse(canvas, (wx, wy), (s, int(s * 0.35)),
                        int(math.degrees(self.angle)) + sign * 30,
                        0, 360, (200, 220, 240), 1)
        # Queen marker
        if self.is_queen:
            cv2.circle(canvas, (cx, cy), s + 3, (100, 100, 255), 1)


def init_bees(rng):
    bees = []
    for _ in range(18):
        bees.append(Bee(
            rng.uniform(60, WIDTH - 60),
            rng.uniform(60, HEIGHT - 60),
            size=rng.integers(5, 9),
            speed=rng.uniform(0.8, 1.6),
        ))
    # One queen
    bees.append(Bee(WIDTH // 2, HEIGHT // 2, size=11, speed=0.5, is_queen=True))
    return bees


# ── Render ────────────────────────────────────────────────────────────────────

def render_frame(bees, frame_no, rng):
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    canvas[:] = BG

    draw_honeycomb(canvas)

    # Subtle vignette
    for bee in sorted(bees, key=lambda b: b.is_queen):
        bee.draw(canvas)
        bee.step(rng)

    # Overlay: title + timestamp
    t_str = (datetime.now() + timedelta(seconds=frame_no / FPS)).strftime("%H:%M:%S")
    cv2.putText(canvas, "Smart Hive AI  |  Demo Mode",
                (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, TEXT_COL, 1)
    cv2.putText(canvas, t_str,
                (12, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.45, DIM_COL, 1)

    # Frame counter (bottom right)
    cv2.putText(canvas, f"frame {frame_no:04d}",
                (WIDTH - 110, HEIGHT - 8), cv2.FONT_HERSHEY_SIMPLEX,
                0.35, DIM_COL, 1)

    return canvas


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(OUTPUT_FILE), fourcc, FPS, (WIDTH, HEIGHT))

    if not writer.isOpened():
        print("ERROR: could not open VideoWriter — check that opencv-python is installed")
        sys.exit(1)

    rng = np.random.default_rng(42)
    bees = init_bees(rng)

    print(f"Rendering {TOTAL_FRAMES} frames ({DURATION}s at {FPS} fps)...")
    for i in range(TOTAL_FRAMES):
        frame = render_frame(bees, i, rng)
        writer.write(frame)
        if (i + 1) % (FPS * 10) == 0:
            print(f"  {(i + 1) // FPS}s / {DURATION}s")

    writer.release()
    size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"Saved: {OUTPUT_FILE}  ({size_mb:.1f} MB)")
    print("Done — restart the demo to use the video.")


if __name__ == "__main__":
    main()
