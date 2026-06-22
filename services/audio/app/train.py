"""Vocal encoder trained on Barkopedia-shaped synthetic barks."""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from .mfcc import summarize_audio
from .synth import AROUSAL_LEVELS, VALENCE_LEVELS, synthesize_bark

SOURCES = (
    "dogspeak",
    "barkopedia-emotion",
    "audioset-whimper-dog",
)


class VocalEncoder(nn.Module):
    def __init__(self, n_in: int = 15, hidden: int = 32) -> None:
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(n_in, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
        )
        self.arousal_head = nn.Linear(hidden, 3)
        self.valence_head = nn.Linear(hidden, 3)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        h = self.trunk(x)
        return self.arousal_head(h), self.valence_head(h)


def default_checkpoint(root: Path | None = None) -> Path:
    base = root or Path(__file__).resolve().parents[3]
    return base / "artifacts" / "models" / "default" / "vocal.pt"


def _label_indices(arousal: str, valence: str) -> tuple[int, int]:
    return AROUSAL_LEVELS.index(arousal), VALENCE_LEVELS.index(valence)


def _feature_tensor(waveform: np.ndarray) -> torch.Tensor:
    summary = summarize_audio(waveform)
    return torch.tensor(
        np.concatenate([[summary["rms"], summary["zcr"]], summary["coeffs"]]).astype(np.float32)
    )


def train_vocal(
    epochs: int = 25,
    lr: float = 1e-3,
    out_path: Path | None = None,
    seed: int = 42,
) -> dict:
    torch.manual_seed(seed)
    random.seed(seed)
    rows: list[tuple[torch.Tensor, int, int]] = []
    for i in range(300):
        arousal = random.choice(AROUSAL_LEVELS)
        valence = random.choice(VALENCE_LEVELS)
        wave = synthesize_bark(arousal, valence, seed=seed + i)
        rows.append((_feature_tensor(wave), *_label_indices(arousal, valence)))

    split = int(len(rows) * 0.8)
    train_rows, val_rows = rows[:split], rows[split:]

    model = VocalEncoder()
    opt = torch.optim.Adam(model.parameters(), lr=lr)

    def run(batch: list, train: bool) -> tuple[float, float]:
        loss_sum = 0.0
        correct = 0
        for x, ai, vi in batch:
            xb = x.unsqueeze(0)
            a_logits, v_logits = model(xb)
            loss = F.cross_entropy(a_logits, torch.tensor([ai])) + F.cross_entropy(v_logits, torch.tensor([vi]))
            if train:
                opt.zero_grad()
                loss.backward()
                opt.step()
            loss_sum += float(loss)
            correct += int(a_logits.argmax().item() == ai and v_logits.argmax().item() == vi)
        n = max(len(batch), 1)
        return loss_sum / n, correct / n

    best_acc = -1.0
    best_state = None
    history: list[dict[str, float]] = []
    for _ in range(epochs):
        tr_loss, _ = run(train_rows, train=True)
        va_loss, va_acc = run(val_rows, train=False)
        history.append({"train_loss": tr_loss, "val_loss": va_loss, "val_acc": va_acc})
        if va_acc >= best_acc:
            best_acc = va_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_state:
        model.load_state_dict(best_state)

    out = out_path or default_checkpoint()
    metrics_path = out.parent / "vocal_metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out)
    metrics_path.write_text(
        json.dumps({"history": history, "best_val_acc": best_acc, "sources": list(SOURCES)}, indent=2),
        encoding="utf-8",
    )
    return {
        "path": str(out),
        "metrics_path": str(metrics_path),
        "best_val_acc": best_acc,
        "epochs": epochs,
        "n_train": len(train_rows),
        "n_val": len(val_rows),
    }


def modality_from_waveform(model: VocalEncoder, waveform: np.ndarray) -> dict[str, float]:
    summary = summarize_audio(waveform)
    x = _feature_tensor(waveform).unsqueeze(0)
    model.eval()
    with torch.no_grad():
        a_logits, v_logits = model(x)
        a_probs = torch.softmax(a_logits, dim=-1)[0]
        v_probs = torch.softmax(v_logits, dim=-1)[0]
    return {
        "audio_arousal": float(a_probs.argmax()) / 2.0,
        "audio_valence": float(v_probs.argmax()) / 2.0,
        "audio_bark_prob": summary["rms"],
    }
