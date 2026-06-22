"""Anticipation label utilities (next-triad targets)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnticipationLabel:
    current_ts_ms: int
    horizon_ms: int
    target_intent: str
    target_emotion: str
    target_behavior: str


def build_anticipation(
    current_ts_ms: int,
    intent: str,
    emotion: str,
    behavior: str,
    horizon_ms: int = 500,
) -> AnticipationLabel:
    return AnticipationLabel(
        current_ts_ms=current_ts_ms,
        horizon_ms=horizon_ms,
        target_intent=intent,
        target_emotion=emotion,
        target_behavior=behavior,
    )
