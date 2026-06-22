"""Scene context tags from simple statistics."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SceneContext:
    indoor: bool
    motion_level: float
    tags: list[str]


def classify_scene(frame_bytes: bytes) -> SceneContext:
    mean_val = sum(frame_bytes) / max(len(frame_bytes), 1) / 255.0
    indoor = mean_val < 0.6
    motion = min(1.0, mean_val)
    tags = ["indoor"] if indoor else ["outdoor"]
    if motion > 0.5:
        tags.append("active")
    return SceneContext(indoor=indoor, motion_level=motion, tags=tags)
