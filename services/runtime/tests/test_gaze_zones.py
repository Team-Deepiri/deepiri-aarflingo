"""Gaze-zone hot-reload + config robustness tests (no camera)."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
import yaml

import app.gaze_zones as _zones

_PKG = "aarf_perception"
_FAKE_MODULES = (_PKG, f"{_PKG}.gaze", f"{_PKG}.pipeline")


def _save_and_clear_aarf() -> dict[str, object | None]:
    saved = {}
    for name in _FAKE_MODULES:
        saved[name] = sys.modules.pop(name, None)
    return saved


def _restore_aarf(saved: dict[str, object | None]) -> None:
    for name in _FAKE_MODULES:
        sys.modules.pop(name, None)
    for name, mod in saved.items():
        if mod is not None:
            sys.modules[name] = mod


@pytest.fixture
def fake_perception():
    """Mount a minimal `aarf_perception` package mirroring how the runtime
    registers the perception service (`aarf_perception.pipeline` +
    `aarf_perception.gaze`, not `aarf_perception.app.*`)."""
    saved = _save_and_clear_aarf()
    pkg = types.ModuleType(_PKG)
    sys.modules[_PKG] = pkg

    gaze = types.ModuleType(f"{_PKG}.gaze")

    def _load_zones(config_path: Path | None = None):
        raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
        return {name: dict(vals) for name, vals in raw.items()}

    gaze.load_zones = _load_zones
    sys.modules[f"{_PKG}.gaze"] = gaze

    pipeline = types.ModuleType(f"{_PKG}.pipeline")
    pipeline._ZONES = {}
    sys.modules[f"{_PKG}.pipeline"] = pipeline
    yield pipeline
    _restore_aarf(saved)


@pytest.fixture
def no_perception_loaded():
    """Guarantee no aarf_perception package is present (e.g. engine import)."""
    saved = _save_and_clear_aarf()
    yield
    _restore_aarf(saved)


def test_reload_zones_rebinds_live_pipeline(tmp_path, monkeypatch, fake_perception) -> None:
    """Regression for F-1: reload must import from `aarf_perception.gaze`
    (runtime registration), not `aarf_perception.app.gaze`."""
    monkeypatch.setattr(_zones, "ZONES_PATH", tmp_path / "zones.yaml")
    _zones.write_zones({"door": {"x": 0.5, "y": 0.1, "w": 0.3, "h": 0.4}})
    assert _zones.reload_zones() is True
    assert fake_perception._ZONES == {"door": {"x": 0.5, "y": 0.1, "w": 0.3, "h": 0.4}}


def test_reload_zones_returns_false_without_pipeline(tmp_path, monkeypatch, no_perception_loaded) -> None:
    monkeypatch.setattr(_zones, "ZONES_PATH", tmp_path / "zones.yaml")
    _zones.write_zones(dict(_zones.DEFAULT_ZONES))
    assert _zones.reload_zones() is False


def test_reload_zones_survives_malformed_config(tmp_path, monkeypatch, fake_perception) -> None:
    """Reload must not raise/500 when the on-disk config is corrupt."""
    monkeypatch.setattr(_zones, "ZONES_PATH", tmp_path / "zones.yaml")
    (tmp_path / "zones.yaml").write_text("door: {x: [not, a, number]\n  bad", encoding="utf-8")
    assert _zones.reload_zones() is False
    assert fake_perception._ZONES == {}


def test_read_zones_falls_back_on_malformed_yaml(tmp_path: Path) -> None:
    p = tmp_path / "zones.yaml"
    p.write_text("door: {x: [not, closed", encoding="utf-8")
    assert _zones.read_zones(p) == _zones.DEFAULT_ZONES


def test_read_zones_skips_non_numeric_values(tmp_path: Path) -> None:
    p = tmp_path / "zones.yaml"
    p.write_text(
        "door: {x: abc, y: 0.1, w: 0.2, h: 0.3}\ntoy: {x: 0.1, y: 0.2, w: 0.3, h: 0.4}\n",
        encoding="utf-8",
    )
    zones = _zones.read_zones(p)
    assert "door" not in zones
    assert zones["toy"] == {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}


def test_write_zones_uses_unique_temp_file(tmp_path: Path) -> None:
    p = _zones.write_zones(dict(_zones.DEFAULT_ZONES), tmp_path / "zones.yaml")
    leftovers = list(tmp_path.glob("zones.yaml.*.tmp"))
    assert leftovers == []
    assert p.exists()