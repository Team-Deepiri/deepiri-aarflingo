"""Face region heuristics for stress signals."""
from __future__ import annotations

from dataclasses import dataclass

from app.pose import Pose


@dataclass
class FaceSignals:
    whale_eye_likelihood: float
    lip_lick_likelihood: float


def estimate_face_signals(pose: Pose, arousal_proxy: float = 0.3) -> FaceSignals:
    return FaceSignals(
        whale_eye_likelihood=min(1.0, arousal_proxy * 0.8),
        lip_lick_likelihood=min(1.0, arousal_proxy * 0.5),
    )
