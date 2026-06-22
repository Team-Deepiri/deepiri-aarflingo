"""Load checkpoint and run inference."""
from __future__ import annotations

from pathlib import Path

import torch

from .labels import behavior_labels, emotion_labels, intent_labels
from .triad_model import TriadNet, TriadPrediction, predict_from_model

_MODEL: TriadNet | None = None
_MODEL_PATH: Path | None = None


def default_checkpoint() -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "artifacts" / "models" / "default" / "triad.pt"


def get_model() -> TriadNet | None:
    global _MODEL, _MODEL_PATH
    path = default_checkpoint()
    if _MODEL is not None and _MODEL_PATH == path:
        return _MODEL
    if not path.exists():
        return None
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    model = TriadNet(intents, emotions, behaviors)
    state = torch.load(path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    _MODEL = model
    _MODEL_PATH = path
    return model


def load_checkpoint(path: Path) -> TriadNet:
    global _MODEL, _MODEL_PATH
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    model = TriadNet(intents, emotions, behaviors)
    state = torch.load(path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    _MODEL = model
    _MODEL_PATH = path
    return model


def infer_sequence(frames: list[list[float]]) -> TriadPrediction:
    model = get_model()
    if model is None:
        from .triad_model import heuristic_predict

        names = [
            "dog_present", "bbox_cx", "bbox_cy", "bbox_w", "bbox_h", "motion",
            "velocity_x", "velocity_y", "gaze_door", "gaze_toy", "gaze_bowl",
            "gaze_center", "edge_left", "edge_right", "edge_top", "edge_bottom",
            "brightness", "contrast", "aspect_ratio", "arousal_proxy",
        ]
        last = frames[-1] if frames else [0.0] * len(names)
        feat = {names[i]: last[i] for i in range(min(len(names), len(last)))}
        return heuristic_predict(feat)
    return predict_from_model(model, frames)


def infer_batch(feature_rows: list[dict]) -> list[TriadPrediction]:
    from .features import vectorize
    from .triad_model import predict

    return [predict(row, [vectorize(row)]) for row in feature_rows]
