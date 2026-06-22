from __future__ import annotations

from core.feature_spec import FEATURE_DIM, FEATURE_NAMES
from core.modality_spec import MODALITY_DIM, MODALITY_NAMES


def test_feature_dim_includes_modalities() -> None:
    assert FEATURE_DIM == 20 + MODALITY_DIM
    assert len(FEATURE_NAMES) == FEATURE_DIM
    assert "vision_yolo_dog_conf" in MODALITY_NAMES
    assert "ecg_stress" in MODALITY_NAMES
