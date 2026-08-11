from __future__ import annotations

from app.dog_detect import BBox
from app.tracker import MultiDogTracker, appearance_similarity, iou


def _bb(x: float, y: float, w: float, h: float, conf: float = 0.9) -> BBox:
    return BBox(x=x, y=y, w=w, h=h, confidence=conf)


def test_iou_overlap_and_disjoint() -> None:
    a = _bb(0.1, 0.1, 0.5, 0.5)
    assert iou(a, _bb(0.2, 0.2, 0.5, 0.5)) > 0.3
    assert iou(a, _bb(0.9, 0.9, 0.1, 0.1)) == 0.0


def test_tracker_keeps_single_identity_across_moves() -> None:
    tracker = MultiDogTracker()
    track = tracker.update([_bb(0.1, 0.1, 0.3, 0.3)])
    assert len(track) == 1
    tid = track[0].track_id
    for x in (0.12, 0.15, 0.18):
        track = tracker.update([_bb(x, 0.1, 0.3, 0.3)])
    assert track[0].track_id == tid
    assert track[0].hits >= 2


def test_tracker_reuses_id_after_brief_gap() -> None:
    tracker = MultiDogTracker()
    tid = tracker.update([_bb(0.1, 0.1, 0.3, 0.3)])[0].track_id
    tracker.update([], None)
    track = tracker.update([_bb(0.12, 0.1, 0.3, 0.3)])
    assert track[0].track_id == tid


def test_tracker_spawns_second_track_for_distinct_dog() -> None:
    tracker = MultiDogTracker()
    tracker.update([_bb(0.1, 0.1, 0.2, 0.2), _bb(0.7, 0.7, 0.2, 0.2)])
    track = tracker.update([_bb(0.1, 0.1, 0.2, 0.2), _bb(0.7, 0.7, 0.2, 0.2)])
    ids = {t.track_id for t in track}
    assert len(ids) == 2


def test_primary_prefers_stable_track() -> None:
    tracker = MultiDogTracker()
    tracker.update([_bb(0.1, 0.1, 0.2, 0.2)])
    for _ in range(4):
        tracker.update([_bb(0.1, 0.1, 0.2, 0.2)])
    tracker.update([_bb(0.7, 0.7, 0.2, 0.2)])
    primary = tracker.primary()
    assert primary is not None
    assert primary.track_id == 0


def test_appearance_similarity_bounded() -> None:
    import numpy as np

    a = np.zeros(32 * 32, dtype=np.float32)
    a[0] = 1.0
    assert 0.0 <= appearance_similarity(a, a) <= 1.0
    assert appearance_similarity(None, None) == 0.0
