"""Runtime engine tests (no camera)."""
from __future__ import annotations

import numpy as np

from app.engine import gate_decision, process_frame


def test_process_frame_synthetic() -> None:
    frame = np.full((120, 160, 3), 140, dtype=np.uint8)
    out = process_frame(frame)
    assert "intent" in out
    assert "confidence" in out
    assert "gate" in out


def test_gate_rejects_forbidden() -> None:
    from dataclasses import dataclass

    @dataclass
    class P:
        intent_id: str
        emotion_id: str
        behavior_id: str
        confidence: float

    pred = P("rest", "excited", "play_bow", 0.95)
    assert gate_decision(pred) == "reject"
