"""Motion dog detector: MOG2 first-frame warmup + static-scene regression."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from app.dog_detect import MotionDogDetector


def _gradient(h: int = 240, w: int = 320) -> np.ndarray:
    col = np.tile(np.linspace(80, 160, w, dtype=np.uint8), (h, 1))
    return np.dstack([col] * 3)


def test_static_scene_reports_no_dog() -> None:
    det = MotionDogDetector()
    frame = _gradient()
    # Feed the same static frame several times; nothing moves, so no bbox.
    for _ in range(5):
        bbox = det.detect(frame)
    assert bbox is None


def test_moving_object_after_warmup_detected() -> None:
    det = MotionDogDetector()
    h, w = 240, 320
    base = np.full((h, w, 3), 120, np.uint8)
    # First frame warms up MOG2 (all-foreground mask must be ignored).
    assert det.detect(base) is None
    # Second static frame: still nothing moving.
    assert det.detect(base) is None
    # Introduce a bright block = motion.
    moving = base.copy()
    moving[80:160, 120:200] = 255
    bbox = det.detect(moving)
    assert bbox is not None
    assert bbox.w > 0.1
