"""Batched PyTorch training loop with IEB triad math."""
from __future__ import annotations

import json
import random
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from core.triad_math import DEFAULT_LAMBDA, coupling_loss_weight
from core.triad_torch import flatten_sequence_batch

from .dataset import TriadSample, load_feedback_dataset, load_synthetic_dataset
from .labels import behavior_labels, emotion_labels, intent_labels
from .losses import coupling_weight
from .triad_model import TriadNet


class TriadDataset(Dataset):
    def __init__(self, samples: list[TriadSample]) -> None:
        self.samples = samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> TriadSample:
        return self.samples[idx]


def _label_index(labels: list[str], value: str) -> int:
    try:
        return labels.index(value)
    except ValueError:
        return 0


def _collate(batch: list[TriadSample]) -> tuple[torch.Tensor, list[int], list[int], list[int], list[TriadSample]]:
    x = flatten_sequence_batch([s.sequence for s in batch])
    li = [_label_index(intent_labels(), s.intent_id) for s in batch]
    le = [_label_index(emotion_labels(), s.emotion_id) for s in batch]
    lb = [_label_index(behavior_labels(), s.behavior_id) for s in batch]
    return x, li, le, lb, batch


def _epoch_metrics(
    model: TriadNet,
    loader: DataLoader,
    opt: torch.optim.Optimizer | None,
    lam: float,
) -> dict[str, float]:
    intents = model.intent_labels
    total_loss = 0.0
    correct = 0
    n = 0
    for x, li, le, lb, samples in loader:
        logits_i, logits_e, logits_b = model(x)
        ti = torch.tensor(li)
        te = torch.tensor(le)
        tb = torch.tensor(lb)
        loss_i = F.cross_entropy(logits_i, ti)
        loss_e = F.cross_entropy(logits_e, te)
        loss_b = F.cross_entropy(logits_b, tb)
        couple = sum(
            coupling_loss_weight(coupling_weight(s.intent_id, s.emotion_id, s.behavior_id))
            for s in samples
        ) / max(len(samples), 1)
        loss = loss_i + loss_e + loss_b + lam * couple
        if opt is not None:
            opt.zero_grad()
            loss.backward()
            opt.step()
        total_loss += float(loss) * len(samples)
        correct += int((logits_i.argmax(dim=1) == ti).sum())
        n += len(samples)
    return {"loss": total_loss / max(n, 1), "intent_acc": correct / max(n, 1)}


def train_epochs(
    epochs: int = 25,
    lr: float = 1e-3,
    batch_size: int = 16,
    val_ratio: float = 0.2,
    lam: float = DEFAULT_LAMBDA,
    out_path: Path | None = None,
    feedback_path: Path | None = None,
    seed: int = 42,
) -> dict:
    random.seed(seed)
    torch.manual_seed(seed)

    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    model = TriadNet(intents, emotions, behaviors)
    opt = torch.optim.Adam(model.parameters(), lr=lr)

    samples = load_synthetic_dataset()
    if feedback_path:
        samples.extend(load_feedback_dataset(feedback_path))
    random.shuffle(samples)

    split = int(len(samples) * (1.0 - val_ratio))
    train_samples = samples[:split] or samples
    val_samples = samples[split:] or samples[-max(1, len(samples) // 5) :]

    train_loader = DataLoader(
        TriadDataset(train_samples),
        batch_size=batch_size,
        shuffle=True,
        collate_fn=_collate,
    )
    val_loader = DataLoader(
        TriadDataset(val_samples),
        batch_size=batch_size,
        shuffle=False,
        collate_fn=_collate,
    )

    history: list[dict[str, float]] = []
    best_val = -1.0
    best_state: dict | None = None

    for _ in range(epochs):
        train_m = _epoch_metrics(model, train_loader, opt, lam)
        val_m = _epoch_metrics(model, val_loader, None, lam)
        row = {"train_loss": train_m["loss"], "val_loss": val_m["loss"], "val_acc": val_m["intent_acc"]}
        history.append(row)
        if val_m["intent_acc"] >= best_val:
            best_val = val_m["intent_acc"]
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_state:
        model.load_state_dict(best_state)

    out = out_path or Path(__file__).resolve().parents[3] / "artifacts" / "models" / "default" / "triad.pt"
    metrics_out = out.parent / "train_metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out)
    metrics_out.write_text(json.dumps({"history": history, "best_val_acc": best_val}, indent=2), encoding="utf-8")

    last = history[-1] if history else {"train_loss": 0.0, "val_acc": 0.0}
    return {
        "final_loss": last["train_loss"],
        "intent_acc": last.get("val_acc", 0.0),
        "best_val_acc": best_val,
        "path": str(out),
        "metrics_path": str(metrics_out),
        "epochs": epochs,
        "n_train": len(train_samples),
        "n_val": len(val_samples),
    }


def train_epoch() -> float:
    result = train_epochs(epochs=5)
    return float(result["final_loss"])
