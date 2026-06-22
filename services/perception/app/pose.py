"""Pose proxy from bounding box geometry."""
from __future__ import annotations

from dataclasses import dataclass

from .dog_detect import BBox


@dataclass
class PoseEstimate:
    aspect_ratio: float
    height_ratio: float
    center_y: float
    leaning_forward: float


def estimate_pose(bbox: BBox) -> PoseEstimate:
    aspect = bbox.w / max(bbox.h, 1e-6)
    return PoseEstimate(
        aspect_ratio=aspect,
        height_ratio=bbox.h,
        center_y=bbox.cy,
        leaning_forward=max(0.0, 0.65 - bbox.cy),
    )
