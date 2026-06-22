"""Coupling-aware loss helpers."""
from __future__ import annotations

import math


def coupling_loss(weight: float, epsilon: float = 1e-6) -> float:
    if weight <= 0:
        return 10.0
    return -math.log(weight + epsilon)


def confidence_penalty(confidence: float, threshold: float = 0.5) -> float:
    if confidence >= threshold:
        return 0.0
    return (threshold - confidence) ** 2


def total_loss(ce: float, couple_w: float, conf: float, lam: float = 0.3, mu: float = 0.1) -> float:
    return ce + lam * coupling_loss(couple_w) + mu * confidence_penalty(conf)
