"""Runtime engine tests (no camera)."""
from __future__ import annotations

import numpy as np

from app.engine import STATE, gate_decision, process_frame, update_audio_modality


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


def test_live_audio_modality_fused_into_features() -> None:
    update_audio_modality(audio_arousal=0.8, audio_valence=0.6, audio_bark_prob=0.9)
    try:
        frame = np.full((120, 160, 3), 140, dtype=np.uint8)
        out = process_frame(frame)
        feats = out["features"]
        assert feats["audio_arousal"] == 0.8
        assert feats["audio_valence"] == 0.6
        assert feats["audio_bark_prob"] == 0.9
    finally:
        update_audio_modality()  # reset so other tests start clean
        STATE.latest_audio_modality = {}
