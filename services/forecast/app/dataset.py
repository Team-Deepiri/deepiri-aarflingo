"""In-memory triad dataset from feature dicts."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TriadSample:
    features: dict
    intent_id: str
    emotion_id: str
    behavior_id: str


def load_demo_dataset() -> list[TriadSample]:
    return [
        TriadSample(
            features={"gaze_aversion": 0.2, "motion": 0.7},
            intent_id="solicit_play",
            emotion_id="excited",
            behavior_id="play_bow",
        ),
        TriadSample(
            features={"gaze_aversion": 0.8, "motion": 0.3},
            intent_id="avoid",
            emotion_id="fearful",
            behavior_id="tail_tucked",
        ),
    ]
