"""Canonical perception feature vector layout (shared by train + runtime)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

try:
    from .modality_spec import MODALITY_NAMES, modality_vectorize
except ImportError:
    _mod_path = Path(__file__).with_name("modality_spec.py")
    _spec = importlib.util.spec_from_file_location("modality_spec", _mod_path)
    if _spec is None or _spec.loader is None:
        raise
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    MODALITY_NAMES = _mod.MODALITY_NAMES
    modality_vectorize = _mod.modality_vectorize

BASE_FEATURE_NAMES: list[str] = [
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

FEATURE_NAMES: list[str] = BASE_FEATURE_NAMES + MODALITY_NAMES

FEATURE_DIM = len(FEATURE_NAMES)
SEQUENCE_LEN = 15


def vectorize(features: dict) -> list[float]:
    base = [float(features.get(name, 0.0)) for name in BASE_FEATURE_NAMES]
    return base + modality_vectorize(features)
