"""Review queue for low-confidence triad predictions."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReviewItem:
    event_id: str
    prediction: dict
    reason: str


def needs_review(prediction: dict, threshold: float = 0.5) -> bool:
    return float(prediction.get("confidence", 0.0)) < threshold


def enqueue(event_id: str, prediction: dict, threshold: float = 0.5) -> ReviewItem | None:
    if not needs_review(prediction, threshold):
        return None
    return ReviewItem(event_id=event_id, prediction=prediction, reason="low_confidence")
