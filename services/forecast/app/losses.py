"""Coupling-aware loss helpers (ethogram-backed)."""
from __future__ import annotations

import json
from pathlib import Path

from core.triad_math import (
    DEFAULT_LAMBDA,
    DEFAULT_MU,
    confidence_penalty,
    coupling_loss_weight,
    total_loss_scalar,
)


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


def coupling_loss(weight: float) -> float:
    return coupling_loss_weight(weight)


def total_loss(ce: float, couple_w: float, conf: float, lam: float = DEFAULT_LAMBDA, mu: float = DEFAULT_MU) -> float:
    """Legacy scalar API — splits CE equally across three heads for tests."""
    third = ce / 3.0
    return total_loss_scalar(third, third, third, couple_w, conf, lam=lam, mu=mu)
