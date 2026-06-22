"""Track bbox across frames for velocity / motion features."""
from __future__ import annotations

from dataclasses import dataclass, field

from .dog_detect import BBox


@dataclass
class TemporalTracker:
    prev_bbox: BBox | None = None
    prev_gray_mean: float = 0.0
    motion_ema: float = 0.0

    def update(self, bbox: BBox | None, frame_gray_mean: float) -> tuple[float, float, float]:
        motion = abs(frame_gray_mean - self.prev_gray_mean)
        self.motion_ema = 0.85 * self.motion_ema + 0.15 * motion
        vx, vy = 0.0, 0.0
        if bbox and self.prev_bbox:
            vx = bbox.cx - self.prev_bbox.cx
            vy = bbox.cy - self.prev_bbox.cy
        if bbox:
            self.prev_bbox = bbox
        self.prev_gray_mean = frame_gray_mean
        return self.motion_ema, vx, vy
