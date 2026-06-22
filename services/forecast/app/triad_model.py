"""PyTorch triad classifier with temporal MLP backbone."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn

import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.feature_spec import FEATURE_DIM, SEQUENCE_LEN  # noqa: E402
from core.triad_torch import flatten_sequence_tensor, triad_confidence


@dataclass
class TriadPrediction:
    intent_id: str
    emotion_id: str
    behavior_id: str
    confidence: float
    intent_probs: dict[str, float] | None = None


class TriadNet(nn.Module):
    def __init__(
        self,
        intent_labels: list[str],
        emotion_labels: list[str],
        behavior_labels: list[str],
        hidden: int = 128,
    ) -> None:
        super().__init__()
        input_dim = FEATURE_DIM * SEQUENCE_LEN
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.intent_head = nn.Linear(hidden, len(intent_labels))
        self.emotion_head = nn.Linear(hidden, len(emotion_labels))
        self.behavior_head = nn.Linear(hidden, len(behavior_labels))
        self.intent_labels = intent_labels
        self.emotion_labels = emotion_labels
        self.behavior_labels = behavior_labels

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        h = self.backbone(x)
        return self.intent_head(h), self.emotion_head(h), self.behavior_head(h)


def flatten_sequence(frames: list[list[float]]) -> torch.Tensor:
    return flatten_sequence_tensor(frames)


def predict_from_model(
    model: TriadNet,
    frames: list[list[float]],
) -> TriadPrediction:
    model.eval()
    with torch.no_grad():
        logits_i, logits_e, logits_b = model(flatten_sequence(frames))
        pi = torch.softmax(logits_i, dim=-1)[0]
        pe = torch.softmax(logits_e, dim=-1)[0]
        pb = torch.softmax(logits_b, dim=-1)[0]
    ii = int(pi.argmax())
    ei = int(pe.argmax())
    bi = int(pb.argmax())
    conf = triad_confidence(pi, pe, pb, ii, ei, bi)
    return TriadPrediction(
        intent_id=model.intent_labels[ii],
        emotion_id=model.emotion_labels[ei],
        behavior_id=model.behavior_labels[bi],
        confidence=conf,
        intent_probs={model.intent_labels[j]: float(pi[j]) for j in range(len(model.intent_labels))},
    )


def heuristic_predict(features: dict) -> TriadPrediction:
    """Rule fallback when no checkpoint — uses gaze zones + motion."""
    door = float(features.get("gaze_door", 0))
    toy = float(features.get("gaze_toy", 0))
    bowl = float(features.get("gaze_bowl", 0))
    motion = float(features.get("motion", 0))
    aversion = float(features.get("gaze_aversion", 0))

    if door > 0.45 and motion > 0.03:
        return TriadPrediction("outside", "anxious", "freeze", 0.72)
    if toy > 0.45 and motion > 0.05:
        return TriadPrediction("play", "excited", "play_bow", 0.78)
    if bowl > 0.45:
        return TriadPrediction("food", "content", "sniff_ground", 0.7)
    if aversion > 0.6:
        return TriadPrediction("avoid", "fearful", "tail_tucked", 0.68)
    if motion > 0.12:
        return TriadPrediction("explore", "excited", "sniff_ground", 0.6)
    return TriadPrediction("rest", "calm", "yawning", 0.55)


def predict(features: dict, frames: list[list[float]] | None = None) -> TriadPrediction:
    from .infer import get_model

    model = get_model()
    if model is None:
        return heuristic_predict(features)
    seq = frames or []
    if not seq:
        from .features import vectorize

        seq = [vectorize(features)]
    return predict_from_model(model, seq)
