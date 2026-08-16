"""Runtime engine tests (no camera)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from app.engine import STATE, _maybe_autofill_breed, gate_decision, process_frame, update_audio_modality


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


def test_process_frame_exposes_bbox_and_breed_fields() -> None:
    frame = np.full((120, 160, 3), 140, dtype=np.uint8)
    out = process_frame(frame)
    assert "bbox" in out
    assert "breed" in out
    assert "breed_conf" in out
    assert "breed_top3" in out


def test_autofill_breed_writes_profile_once(tmp_path: Path, monkeypatch) -> None:
    from app import dog_profile
    from app.dog_profile import load_profile

    monkeypatch.setattr(dog_profile, "ARTIFACTS", tmp_path)
    _orig_dog_id = STATE.dog_id
    try:
        test_id = "aarf-autofill-test"
        STATE.dog_id = test_id

        feats = {"dog_present": 1.0, "breed": "Golden Retriever", "breed_conf": 0.9}
        _maybe_autofill_breed(feats)
        p = load_profile(test_id)
        assert p.breed == "Golden Retriever"
        assert (tmp_path / f"{test_id}.json").exists()

        # second call must NOT overwrite
        _maybe_autofill_breed({**feats, "breed": "Poodle"})
        assert load_profile(test_id).breed == "Golden Retriever"

        # low confidence must not write at all
        low_id = "low-aarf-autofill-test"
        STATE.dog_id = low_id
        _maybe_autofill_breed({**feats, "breed_conf": 0.1})
        assert not (tmp_path / f"{low_id}.json").exists()
    finally:
        STATE.dog_id = _orig_dog_id
