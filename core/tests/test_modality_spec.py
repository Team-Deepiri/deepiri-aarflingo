from __future__ import annotations

from core.feature_spec import BASE_FEATURE_NAMES, FEATURE_DIM, FEATURE_NAMES
from core.modality_spec import MODALITY_DIM, MODALITY_NAMES


def test_feature_dim_includes_modalities() -> None:
    assert FEATURE_DIM == len(BASE_FEATURE_NAMES) + MODALITY_DIM
    assert len(FEATURE_NAMES) == FEATURE_DIM
    assert "vision_yolo_dog_conf" in MODALITY_NAMES
    assert "ecg_stress" in MODALITY_NAMES


def test_new_vision_features_present() -> None:
    for name in ("n_dogs", "pose_head_y", "pose_head_gaze_x", "pose_body_stretch", "pose_play_bow"):
        assert name in BASE_FEATURE_NAMES


def test_approach_geometry_features_present() -> None:
    for name in (
        "tau_door", "tau_toy", "tau_bowl",
        "closing_door", "closing_toy", "closing_bowl",
        "heading_door", "heading_toy", "heading_bowl",
    ):
        assert name in BASE_FEATURE_NAMES
