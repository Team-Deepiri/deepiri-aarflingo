"""Voice plan for talking to the dog.

Given a TriadNet prediction (or a bark arousal/valence reading) the system
picks a short spoken line and synthesizes it through deepiri-speech. A
cooldown prevents the system from chattering at the dog every frame.
"""
from __future__ import annotations

import time
from typing import Any

from .speech_client import SpeechClient

DEFAULT_COOLDOWN_S = 20.0

# Spoken lines keyed by (intent, emotion). Kept short — dogs parse tone,
# so the prosody (positive/calm) matters more than the words.
_PHRASES: dict[tuple[str, str], list[str]] = {
    ("outside", "anxious"): [
        "Hey buddy, the door is open. Let's go out.",
        "Ready for your walk, buddy? Let's go.",
    ],
    ("outside", "excited"): [
        "Outside time! Let's go, good dog.",
        "Wanna go out? Let's go, buddy.",
    ],
    ("play", "excited"): [
        "Who's a good dog? Let's play!",
        "Toy time, buddy. Get it!",
    ],
    ("food", "content"): [
        "Treat time, good dog!",
        "Time to eat, buddy.",
    ],
    ("food", "hungry"): [
        "Your food is ready, good dog.",
    ],
    ("avoid", "fearful"): [
        "It's okay, buddy. You're safe.",
        "Easy, easy. I'm right here.",
    ],
    ("explore", "excited"): [
        "What did you find, buddy?",
        "Go sniff it out, good dog.",
    ],
    ("rest", "calm"): [
        "Good boy. Settle in.",
        "You rest, buddy. I'm here.",
    ],
}

_DEFAULT_PHRASES: list[str] = [
    "Good dog, buddy.",
    "I see you, buddy.",
]

_BARK_RESPONSES: dict[tuple[str, str], list[str]] = {
    ("high", "negative"): [
        "Hey buddy, it's okay. You're safe with me.",
        "Easy, easy. What's wrong, buddy?",
    ],
    ("high", "positive"): [
        "Who's a good dog! I hear you!",
        "Yes! Good dog!",
    ],
    ("high", "neutral"): [
        "I hear you, buddy.",
        "What is it, boy?",
    ],
    ("medium", "negative"): [
        "It's okay, buddy. I'm right here.",
    ],
    ("medium", "positive"): [
        "Good boy. Good bark!",
    ],
    ("low", "negative"): [
        "I've got you, buddy. You're safe.",
    ],
    ("low", "positive"): [
        "Good dog. Come here, buddy.",
    ],
}

_BARK_DEFAULT: list[str] = [
    "I hear you, buddy.",
    "I'm here, buddy.",
]


def phrase_for(pred: Any) -> str:
    """Pick a spoken line for a TriadPrediction-like object."""
    intent = getattr(pred, "intent_id", None) or ""
    emotion = getattr(pred, "emotion_id", None) or ""
    lines = _PHRASES.get((intent, emotion))
    if lines is None:
        lines = _PHRASES.get((intent, "")) or _DEFAULT_PHRASES
    return _pick(lines, intent, emotion)


def response_to_bark(arousal: str, valence: str) -> str:
    """Acknowledge a bark with a spoken line matched to arousal/valence."""
    lines = _BARK_RESPONSES.get((arousal, valence)) or _BARK_DEFAULT
    return _pick(lines, arousal, valence)


def _pick(lines: list[str], a: str, b: str) -> str:
    idx = abs(hash(f"{a}:{b}")) % len(lines)
    return lines[idx]


class DogVoice:
    def __init__(self, client: SpeechClient, cooldown_s: float = DEFAULT_COOLDOWN_S) -> None:
        self.client = client
        self.cooldown_s = cooldown_s
        self._last_spoken_at: float = 0.0
        self._last_phrase: str | None = None
        self._last_audio: bytes | None = None

    def speak(self, text: str, voice: str | None = None, force: bool = False) -> bytes | None:
        """Synthesize + return audio bytes, respecting the cooldown unless forced."""
        if not force and not self.can_speak():
            return None
        audio = self.client.synthesize(text, voice=voice)
        if audio:
            self._last_spoken_at = time.monotonic()
            self._last_phrase = text
            self._last_audio = audio
        return audio

    def respond_to_prediction(self, pred: Any, voice: str | None = None, force: bool = False) -> bytes | None:
        text = phrase_for(pred)
        return self.speak(text, voice=voice, force=force)

    def respond_to_bark(self, arousal: str, valence: str, voice: str | None = None, force: bool = False) -> bytes | None:
        text = response_to_bark(arousal, valence)
        return self.speak(text, voice=voice, force=force)

    def can_speak(self) -> bool:
        return (time.monotonic() - self._last_spoken_at) >= self.cooldown_s

    @property
    def last_phrase(self) -> str | None:
        return self._last_phrase

    @property
    def last_audio(self) -> bytes | None:
        return self._last_audio
