"""DogVoice phrase selection, cooldown, and bark responses."""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.dog_voice import DEFAULT_COOLDOWN_S, DogVoice, phrase_for, response_to_bark
from app.speech_client import SpeechClient


@dataclass
class FakePred:
    intent_id: str
    emotion_id: str
    behavior_id: str


@dataclass
class _FakeClient:
    last_text: str | None = None
    synthesize_returns: bytes = b"\x00\x01"

    def synthesize(self, text: str, voice: Optional[str] = None) -> bytes:
        self.last_text = text
        return self.synthesize_returns


def test_phrase_for_intent_emotion() -> None:
    pred = FakePred("play", "excited", "play_bow")
    phrase = phrase_for(pred)
    assert isinstance(phrase, str) and len(phrase) > 0


def test_phrase_falls_back_for_unknown_intent() -> None:
    pred = FakePred("teleport", "baffled", "vanish")
    assert phrase_for(pred) in ("Good dog, buddy.", "I see you, buddy.")


def test_response_to_bark_matches_arousal() -> None:
    high_neg = {
        "hey buddy, it's okay. you're safe with me.",
        "easy, easy. what's wrong, buddy?",
    }
    assert response_to_bark("high", "negative").lower() in high_neg


def test_speak_respects_cooldown() -> None:
    client = _FakeClient()
    dv = DogVoice(client, cooldown_s=DEFAULT_COOLDOWN_S)
    assert dv.can_speak()
    assert dv.speak("first") == client.synthesize_returns
    assert not dv.can_speak()
    assert dv.speak("second") is None  # inside cooldown
    assert client.last_text == "first"


def test_speak_forced_bypasses_cooldown() -> None:
    client = _FakeClient()
    dv = DogVoice(client, cooldown_s=DEFAULT_COOLDOWN_S)
    dv.speak("first")
    assert dv.speak("forced", force=True) is not None
    assert client.last_text == "forced"


def test_respond_to_prediction_speaks_phrase() -> None:
    client = _FakeClient()
    dv = DogVoice(client, cooldown_s=0.0)
    pred = FakePred("food", "content", "sniff_ground")
    audio = dv.respond_to_prediction(pred, force=True)
    assert audio is not None
    assert dv.last_phrase is not None
    assert "food" in dv.last_phrase.lower() or "eat" in dv.last_phrase.lower() or "treat" in dv.last_phrase.lower()


def test_respond_to_bark() -> None:
    client = _FakeClient()
    dv = DogVoice(client, cooldown_s=0.0)
    assert dv.respond_to_bark("high", "negative", force=True) is not None
    assert dv.last_phrase is not None


def test_real_speech_client_constructs() -> None:
    client = SpeechClient(base_url="http://127.0.0.1:1", timeout=0.5)
    dv = DogVoice(client, cooldown_s=0.0)
    audio = dv.respond_to_prediction(FakePred("rest", "calm", "yawning"), force=True)
    assert audio is not None  # offline silent-wav fallback
    client.close()


def test_cooldown_reset_after_elapsed() -> None:
    client = _FakeClient()
    dv = DogVoice(client, cooldown_s=0.05)
    dv.speak("a")
    time.sleep(0.07)
    assert dv.can_speak()
