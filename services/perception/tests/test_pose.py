from __future__ import annotations

from app.dog_detect import BBox
from app.pose import estimate_pose


def _bb(x: float, y: float, w: float, h: float) -> BBox:
    return BBox(x=x, y=y, w=w, h=h, confidence=0.9)


def test_pose_defaults_in_range() -> None:
    pose = estimate_pose(_bb(0.2, 0.1, 0.5, 0.6))
    assert 0.0 <= pose.aspect_ratio <= 1.0
    assert 0.0 <= pose.head_y <= 1.0
    assert 0.0 <= pose.head_gaze_x <= 1.0


def test_wide_low_box_scores_play_bow() -> None:
    wide_low = estimate_pose(_bb(0.1, 0.5, 0.8, 0.3))
    tall_high = estimate_pose(_bb(0.1, 0.1, 0.2, 0.8))
    assert wide_low.play_bow > 0.0
    assert tall_high.play_bow == 0.0


def test_head_y_lower_for_bottom_heavy_box() -> None:
    low = estimate_pose(_bb(0.1, 0.6, 0.5, 0.3))
    high = estimate_pose(_bb(0.1, 0.1, 0.5, 0.3))
    assert low.head_y > high.head_y


def test_body_stretch_scales_with_aspect() -> None:
    wide = estimate_pose(_bb(0.1, 0.1, 0.7, 0.2))
    tall = estimate_pose(_bb(0.1, 0.1, 0.2, 0.7))
    assert wide.body_stretch > tall.body_stretch
