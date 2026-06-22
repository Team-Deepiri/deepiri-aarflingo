"""Batch inference helper."""
from __future__ import annotations

from app.triad_model import TriadPrediction, predict


def infer_batch(feature_rows: list[dict]) -> list[TriadPrediction]:
    return [predict(row) for row in feature_rows]
