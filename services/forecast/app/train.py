"""Real PyTorch training loop."""
from __future__ import annotations

from pathlib import Path

import torch
import torch.nn.functional as F

from .dataset import TriadSample, load_feedback_dataset, load_synthetic_dataset
from .labels import behavior_labels, emotion_labels, intent_labels
from .losses import coupling_penalty
from .triad_model import TriadNet, flatten_sequence


def _label_index(labels: list[str], value: str) -> int:
    try:
        return labels.index(value)
    except ValueError:
        return 0


def train_epochs(
    epochs: int = 25,
    lr: float = 1e-3,
    out_path: Path | None = None,
    feedback_path: Path | None = None,
) -> dict:
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    model = TriadNet(intents, emotions, behaviors)
    opt = torch.optim.Adam(model.parameters(), lr=lr)

    samples = load_synthetic_dataset()
    if feedback_path:
        samples.extend(load_feedback_dataset(feedback_path))

    history: list[float] = []
    for _ in range(epochs):
        total = 0.0
        correct = 0
        for sample in samples:
            x = flatten_sequence(sample.sequence)
            li = _label_index(intents, sample.intent_id)
            le = _label_index(emotions, sample.emotion_id)
            lb = _label_index(behaviors, sample.behavior_id)
            logits_i, logits_e, logits_b = model(x)
            loss_i = F.cross_entropy(logits_i, torch.tensor([li]))
            loss_e = F.cross_entropy(logits_e, torch.tensor([le]))
            loss_b = F.cross_entropy(logits_b, torch.tensor([lb]))
            couple = coupling_penalty(sample.intent_id, sample.emotion_id, sample.behavior_id)
            loss = loss_i + loss_e + loss_b + couple
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += float(loss)
            if int(logits_i.argmax()) == li:
                correct += 1
        history.append(total / max(len(samples), 1))

    out = out_path or Path(__file__).resolve().parents[3] / "artifacts" / "models" / "default" / "triad.pt"
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out)
    acc = correct / max(len(samples), 1)
    return {"final_loss": history[-1], "intent_acc": acc, "path": str(out)}


def train_epoch() -> float:
    result = train_epochs(epochs=5)
    return float(result["final_loss"])
