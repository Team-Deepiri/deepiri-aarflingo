"""Gaze zone config — read/write `infra/configs/zones.default.yaml`.

The perception pipeline loads zones once at import; `reload_zones` rebinds
`_ZONES` on the live pipeline module so edits from the Studio apply without a
runtime restart.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ZONES_PATH = _REPO_ROOT / "infra" / "configs" / "zones.default.yaml"

# Overridable so tests can point at a temp file instead of the repo config.
ZONES_PATH: Path | None = None


def _zones_path(path: Path | None) -> Path:
    return path or ZONES_PATH or DEFAULT_ZONES_PATH

DEFAULT_ZONES: dict[str, dict[str, float]] = {
    "door": {"x": 0.75, "y": 0.05, "w": 0.22, "h": 0.45},
    "toy": {"x": 0.05, "y": 0.55, "w": 0.25, "h": 0.35},
    "bowl": {"x": 0.40, "y": 0.70, "w": 0.20, "h": 0.25},
}


@dataclass
class Zone:
    x: float
    y: float
    w: float
    h: float


def read_zones(path: Path | None = None) -> dict[str, dict[str, float]]:
    """Read zones from disk; returns defaults when the file is missing."""
    p = _zones_path(path)
    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except (FileNotFoundError, OSError):
        return dict(DEFAULT_ZONES)
    zones: dict[str, dict[str, float]] = {}
    for name, vals in raw.items():
        if not isinstance(vals, dict):
            continue
        z = Zone(
            x=float(vals.get("x", 0.0)),
            y=float(vals.get("y", 0.0)),
            w=float(vals.get("w", 0.0)),
            h=float(vals.get("h", 0.0)),
        )
        zones[str(name)] = {"x": z.x, "y": z.y, "w": z.w, "h": z.h}
    return zones if zones else dict(DEFAULT_ZONES)


def write_zones(zones: dict[str, dict[str, float]], path: Path | None = None) -> Path:
    """Atomically persist zones to YAML, clamped to the unit square."""
    p = _zones_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cleaned: dict[str, dict[str, float]] = {}
    for name, vals in zones.items():
        z = Zone(
            x=min(1.0, max(0.0, float(vals.get("x", 0.0)))),
            y=min(1.0, max(0.0, float(vals.get("y", 0.0)))),
            w=min(1.0, max(0.0, float(vals.get("w", 0.0)))),
            h=min(1.0, max(0.0, float(vals.get("h", 0.0)))),
        )
        cleaned[str(name)] = {"x": round(z.x, 4), "y": round(z.y, 4), "w": round(z.w, 4), "h": round(z.h, 4)}
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(cleaned, sort_keys=False), encoding="utf-8")
    tmp.replace(p)
    return p


def reload_zones() -> bool:
    """Rebind `_ZONES` on a live perception pipeline module (if loaded).

    Returns True when the live pipeline picked up the new zones.
    """
    mod = None
    for name in ("aarf_perception.pipeline", "perception.pipeline"):
        m = sys.modules.get(name)
        if m is not None and hasattr(m, "_ZONES"):
            mod = m
            break
    if mod is None:
        return False
    try:
        from aarf_perception.app.gaze import load_zones as _load
    except ImportError:
        try:
            from perception.app.gaze import load_zones as _load  # type: ignore[no-redef]
        except ImportError:
            return False
    mod._ZONES = _load()  # type: ignore[attr-defined]
    return True