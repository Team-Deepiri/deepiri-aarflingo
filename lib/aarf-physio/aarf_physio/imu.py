"""IMU window features shaped after Mendeley dog posture/behavior datasets."""
from __future__ import annotations

import numpy as np

# 100 Hz, 6-DoF (accel + gyro) — collar/harness placement from vxhx934tbn / mpph6bmn7g.
DEFAULT_SAMPLE_RATE = 100.0
POSTURES = ("standing", "sitting", "lying", "walking", "shake")


def synthesize_imu_window(
    posture: str = "standing",
    duration_s: float = 3.0,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    seed: int | None = None,
) -> np.ndarray:
    """Return (N, 6) accel_xyz + gyro_xyz."""
    rng = np.random.default_rng(seed)
    n = int(duration_s * sample_rate)
    t = np.linspace(0, duration_s, n, dtype=np.float32)
    gravity = np.array([0.0, -1.0, 0.0], dtype=np.float32)

    if posture == "lying":
        gravity = np.array([0.0, 0.0, -1.0], dtype=np.float32)
        motion = 0.02
    elif posture == "sitting":
        gravity = np.array([0.2, -0.9, 0.1], dtype=np.float32)
        motion = 0.04
    elif posture == "walking":
        gravity = np.array([0.05, -0.98, 0.05], dtype=np.float32)
        motion = 0.35
    elif posture == "shake":
        gravity = np.array([0.0, -1.0, 0.0], dtype=np.float32)
        motion = 0.8
    else:
        motion = 0.06

    accel = np.tile(gravity, (n, 1))
    if posture in ("walking", "shake"):
        accel[:, 0] += motion * np.sin(2 * np.pi * (3.5 if posture == "walking" else 8.0) * t)
        accel[:, 2] += motion * 0.5 * np.cos(2 * np.pi * 2.0 * t)
    gyro = rng.normal(0.0, motion * 0.4, size=(n, 3)).astype(np.float32)
    accel += rng.normal(0.0, 0.03, size=(n, 3)).astype(np.float32)
    return np.concatenate([accel, gyro], axis=1).astype(np.float32)


def imu_window_features(window: np.ndarray) -> dict[str, float]:
    if window.ndim != 2 or window.shape[1] < 6:
        return {"activity": 0.0, "posture_static": 1.0}
    accel = window[:, :3]
    gyro = window[:, 3:6]
    activity = float(np.mean(np.linalg.norm(accel, axis=1)) + np.mean(np.linalg.norm(gyro, axis=1)))
    activity = min(1.0, activity / 2.5)
    static = 1.0 - min(1.0, float(np.std(accel)) * 4.0)
    return {"activity": activity, "posture_static": static}
