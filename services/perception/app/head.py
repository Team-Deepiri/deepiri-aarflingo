"""Head angle & orientation (docs/ADVANCED_MATH.md §3).

Rotation math operates on supplied pitch/yaw/roll angles (radians) or head/
object direction vectors — no keypoint detector included here, same split
as tail.py/facs.py.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


def rotation_matrix(yaw: float, pitch: float, roll: float) -> np.ndarray:
    """R_head = R_z(yaw) R_y(pitch) R_x(roll), intrinsic body-frame convention."""
    cz, sz = math.cos(yaw), math.sin(yaw)
    cy, sy = math.cos(pitch), math.sin(pitch)
    cx, sx = math.cos(roll), math.sin(roll)
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    return rz @ ry @ rx


def attention_alignment(head_vector: tuple[float, float, float], object_vector: tuple[float, float, float]) -> float:
    """Cosine similarity between head-pointing vector and object direction.

    1.0 -> looking directly at the object; 0.0 -> perpendicular; -1.0 ->
    facing directly away. A practical proxy for "attention to stimulus"
    that combines head yaw with gaze, per the doc.
    """
    h = np.asarray(head_vector, dtype=float)
    o = np.asarray(object_vector, dtype=float)
    hn, on = np.linalg.norm(h), np.linalg.norm(o)
    if hn < 1e-9 or on < 1e-9:
        return 0.0
    return float(np.clip(np.dot(h, o) / (hn * on), -1.0, 1.0))


@dataclass
class RollTracker:
    """Rolling roll-angle variance -> head-cock / cognitive-processing signal.

    sigma_roll^2 = (1/T) * integral[(roll(tau) - mean_roll)^2] dtau over a
    window. Elevated variance -> cognitive processing / auditory attention
    (2020 Animal Cognition head-tilt finding).
    """

    window_s: float = 5.0
    samples: list[tuple[float, float]] = field(default_factory=list)  # (t, roll)

    def push(self, t: float, roll: float) -> None:
        self.samples.append((t, roll))
        cutoff = t - self.window_s
        self.samples = [(ts, r) for ts, r in self.samples if ts >= cutoff]

    def roll_variance(self) -> float:
        if len(self.samples) < 2:
            return 0.0
        rolls = [r for _, r in self.samples]
        mean_r = sum(rolls) / len(rolls)
        return sum((r - mean_r) ** 2 for r in rolls) / len(rolls)
