"""ONNX decode unit tests."""
from __future__ import annotations

import numpy as np

from core.ethogram_labels import behavior_labels, emotion_labels, intent_labels
from core.onnx_decode import decode_onnx_outputs


def test_decode_picks_argmax_intent() -> None:
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    intent = np.zeros(len(intents), dtype=np.float32)
    intent[intents.index("play")] = 0.92
    emotion = np.zeros(len(emotions), dtype=np.float32)
    emotion[0] = 0.7
    behavior = np.zeros(len(behaviors), dtype=np.float32)
    behavior[0] = 0.8
    out = decode_onnx_outputs(intent, emotion, behavior)
    assert out.intent == "play"
    assert out.confidence > 0.9
