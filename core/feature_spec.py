"""Canonical perception feature vector layout (shared by train + runtime)."""
from __future__ import annotations

FEATURE_NAMES: list[str] = [
    "dog_present",
    "bbox_cx",
    "bbox_cy",
    "bbox_w",
    "bbox_h",
    "motion",
    "velocity_x",
    "velocity_y",
    "gaze_door",
    "gaze_toy",
    "gaze_bowl",
    "gaze_center",
    "edge_left",
    "edge_right",
    "edge_top",
    "edge_bottom",
    "brightness",
    "contrast",
    "aspect_ratio",
    "arousal_proxy",
]

FEATURE_DIM = len(FEATURE_NAMES)
SEQUENCE_LEN = 15


def vectorize(features: dict) -> list[float]:
    return [float(features.get(name, 0.0)) for name in FEATURE_NAMES]
