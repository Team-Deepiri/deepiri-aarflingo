"""Approach geometry (tau/closing/heading) tests."""
from __future__ import annotations

from app.dog_detect import BBox
from app.gaze import Zone
from app.tau import score_approach

ZONES = {
    "door": Zone(x=0.75, y=0.05, w=0.22, h=0.45),
    "toy": Zone(x=0.05, y=0.55, w=0.25, h=0.35),
    "bowl": Zone(x=0.40, y=0.70, w=0.20, h=0.25),
}


def _bbox(cx: float, cy: float) -> BBox:
    return BBox(x=cx - 0.05, y=cy - 0.05, w=0.1, h=0.1, confidence=0.9)


def test_approaching_zone_gives_high_tau_and_closing() -> None:
    dog = _bbox(cx=0.45, cy=0.25)
    scores = score_approach(dog, vx=0.02, vy=0.02, zones=ZONES)
    assert scores.tau["door"] > 0.5
    assert scores.closing["door"] > 0.5
    assert scores.heading["door"] > 0.5


def test_moving_away_gives_negative_heading_and_zero_closing() -> None:
    dog = _bbox(cx=0.45, cy=0.25)
    scores = score_approach(dog, vx=-0.02, vy=-0.02, zones=ZONES)
    assert scores.heading["door"] < 0
    assert scores.closing["door"] == 0.0
    assert scores.tau["door"] < 0.1


def test_stationary_dog_has_zero_heading() -> None:
    dog = _bbox(cx=0.5, cy=0.5)
    scores = score_approach(dog, vx=0.0, vy=0.0, zones=ZONES)
    for z in ZONES:
        assert scores.heading[z] == 0.0
        assert scores.closing[z] == 0.0


def test_heading_is_cosine_bounded() -> None:
    dog = _bbox(cx=0.2, cy=0.2)
    scores = score_approach(dog, vx=0.01, vy=0.0, zones=ZONES)
    for z in ZONES:
        assert -1.0 <= scores.heading[z] <= 1.0
        assert 0.0 <= scores.closing[z] <= 1.0
        assert 0.0 <= scores.tau[z] <= 1.0
