"""Clip windows around motion triggers."""
from __future__ import annotations

from dataclasses import dataclass

from app.capture import Frame


@dataclass
class Clip:
    start_ms: int
    end_ms: int
    frames: list[Frame]


def clip_around_trigger(
    frames: list[Frame],
    trigger_ms: int,
    pre_roll_ms: int = 500,
    clip_ms: int = 3000,
) -> Clip:
    start = trigger_ms - pre_roll_ms
    end = trigger_ms + clip_ms
    selected = [f for f in frames if start <= f.ts_ms <= end]
    if not selected:
        selected = frames[:1]
    return Clip(start_ms=start, end_ms=end, frames=selected)
