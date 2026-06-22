"""Baseline metric aggregation for a dog session."""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class BaselineMetrics:
    resting_heart_rate_bpm: float
    tail_angle_mean_deg: float
    gaze_aversion_mean: float = 0.2
    arousal_index: float = 0.15


@dataclass
class Baseline:
    baseline_id: str
    dog_id: str
    captured_at: str
    metrics: BaselineMetrics

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


def record_baseline(dog_id: str, hr_bpm: float, tail_deg: float) -> Baseline:
    return Baseline(
        baseline_id=str(uuid.uuid4()),
        dog_id=dog_id,
        captured_at=datetime.now(timezone.utc).isoformat(),
        metrics=BaselineMetrics(
            resting_heart_rate_bpm=hr_bpm,
            tail_angle_mean_deg=tail_deg,
        ),
    )
