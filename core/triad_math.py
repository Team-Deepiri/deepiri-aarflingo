"""
IEB (Intent–Emotion–Behavior) triad math — canonical reference (NumPy/scalar).

See docs/MATH.md for notation. PyTorch helpers live in core/triad_torch.py.
"""
from __future__ import annotations

import math
from typing import Sequence

from core.feature_spec import FEATURE_DIM, SEQUENCE_LEN

EPSILON = 1e-6
DEFAULT_LAMBDA = 0.3
DEFAULT_MU = 0.1
FORBIDDEN_COUPLING_LOSS = 10.0


def coupling_loss_weight(weight: float, epsilon: float = EPSILON) -> float:
    if weight <= 0:
        return FORBIDDEN_COUPLING_LOSS
    return -math.log(weight + epsilon)


def confidence_penalty(confidence: float, threshold: float = 0.5) -> float:
    if confidence >= threshold:
        return 0.0
    return (threshold - confidence) ** 2


def total_loss_scalar(
    ce_intent: float,
    ce_emotion: float,
    ce_behavior: float,
    couple_weight: float,
    confidence: float = 1.0,
    lam: float = DEFAULT_LAMBDA,
    mu: float = DEFAULT_MU,
) -> float:
    ce = ce_intent + ce_emotion + ce_behavior
    return ce + lam * coupling_loss_weight(couple_weight) + mu * confidence_penalty(confidence)


def flatten_sequence_rows(frames: Sequence[Sequence[float]]) -> list[float]:
    padded = list(frames[-SEQUENCE_LEN:])
    while len(padded) < SEQUENCE_LEN:
        padded.insert(0, [0.0] * FEATURE_DIM)
    flat: list[float] = []
    for row in padded:
        row_list = list(row)
        flat.extend(row_list[:FEATURE_DIM] + [0.0] * max(0, FEATURE_DIM - len(row_list)))
    return flat


def numpy_softmax(logits: Sequence[float]) -> list[float]:
    import numpy as np

    z = np.asarray(logits, dtype=np.float64)
    z = z - z.max()
    ex = np.exp(z)
    p = ex / ex.sum()
    return p.tolist()


def numpy_cross_entropy(probs: Sequence[float], target: int) -> float:
    p = max(float(probs[target]), EPSILON)
    return -math.log(p)


def triad_confidence_scalar(
    intent_prob: float,
    emotion_prob: float,
    behavior_prob: float,
) -> float:
    return (intent_prob + emotion_prob + behavior_prob) / 3.0


def margin_confidence(probs: Sequence[float]) -> float:
    """Honest confidence: gap between top-1 and top-2 probability.

    Max-probability alone overstates confidence — a dog equidistant between
    door and toy yields two near-equal probabilities and a small margin.
    """
    sorted_p = sorted(float(p) for p in probs)
    if len(sorted_p) < 2:
        return 1.0 if len(sorted_p) == 1 else 0.0
    return sorted_p[-1] - sorted_p[-2]


def triad_margin_scalar(
    intent_probs: Sequence[float],
    emotion_probs: Sequence[float],
    behavior_probs: Sequence[float],
) -> float:
    return (
        margin_confidence(intent_probs)
        + margin_confidence(emotion_probs)
        + margin_confidence(behavior_probs)
    ) / 3.0
