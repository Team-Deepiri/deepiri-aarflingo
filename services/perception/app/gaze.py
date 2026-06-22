"""Gaze / attention proxy toward configured scene zones."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from .dog_detect import BBox


@dataclass
class Zone:
    x: float
    y: float
    w: float
    h: float


@dataclass
class GazeScores:
    door: float
    toy: float
    bowl: float
    center: float
    aversion: float


def _point_in_zone(px: float, py: float, zone: Zone) -> float:
    if zone.x <= px <= zone.x + zone.w and zone.y <= py <= zone.y + zone.h:
        cx, cy = zone.x + zone.w / 2, zone.y + zone.h / 2
        dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
        return max(0.0, 1.0 - dist * 2)
    cx, cy = zone.x + zone.w / 2, zone.y + zone.h / 2
    dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
    return max(0.0, 0.35 - dist)


def load_zones(config_path: Path | None = None) -> dict[str, Zone]:
    root = Path(__file__).resolve().parents[3]
    path = config_path or root / "infra" / "configs" / "zones.default.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {name: Zone(**vals) for name, vals in raw.items()}


def score_gaze(bbox: BBox, zones: dict[str, Zone] | None = None) -> GazeScores:
    zones = zones or load_zones()
    px, py = bbox.cx, bbox.cy
    door = _point_in_zone(px, py, zones["door"])
    toy = _point_in_zone(px, py, zones["toy"])
    bowl = _point_in_zone(px, py, zones["bowl"])
    center = max(0.0, 1.0 - abs(px - 0.5) - abs(py - 0.5))
    aversion = max(0.0, 1.0 - max(door, toy, bowl, center))
    return GazeScores(door=door, toy=toy, bowl=bowl, center=center, aversion=aversion)


def gaze_aversion(bbox: BBox, zones: dict[str, Zone] | None = None) -> float:
    return score_gaze(bbox, zones).aversion
