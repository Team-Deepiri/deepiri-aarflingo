"""Training data from synthetic heuristics + feedback export."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.feature_spec import FEATURE_DIM, SEQUENCE_LEN, vectorize  # noqa: E402


@dataclass
class TriadSample:
    sequence: list[list[float]]
    intent_id: str
    emotion_id: str
    behavior_id: str


def _synth_row(intent: str) -> dict:
    r = random.random
    base = {name: r() * 0.2 for name in [
        "dog_present", "bbox_cx", "bbox_cy", "bbox_w", "bbox_h", "motion",
        "velocity_x", "velocity_y", "gaze_door", "gaze_toy", "gaze_bowl",
        "gaze_center", "edge_left", "edge_right", "edge_top", "edge_bottom",
        "brightness", "contrast", "aspect_ratio", "arousal_proxy",
    ]}
    base["dog_present"] = 1.0
    if intent == "outside":
        base.update({"gaze_door": 0.7 + r() * 0.2, "motion": 0.08 + r() * 0.1})
        return base, "outside", "anxious", "freeze"
    if intent == "play":
        base.update({"gaze_toy": 0.75 + r() * 0.2, "motion": 0.15 + r() * 0.15})
        return base, "play", "excited", "play_bow"
    if intent == "food":
        base.update({"gaze_bowl": 0.7 + r() * 0.2, "motion": 0.04 + r() * 0.05})
        return base, "food", "content", "sniff_ground"
    if intent == "avoid":
        base.update({"gaze_aversion": 0.8, "motion": 0.05})
        return base, "avoid", "fearful", "tail_tucked"
    base.update({"motion": 0.02})
    return base, "rest", "calm", "yawning"


def load_synthetic_dataset(n_per_class: int = 40) -> list[TriadSample]:
    random.seed(42)
    samples: list[TriadSample] = []
    for intent in ("outside", "play", "food", "avoid", "rest"):
        for _ in range(n_per_class):
            seq: list[list[float]] = []
            for _ in range(SEQUENCE_LEN):
                row, iid, eid, bid = _synth_row(intent)
                seq.append(vectorize(row))
            samples.append(TriadSample(seq, iid, eid, bid))
    return samples


def load_feedback_dataset(feedback_db: Path) -> list[TriadSample]:
    if not feedback_db.exists():
        return []
    rows = json.loads(feedback_db.read_text(encoding="utf-8"))
    out: list[TriadSample] = []
    for row in rows.get("samples", []):
        seq = row.get("sequence")
        if not seq:
            continue
        out.append(
            TriadSample(
                sequence=seq,
                intent_id=row["intent_id"],
                emotion_id=row["emotion_id"],
                behavior_id=row["behavior_id"],
            )
        )
    return out


def load_demo_dataset() -> list[TriadSample]:
    return load_synthetic_dataset(n_per_class=8)
