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
