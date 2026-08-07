"""ConversationEngine: weight updates, response window, phrase selection drift."""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.conversation import (
    LEARNING_RATE,
    DEFAULT_WEIGHT,
    REWARD_NEGATIVE,
    REWARD_POSITIVE,
    REWARD_SILENCE,
    RESPONSE_WINDOW_S,
    ConversationEngine,
)
from app.mic_listener import BarkEvent
from app.dog_voice import DogVoice


# ── fakes ──────────────────────────────────────────────────────────────────

@dataclass
class FakePred:
    intent_id: str = "play"
    emotion_id: str = "excited"
    behavior_id: str = "play_bow"


@dataclass
class _FakeSpeechClient:
    synthesize_returns: bytes = b"\x00\x01" * 100

    def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:
        return self.synthesize_returns


class _FakeStore:
    def __init__(self):
        self.outcomes: list[dict] = []

    def log_voice_outcome(self, **kwargs) -> str:
        self.outcomes.append(kwargs)
        return "fake-id"


def _make_engine(tmp_path: Path, window_s: float = 1.0, store=None) -> ConversationEngine:
    client = _FakeSpeechClient()
    voice = DogVoice(client, cooldown_s=0.0)
    weights_path = tmp_path / "weights.json"
    return ConversationEngine(
        voice=voice,
        store=store,
        weights_path=weights_path,
        response_window_s=window_s,
        learning_rate=LEARNING_RATE,
    )


def _bark(arousal="high", valence="positive", ts=None) -> BarkEvent:
    return BarkEvent(
        ts=ts if ts is not None else time.monotonic(),
        arousal=arousal,
        valence=valence,
        rms=0.3,
    )


# ── tests ──────────────────────────────────────────────────────────────────

def test_on_prediction_returns_phrase(tmp_path: Path) -> None:
    eng = _make_engine(tmp_path)
    result = eng.on_prediction(FakePred())
    assert result is not None
    assert "phrase" in result
    assert len(result["phrase"]) > 0
    eng.stop()


def test_bark_in_window_is_scored(tmp_path: Path) -> None:
    store = _FakeStore()
    eng = _make_engine(tmp_path, window_s=2.0, store=store)
    eng.on_prediction(FakePred())
    time.sleep(0.05)
    result = eng.on_bark(_bark(valence="positive"))
    assert result is not None
    assert result["responded"] is True
    assert result["bark_valence"] == "positive"
    assert result["reward"] == REWARD_POSITIVE
    assert len(store.outcomes) == 1
    eng.stop()


def test_bark_after_window_is_ignored(tmp_path: Path) -> None:
    eng = _make_engine(tmp_path, window_s=0.1)
    eng.on_prediction(FakePred())
    time.sleep(0.15)
    result = eng.on_bark(_bark())
    assert result is None
    eng.stop()


def test_silence_window_expires_as_silence(tmp_path: Path) -> None:
    store = _FakeStore()
    eng = _make_engine(tmp_path, window_s=0.2, store=store)
    eng.on_prediction(FakePred())
    time.sleep(0.5)  # let expiry thread fire
    assert len(store.outcomes) == 1
    assert store.outcomes[0]["responded"] is False
    assert store.outcomes[0]["reward"] == REWARD_SILENCE
    eng.stop()


def test_positive_bark_raises_phrase_weight(tmp_path: Path) -> None:
    eng = _make_engine(tmp_path, window_s=2.0)
    eng.on_prediction(FakePred())
    phrase = eng._pending.phrase  # type: ignore[union-attr]
    w_before = eng._weights.get(phrase, DEFAULT_WEIGHT)
    eng.on_bark(_bark(valence="positive"))
    w_after = eng._weights.get(phrase, DEFAULT_WEIGHT)
    assert w_after > w_before
    eng.stop()


def test_negative_bark_lowers_phrase_weight(tmp_path: Path) -> None:
    eng = _make_engine(tmp_path, window_s=2.0)
    eng.on_prediction(FakePred())
    phrase = eng._pending.phrase  # type: ignore[union-attr]
    eng._weights[phrase] = DEFAULT_WEIGHT  # ensure known start
    eng.on_bark(_bark(valence="negative"))
    w_after = eng._weights.get(phrase, DEFAULT_WEIGHT)
    assert w_after < DEFAULT_WEIGHT
    eng.stop()


def test_weights_persist_across_restart(tmp_path: Path) -> None:
    eng1 = _make_engine(tmp_path, window_s=2.0)
    eng1.on_prediction(FakePred())
    phrase = eng1._pending.phrase  # type: ignore[union-attr]
    eng1.on_bark(_bark(valence="positive"))
    w1 = eng1._weights[phrase]
    eng1.stop()

    eng2 = _make_engine(tmp_path, window_s=2.0)
    assert eng2._weights.get(phrase) == pytest.approx(w1, rel=1e-4)
    eng2.stop()


def test_best_phrase_prefers_high_weight(tmp_path: Path) -> None:
    eng = _make_engine(tmp_path, window_s=2.0)
    from app.dog_voice import _PHRASES
    pred = FakePred("play", "excited", "play_bow")
    candidates = _PHRASES.get(("play", "excited"), [])
    if len(candidates) < 2:
        pytest.skip("need at least 2 phrases for this test")

    # Artificially push first phrase weight very high
    eng._weights[candidates[0]] = 1.9
    eng._weights[candidates[1]] = 0.1
    best = eng.best_phrase_for(pred)
    assert best == candidates[0]
    eng.stop()


def test_on_bark_without_pending_returns_none(tmp_path: Path) -> None:
    eng = _make_engine(tmp_path)
    assert eng.on_bark(_bark()) is None
    eng.stop()


def test_second_prediction_closes_unanswered_window(tmp_path: Path) -> None:
    store = _FakeStore()
    eng = _make_engine(tmp_path, window_s=30.0, store=store)
    eng.on_prediction(FakePred())
    time.sleep(0.05)
    eng.on_prediction(FakePred("rest", "calm", "yawning"))
    # First window should be closed as silence
    assert len(store.outcomes) == 1
    assert store.outcomes[0]["responded"] is False
    eng.stop()


def test_phrase_weight_floor(tmp_path: Path) -> None:
    from app.conversation import WEIGHT_FLOOR
    eng = _make_engine(tmp_path, window_s=2.0)
    eng.on_prediction(FakePred())
    phrase = eng._pending.phrase  # type: ignore[union-attr]
    # Drive weight down through many negative barks
    for _ in range(30):
        eng._weights[phrase] = DEFAULT_WEIGHT
        eng._pending.outcome_logged = False  # type: ignore[union-attr]
        eng._pending.spoken_at = time.monotonic()  # type: ignore[union-attr]
        eng.on_bark(_bark(valence="negative"))
    assert eng._weights[phrase] >= WEIGHT_FLOOR
    eng.stop()
