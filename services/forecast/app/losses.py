"""Coupling-aware loss helpers."""
from __future__ import annotations

import json
import math
from pathlib import Path


def _matrix_path() -> Path:
    return Path(__file__).resolve().parents[3] / "ethogram" / "coupling-matrix.json"


def coupling_weight(intent: str, emotion: str, behavior: str) -> float:
    data = json.loads(_matrix_path().read_text(encoding="utf-8"))
    for triple in data.get("triples", []):
        if triple["intent"] == intent and triple["emotion"] == emotion and triple["behavior"] == behavior:
            return float(triple.get("weight", 0))
    return 0.0


def coupling_penalty(intent: str, emotion: str, behavior: str) -> float:
    return coupling_loss(coupling_weight(intent, emotion, behavior))


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
