"""Decode TriadNet ONNX softmax outputs into ethogram ids."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from core.ethogram_labels import behavior_labels, emotion_labels, intent_labels


@dataclass
class DecodedTriad:
    intent: str
    emotion: str
    behavior: str
    confidence: float
    intent_probs: dict[str, float]


def _argmax_probs(probs: np.ndarray, labels: list[str]) -> tuple[str, float, dict[str, float]]:
    flat = np.asarray(probs, dtype=np.float32).reshape(-1)
    idx = int(flat.argmax())
    label = labels[min(idx, len(labels) - 1)]
    prob_map = {labels[i]: float(flat[i]) for i in range(min(len(labels), len(flat)))}
    return label, float(flat[idx]), prob_map


def decode_onnx_outputs(
    intent_probs: np.ndarray,
    emotion_probs: np.ndarray,
    behavior_probs: np.ndarray,
) -> DecodedTriad:
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    intent, conf, intent_prob_map = _argmax_probs(intent_probs, intents)
    emotion, _, _ = _argmax_probs(emotion_probs, emotions)
    behavior, _, _ = _argmax_probs(behavior_probs, behaviors)
    return DecodedTriad(
        intent=intent,
        emotion=emotion,
        behavior=behavior,
        confidence=conf,
        intent_probs=intent_prob_map,
    )
