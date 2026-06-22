"""Pose keypoint proxy from bbox geometry."""
from __future__ import annotations

from dataclasses import dataclass

from app.dog_detect import BBox


@dataclass
class Pose:
    tail_base: tuple[float, float]
    neck: tuple[float, float]
    nose: tuple[float, float]


def estimate_pose(bbox: BBox) -> Pose:
    cx = bbox.x + bbox.w / 2
    return Pose(
        tail_base=(bbox.x + 0.1, bbox.y + bbox.h * 0.5),
        neck=(cx, bbox.y + bbox.h * 0.35),
        nose=(bbox.x + bbox.w * 0.85, bbox.y + bbox.h * 0.25),
    )
