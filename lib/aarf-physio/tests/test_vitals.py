from __future__ import annotations

import numpy as np

from aarf_physio.ecg import ecg_window_features, synthesize_ecg
from aarf_physio.imu import imu_window_features, synthesize_imu_window


def test_synthetic_ecg_hrv_in_range() -> None:
    ecg = synthesize_ecg(hr_bpm=85.0, sdnn_ms=50.0, seed=1)
    feats = ecg_window_features(ecg)
    assert 50.0 < feats["hr_bpm"] < 130.0
    assert feats["sdnn_ms"] > 0.0


def test_imu_activity_walking_gt_lying() -> None:
    walk = imu_window_features(synthesize_imu_window("walking", seed=2))
    lie = imu_window_features(synthesize_imu_window("lying", seed=3))
    assert walk["activity"] > lie["activity"]
