"""Feedback store tests."""
from __future__ import annotations

from pathlib import Path

from app.store import FeedbackStore


def test_feedback_roundtrip(tmp_path: Path) -> None:
    db = FeedbackStore(tmp_path / "t.db")
    sid = db.start_session("dog1")
    pid = db.log_prediction(sid, "play", "excited", "play_bow", 0.9, {}, [[0.0] * 20] * 15)
    db.add_feedback(pid, rating=1, corrected_intent="outside")
    out = tmp_path / "export.json"
    n = db.export_training_json(out)
    assert n == 1
    assert out.exists()


def test_recent_predictions_marks_needs_label(tmp_path: Path) -> None:
    db = FeedbackStore(tmp_path / "t.db")
    sid = db.start_session("dog1")
    high = db.log_prediction(sid, "play", "excited", "play_bow", 0.93, {}, [[0.0] * 20] * 15)
    low_labelled = db.log_prediction(sid, "rest", "calm", "tail_wag_loose", 0.55, {}, [[0.0] * 20] * 15)
    low_unlabelled = db.log_prediction(sid, "alert", "fearful", "lip_lick", 0.42, {}, [[0.0] * 20] * 15)
    db.add_feedback(low_labelled, rating=1, corrected_intent="food")

    rows = {r["id"]: r for r in db.recent_predictions(10)}
    assert rows[high]["has_feedback"] is False
    assert rows[high]["needs_label"] is False  # confident — no label needed
    assert rows[low_labelled]["has_feedback"] is True
    assert rows[low_labelled]["needs_label"] is False  # labelled
    assert rows[low_unlabelled]["has_feedback"] is False
    assert rows[low_unlabelled]["needs_label"] is True  # unlabelled + conf < 0.8
