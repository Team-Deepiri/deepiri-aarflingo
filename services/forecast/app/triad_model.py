"""Minimal triad classifier (rule-based for smoke tests)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TriadPrediction:
    intent_id: str
    emotion_id: str
    behavior_id: str
    confidence: float


def predict(features: dict) -> TriadPrediction:
    ga = float(features.get("gaze_aversion", 0.0))
    motion = float(features.get("motion", 0.0))
    if ga > 0.6:
        return TriadPrediction("avoid", "fearful", "tail_tucked", 0.7)
    if motion > 0.5:
        return TriadPrediction("solicit_play", "excited", "play_bow", 0.75)
    return TriadPrediction("rest", "calm", "yawning", 0.55)
