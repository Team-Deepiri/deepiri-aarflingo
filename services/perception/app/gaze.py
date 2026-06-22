"""Gaze aversion proxy from nose-neck vector."""
from __future__ import annotations

import math

from app.pose import Pose


def gaze_aversion(pose: Pose) -> float:
    nx, ny = pose.nose
    cx, cy = pose.neck
    dx = nx - cx
    dy = ny - cy
    angle = abs(math.atan2(dy, dx))
    return min(1.0, angle / math.pi)
