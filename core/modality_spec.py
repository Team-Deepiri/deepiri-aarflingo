"""Multimodal encoder outputs fused into the TriadNet feature vector."""
from __future__ import annotations

MODALITY_NAMES: list[str] = [
    "vision_yolo_dog_conf",
    "audio_arousal",
    "audio_valence",
    "audio_bark_prob",
    # docs/ADVANCED_MATH.md §4 — psychoacoustic descriptors
    "audio_f0",
    "audio_hnr",
    "audio_formant_f1",
    "audio_burstiness",
    "ecg_hr_norm",
    "ecg_stress",
    # docs/ADVANCED_MATH.md §8 — HRV spectral power ratio + short-term variability
    "ecg_lfhf",
    "ecg_rmssd_norm",
    "imu_activity",
    "imu_posture_static",
    # docs/ADVANCED_MATH.md §7 — cross-modal synchrony + latent fusion
    "sync_plv",
    "sync_corr",
    "sync_latent_arousal",
    "sync_latent_valence",
]

MODALITY_DIM = len(MODALITY_NAMES)


def modality_defaults() -> dict[str, float]:
    return {name: 0.0 for name in MODALITY_NAMES}


def modality_vectorize(features: dict) -> list[float]:
    return [float(features.get(name, 0.0)) for name in MODALITY_NAMES]
