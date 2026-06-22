"""Minimal dog detection stub using luminance threshold."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BBox:
    x: float
    y: float
    w: float
    h: float
    confidence: float


def detect_dog(frame_bytes: bytes, width: int = 64, height: int = 64) -> BBox | None:
    if not frame_bytes:
        return None
    mean_val = sum(frame_bytes) / len(frame_bytes) / 255.0
    if mean_val < 0.05:
        return None
    return BBox(x=0.2, y=0.15, w=0.5, h=0.7, confidence=min(0.99, mean_val + 0.3))
