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
    "pose_head_y",
    "pose_head_gaze_x",
    "pose_body_stretch",
    "pose_play_bow",
    "n_dogs",
    "track_stability",
    "tau_door",
    "tau_toy",
    "tau_bowl",
    "closing_door",
    "closing_toy",
    "closing_bowl",
    "heading_door",
    "heading_toy",
    "heading_bowl",
    # docs/ADVANCED_MATH.md §1 — tail biomechanics (beyond wag rate)
    "tail_wag_rate",
    "tail_amplitude",
    "tail_velocity",
    "tail_rhythmicity",
    "tail_height",
    "tail_asymmetry",
    "tail_lyapunov",
    # docs/ADVANCED_MATH.md §2/§5 — DogFACS facial action units, ears, mouth
    "facs_au_intensity",
    "ear_angle",
    "sclera_exposure",
    "blink_rate",
    "mouth_tension",
    # docs/ADVANCED_MATH.md §3 — head pitch/yaw/roll-cock variance
    "head_pitch",
    "head_yaw",
    "head_roll_var",
    # docs/ADVANCED_MATH.md §6 — COM shift, approach/avoidance, gait, freezing
    "com_shift_x",
    "approach_avoid",
    "gait_phase_trot",
    "gait_phase_pace",
    "freeze_duration",
]

FEATURE_NAMES: list[str] = BASE_FEATURE_NAMES + MODALITY_NAMES

FEATURE_DIM = len(FEATURE_NAMES)
SEQUENCE_LEN = 15


def vectorize(features: dict) -> list[float]:
    base = [float(features.get(name, 0.0)) for name in BASE_FEATURE_NAMES]
    return base + modality_vectorize(features)
