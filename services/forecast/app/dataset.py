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

from core.feature_spec import BASE_FEATURE_NAMES, SEQUENCE_LEN, vectorize  # noqa: E402
from core.modality_spec import modality_defaults  # noqa: E402


@dataclass
class TriadSample:
    sequence: list[list[float]]
    intent_id: str
    emotion_id: str
    behavior_id: str


def _modality_for_intent(intent: str) -> dict[str, float]:
    m = modality_defaults()
    if intent == "outside":
        m.update({"vision_yolo_dog_conf": 0.85, "ecg_stress": 0.7, "audio_arousal": 0.6, "imu_activity": 0.35})
    elif intent == "play":
        m.update({"vision_yolo_dog_conf": 0.92, "audio_arousal": 0.85, "audio_valence": 0.8, "audio_bark_prob": 0.75, "imu_activity": 0.8})
    elif intent == "food":
        m.update({"vision_yolo_dog_conf": 0.88, "audio_arousal": 0.35, "imu_activity": 0.25, "imu_posture_static": 0.7})
    elif intent == "avoid":
        m.update({"vision_yolo_dog_conf": 0.8, "ecg_stress": 0.85, "audio_valence": 0.1, "audio_bark_prob": 0.4, "imu_posture_static": 0.85})
    else:
        m.update({"vision_yolo_dog_conf": 0.75, "ecg_hr_norm": 0.35, "ecg_stress": 0.2, "imu_posture_static": 0.9, "imu_activity": 0.1})
    return m


def _synth_row(intent: str) -> tuple[dict, str, str, str]:
    r = random.random
    base = {name: r() * 0.2 for name in BASE_FEATURE_NAMES}
    base["dog_present"] = 1.0
    base.update(_modality_for_intent(intent))
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
