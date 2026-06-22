"""Multimodal encoder outputs fused into the TriadNet feature vector."""
from __future__ import annotations

MODALITY_NAMES: list[str] = [
    "vision_yolo_dog_conf",
    "audio_arousal",
    "audio_valence",
    "audio_bark_prob",
    "ecg_hr_norm",
    "ecg_stress",
    "imu_activity",
    "imu_posture_static",
]

MODALITY_DIM = len(MODALITY_NAMES)


def modality_defaults() -> dict[str, float]:
    return {name: 0.0 for name in MODALITY_NAMES}


def modality_vectorize(features: dict) -> list[float]:
    return [float(features.get(name, 0.0)) for name in MODALITY_NAMES]
