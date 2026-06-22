"""Scene-level motion and arousal proxies."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SceneSignals:
    motion_level: float
    brightness: float
    contrast: float
    tags: list[str]


def classify_scene(frame_bgr: np.ndarray, motion_level: float = 0.0) -> SceneSignals:
    gray = np.mean(frame_bgr, axis=2)
    brightness = float(np.mean(gray) / 255.0)
    contrast = float(np.std(gray) / 128.0)
    tags: list[str] = []
    if motion_level > 0.08:
        tags.append("motion")
    if brightness < 0.25:
        tags.append("low_light")
    return SceneSignals(motion_level=motion_level, brightness=brightness, contrast=contrast, tags=tags)
