"""Small vitals encoder: ECG HRV + IMU activity → modality features."""
from __future__ import annotations

from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F

from .ecg import ecg_window_features, synthesize_ecg
from .imu import imu_window_features, synthesize_imu_window


class VitalsEncoder(nn.Module):
    def __init__(self, hidden: int = 32) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(6, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 4),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def features_to_tensor(ecg_feats: dict[str, float], imu_feats: dict[str, float]) -> torch.Tensor:
    return torch.tensor(
        [
            ecg_feats["hr_norm"],
            ecg_feats["stress_score"],
            ecg_feats["sdnn_ms"] / 100.0,
            imu_feats["activity"],
            imu_feats["posture_static"],
            ecg_feats["rmssd_ms"] / 100.0,
        ],
        dtype=torch.float32,
    )


def modality_from_vitals(ecg_feats: dict[str, float], imu_feats: dict[str, float]) -> dict[str, float]:
    return {
        "ecg_hr_norm": ecg_feats["hr_norm"],
        "ecg_stress": ecg_feats["stress_score"],
        "imu_activity": imu_feats["activity"],
        "imu_posture_static": imu_feats["posture_static"],
    }


def infer_modality(model: VitalsEncoder, ecg_feats: dict[str, float], imu_feats: dict[str, float]) -> dict[str, float]:
    model.eval()
    x = features_to_tensor(ecg_feats, imu_feats).unsqueeze(0)
    with torch.no_grad():
        out = model(x)[0]
    probs = torch.softmax(out[:2], dim=0)
    return {
        "ecg_hr_norm": float(ecg_feats["hr_norm"]),
        "ecg_stress": float(torch.sigmoid(out[2])),
        "imu_activity": float(imu_feats["activity"]),
        "imu_posture_static": float(imu_feats["posture_static"]),
        "_vitals_head_stress": float(probs[1]),
    }


def default_checkpoint(root: Path | None = None) -> Path:
    base = root or Path(__file__).resolve().parents[3]
    return base / "artifacts" / "models" / "default" / "vitals.pt"
