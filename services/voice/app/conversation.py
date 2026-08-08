"""ConversationEngine — bidirectional dog conversation loop.

The engine sits between the perception / forecast pipeline and the voice
synthesizer. It:

1. Listens to TriadNet predictions and decides *what* to say.
2. Keeps a short response window after each utterance.
3. Receives BarkEvents from the mic listener during that window.
4. Scores the outcome (did the dog respond? positive/negative valence?).
5. Updates per-phrase weights so that over time the system learns which
   phrases actually *move* your specific dog.

Phrase weights are persisted to ``artifacts/voice/phrase_weights.json`` so
learning survives restarts.

Architecture::

    TriadNet ──► on_prediction() ──► best_phrase_for() ──► DogVoice.speak()
                                              ▲                    │
                               phrase_weights │                    │ sets _pending
                                              │                    ▼
                    MicListener ──► on_bark() ──► _score_outcome() ──► update weights
                                                        │
                                                        ▼
                                               FeedbackStore.log_voice_outcome()

Weight update rule (simple exponential moving average, no RL required):

    w_new = (1 - α) * w_old + α * reward

    reward = +1.0  if bark.valence == "positive"  within window
    reward =  0.0  if no bark within window (silence = neutral)
    reward = -0.5  if bark.valence == "negative" within window

α = LEARNING_RATE (default 0.15)
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .dog_voice import DogVoice, _PHRASES, _DEFAULT_PHRASES, phrase_for, _pick
from .mic_listener import BarkEvent

# ── constants ──────────────────────────────────────────────────────────────
RESPONSE_WINDOW_S = 8.0     # seconds to wait for a bark after speaking
LEARNING_RATE = 0.15        # EMA alpha for weight updates
WEIGHT_FLOOR = 0.05         # phrase weight never drops below this
WEIGHT_CEIL = 2.0           # phrase weight never rises above this
DEFAULT_WEIGHT = 1.0        # initial weight for every phrase

REWARD_POSITIVE = +1.0
REWARD_SILENCE = 0.0
REWARD_NEGATIVE = -0.5


@dataclass
class VoiceOutcome:
    """One completed utterance + dog response."""
    ts: float
    phrase: str
    intent: str
    emotion: str
    responded: bool
    bark_arousal: str | None
    bark_valence: str | None
    reward: float


@dataclass
class _PendingUtterance:
    phrase: str
    intent: str
    emotion: str
    spoken_at: float
    outcome_logged: bool = False


class ConversationEngine:
    """Manages the speak → listen → learn cycle for a single dog session.

    Parameters
    ----------
    voice:
        A DogVoice instance (wraps SpeechClient + cooldown).
    store:
        Optional FeedbackStore for persisting voice outcomes.
    weights_path:
        JSON file for persisting phrase weights across restarts.
    response_window_s:
        How long (seconds) after speaking to wait for a bark response.
    learning_rate:
        EMA alpha applied to phrase weight on each outcome.
    """

    def __init__(
        self,
        voice: DogVoice,
        store: Any | None = None,
        weights_path: Path | None = None,
        response_window_s: float = RESPONSE_WINDOW_S,
        learning_rate: float = LEARNING_RATE,
    ) -> None:
        self.voice = voice
        self.store = store
        self.weights_path = weights_path or Path(__file__).resolve().parents[3] / "artifacts" / "voice" / "phrase_weights.json"
        self.response_window_s = response_window_s
        self.learning_rate = learning_rate

        self._weights: dict[str, float] = {}
        self._pending: _PendingUtterance | None = None
        self._outcomes: list[VoiceOutcome] = []
        self._lock = threading.Lock()

        self._load_weights()
        # Start the window-expiry background thread
        self._stop = threading.Event()
        self._expiry_thread = threading.Thread(
            target=self._expiry_loop, daemon=True, name="aarf-conv-expiry"
        )
        self._expiry_thread.start()

    # ── public API ──────────────────────────────────────────────────────────

    def on_prediction(self, pred: Any) -> dict | None:
        """Called by the runtime engine on each TriadNet prediction.

        Returns a dict with phrase + audio bytes metadata if something was
        spoken, or None if cooldown / gate suppressed it.
        """
        audio = self.voice.respond_to_prediction(pred, force=False)
        if not audio:
            return None
        phrase = self.voice.last_phrase or phrase_for(pred)
        intent = getattr(pred, "intent_id", "") or ""
        emotion = getattr(pred, "emotion_id", "") or ""
        with self._lock:
            # Close any un-answered previous window as silence
            if self._pending and not self._pending.outcome_logged:
                self._close_window(bark=None)
            self._pending = _PendingUtterance(
                phrase=phrase,
                intent=intent,
                emotion=emotion,
                spoken_at=time.monotonic(),
            )
        return {"phrase": phrase, "audio_bytes": len(audio)}

    def on_bark(self, event: BarkEvent) -> dict | None:
        """Called when the mic listener detects and classifies a bark.

        If there is an open response window the bark closes it and the
        phrase weight is updated. Returns the outcome dict or None.
        """
        with self._lock:
            pending = self._pending
            if pending is None or pending.outcome_logged:
                return None
            elapsed = event.ts - pending.spoken_at
            if elapsed > self.response_window_s:
                return None  # too late; expiry loop will handle it
            return self._close_window(bark=event)

    def best_phrase_for(self, pred: Any) -> str:
        """Return the highest-weight phrase for this prediction.

        Falls back to the default round-robin picker when all weights are
        equal (i.e. no learning has happened yet).
        """
        intent = getattr(pred, "intent_id", "") or ""
        emotion = getattr(pred, "emotion_id", "") or ""
        candidates = (
            _PHRASES.get((intent, emotion))
            or _PHRASES.get((intent, ""))
            or _DEFAULT_PHRASES
        )
        if len(candidates) == 1:
            return candidates[0]
        weights = [self._weights.get(p, DEFAULT_WEIGHT) for p in candidates]
        total = sum(weights)
        if total <= 0 or all(w == weights[0] for w in weights):
            return _pick(candidates, intent, emotion)
        # Weighted selection — deterministic: pick highest weight
        best_idx = max(range(len(weights)), key=lambda i: weights[i])
        return candidates[best_idx]

    def recent_outcomes(self, n: int = 20) -> list[dict]:
        with self._lock:
            return [
                {
                    "ts": o.ts,
                    "phrase": o.phrase,
                    "intent": o.intent,
                    "emotion": o.emotion,
                    "responded": o.responded,
                    "bark_arousal": o.bark_arousal,
                    "bark_valence": o.bark_valence,
                    "reward": o.reward,
                    "phrase_weight": round(self._weights.get(o.phrase, DEFAULT_WEIGHT), 4),
                }
                for o in self._outcomes[-n:]
            ]

    def phrase_weights(self) -> dict[str, float]:
        with self._lock:
            return dict(self._weights)

    def stop(self) -> None:
        self._stop.set()
        self._expiry_thread.join(timeout=2.0)

    # ── internal ────────────────────────────────────────────────────────────

    def _close_window(self, bark: BarkEvent | None) -> dict | None:
        """Must be called with self._lock held."""
        pending = self._pending
        if pending is None or pending.outcome_logged:
            return None
        pending.outcome_logged = True

        if bark is None:
            reward = REWARD_SILENCE
            responded = False
            arousal = valence = None
        else:
            responded = True
            arousal = bark.arousal
            valence = bark.valence
            if valence == "positive":
                reward = REWARD_POSITIVE
            elif valence == "negative":
                reward = REWARD_NEGATIVE
            else:
                reward = REWARD_SILENCE

        self._update_weight(pending.phrase, reward)

        outcome = VoiceOutcome(
            ts=time.time(),
            phrase=pending.phrase,
            intent=pending.intent,
            emotion=pending.emotion,
            responded=responded,
            bark_arousal=arousal,
            bark_valence=valence,
            reward=reward,
        )
        self._outcomes.append(outcome)

        if self.store is not None:
            try:
                self.store.log_voice_outcome(
                    phrase=pending.phrase,
                    intent=pending.intent,
                    emotion=pending.emotion,
                    responded=responded,
                    bark_arousal=arousal,
                    bark_valence=valence,
                    reward=reward,
                )
            except Exception:
                pass  # don't let a DB error interrupt the loop

        self._save_weights()

        return {
            "phrase": pending.phrase,
            "responded": responded,
            "bark_arousal": arousal,
            "bark_valence": valence,
            "reward": reward,
            "phrase_weight": round(self._weights.get(pending.phrase, DEFAULT_WEIGHT), 4),
        }

    def _update_weight(self, phrase: str, reward: float) -> None:
        current = self._weights.get(phrase, DEFAULT_WEIGHT)
        # EMA toward the target (reward mapped to [0, 1] space scaled by ceil)
        target = (reward + 1.0) / 2.0 * WEIGHT_CEIL  # map [-0.5..1] → [0.25..2]
        updated = (1.0 - self.learning_rate) * current + self.learning_rate * target
        self._weights[phrase] = max(WEIGHT_FLOOR, min(WEIGHT_CEIL, updated))

    def _expiry_loop(self) -> None:
        """Periodically close un-answered windows as silence outcomes."""
        while not self._stop.is_set():
            time.sleep(0.5)
            now = time.monotonic()
            with self._lock:
                p = self._pending
                if p and not p.outcome_logged:
                    if now - p.spoken_at > self.response_window_s:
                        self._close_window(bark=None)

    def _load_weights(self) -> None:
        if self.weights_path.is_file():
            try:
                data = json.loads(self.weights_path.read_text(encoding="utf-8"))
                self._weights = {k: float(v) for k, v in data.items()}
            except Exception:
                self._weights = {}
        else:
            self._weights = {}

    def _save_weights(self) -> None:
        try:
            self.weights_path.parent.mkdir(parents=True, exist_ok=True)
            self.weights_path.write_text(
                json.dumps(self._weights, indent=2, sort_keys=True), encoding="utf-8"
            )
        except Exception:
            pass
