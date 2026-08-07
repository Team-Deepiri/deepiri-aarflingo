"""Posture features from bounding box geometry (extensible to keypoints).

v0.2 upgrade: enriches the bare aspect ratio with head-region, play-bow,
and body-stretch posture signals that feed the TriadNet feature vector.
A keypoint head can override these when a dog-pose model is available.
"""
from __future__ import annotations

from dataclasses import dataclass

from .dog_detect import BBox


@dataclass
class PoseEstimate:
    aspect_ratio: float
    height_ratio: float
    center_y: float
    leaning_forward: float
    head_y: float = 0.5
    head_gaze_x: float = 0.5
    body_stretch: float = 0.5
    play_bow: float = 0.0

    @classmethod
    def from_geometry(cls, bbox: BBox) -> "PoseEstimate":
        aspect = bbox.w / max(bbox.h, 1e-6)
        # Head sits near the top edge of the box; head_y = 0 means the head is
        # high in the frame, 1 means lowered toward the ground.
        head_y = min(1.0, max(0.0, bbox.y + bbox.h))
        head_gaze_x = min(1.0, max(0.0, bbox.cx))
        stretch = max(0.0, min(1.0, aspect / 1.5)) if aspect < 1.5 else min(1.0, aspect / 2.5)
        # Play bow heuristic: wide box (front legs down) + head lowered low in
        # the frame (crouching toward the ground).
        wide = min(1.0, max(0.0, (aspect - 1.2) / 0.8))
        head_low = min(1.0, max(0.0, (bbox.y - 0.35) / 0.3))
        play_bow = wide * head_low
        return cls(
            aspect_ratio=aspect,
            height_ratio=bbox.h,
            center_y=bbox.cy,
            leaning_forward=max(0.0, 0.65 - bbox.cy),
            head_y=head_y,
            head_gaze_x=head_gaze_x,
            body_stretch=stretch,
            play_bow=play_bow,
        )


def estimate_pose(bbox: BBox) -> PoseEstimate:
    return PoseEstimate.from_geometry(bbox)
