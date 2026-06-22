"""Synthetic frame capture for dev / smoke tests."""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class Frame:
    index: int
    ts_ms: int
    pixels: bytes


def capture_frames(count: int = 10, interval_ms: int = 100) -> list[Frame]:
    frames: list[Frame] = []
    start = int(time.time() * 1000)
    for i in range(count):
        ts = start + i * interval_ms
        frames.append(Frame(index=i, ts_ms=ts, pixels=bytes([i % 256] * 16)))
    return frames
