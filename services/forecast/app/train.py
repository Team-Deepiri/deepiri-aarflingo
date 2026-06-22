"""Training loop stub over demo dataset."""
from __future__ import annotations

from app.dataset import load_demo_dataset
from app.losses import total_loss
from app.triad_model import predict


def train_epoch() -> float:
    samples = load_demo_dataset()
    losses: list[float] = []
    for sample in samples:
        pred = predict(sample.features)
        ce = 0.0 if pred.intent_id == sample.intent_id else 1.0
        couple_w = 0.9 if pred.behavior_id == sample.behavior_id else 0.1
        losses.append(total_loss(ce, couple_w, pred.confidence))
    return sum(losses) / len(losses)
