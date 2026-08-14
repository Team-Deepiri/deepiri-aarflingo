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
from .temporal_math import info_nce_loss, momentum_update, regression_loss, window_statistics
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
        total_loss += float(loss.detach()) * len(samples)
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


def _collate_temporal(batch: list[TriadSample], feature_dim: int) -> tuple[torch.Tensor, list[int], list[int], list[int]]:
    """(batch, SEQUENCE_LEN, FEATURE_DIM) tensor + label indices."""
    x = torch.tensor([s.sequence for s in batch], dtype=torch.float32)
    li = [_label_index(intent_labels(), s.intent_id) for s in batch]
    le = [_label_index(emotion_labels(), s.emotion_id) for s in batch]
    lb = [_label_index(behavior_labels(), s.behavior_id) for s in batch]
    assert x.ndim == 3 and x.size(-1) == feature_dim, f"temporal input must be (B, {SEQUENCE_LEN}, {feature_dim}), got {tuple(x.shape)}"
    return torch.as_tensor(x), li, le, lb


_AROUSAL_BY_INTENT = {
    0: 0.65,   # outside
    1: 0.85,   # play
    2: 0.3,    # food
    3: 0.75,   # avoid
    4: 0.15,   # rest
}
_VALENCE_BY_INTENT = {
    0: -0.3,   # outside -> anxious
    1: 0.8,    # play
    2: 0.5,    # food
    3: -0.8,   # avoid -> fearful
    4: 0.2,    # rest
}


def _regression_targets(li: list[int], x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Continuous arousal/valence targets per sample.

    Intent prior blended with the §9 window statistics of the batch's own
    audio-arousal / audio-valence columns, so the regression heads learn to
    follow the stream, not just the prior.
    """
    from core.feature_spec import FEATURE_NAMES

    a_idx = FEATURE_NAMES.index("audio_arousal") if "audio_arousal" in FEATURE_NAMES else None
    v_idx = FEATURE_NAMES.index("audio_valence") if "audio_valence" in FEATURE_NAMES else None
    ar, va = [], []
    for i, (seq, intent_idx) in enumerate(zip(x, li)):
        ar_prior = float(_AROUSAL_BY_INTENT.get(intent_idx, 0.5))
        va_prior = float(_VALENCE_BY_INTENT.get(intent_idx, 0.0))
        if x.ndim == 3 and x.size(0) > i:
            if a_idx is not None:
                ar_prior = 0.7 * ar_prior + 0.3 * window_statistics(seq[:, a_idx].tolist())["mean"]
            if v_idx is not None:
                va_prior = 0.7 * va_prior + 0.3 * window_statistics(seq[:, v_idx].tolist())["mean"]
        ar.append(ar_prior)
        va.append(va_prior)
    return torch.tensor(ar, dtype=torch.float32), torch.tensor(va, dtype=torch.float32)


def train_temporal_epochs(
    epochs: int = 25,
    lr: float = 1e-3,
    batch_size: int = 16,
    val_ratio: float = 0.2,
    lam: float = DEFAULT_LAMBDA,
    out_path: Path | None = None,
    feedback_path: Path | None = None,
    seed: int = 42,
    contrastive_pre: int = 3,
) -> dict:
    """Train the BiLSTM+attention TriadNetTemporal backbone (§9).

    Uses the §9 temporal math explicitly:
      * window_statistics summarizes each sequence row (used to derive the
        continuous arousal/valence regression targets from the audio rows);
      * regression_loss on those heads, combined with the triad CE loss;
      * MoCo-style info_nce_loss + momentum_update for `contrastive_pre`
        epochs of unsupervised pretraining on the encoder.
    """
    import torch.nn.functional as F
    from .temporal_math import TriadNetTemporal

    random.seed(seed)
    torch.manual_seed(seed)

    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    feature_dim = torch.as_tensor(load_synthetic_dataset(1)[0].sequence).size(-1)
    model = TriadNetTemporal(feature_dim, intents, emotions, behaviors)

    samples = load_synthetic_dataset()
    if feedback_path:
        samples.extend(load_feedback_dataset(feedback_path))
    random.shuffle(samples)

    split = int(len(samples) * (1.0 - val_ratio))
    train_samples = samples[:split] or samples
    val_samples = samples[split:] or samples[-max(1, len(samples) // 5) :]

    train_loader = DataLoader(TriadDataset(train_samples), batch_size=batch_size, shuffle=True, collate_fn=lambda b: _collate_temporal(b, feature_dim))
    val_loader = DataLoader(TriadDataset(val_samples), batch_size=batch_size, shuffle=False, collate_fn=lambda b: _collate_temporal(b, feature_dim))

    # MoCo-style momentum contrastive pretraining (info_nce_loss + momentum_update).
    if contrastive_pre > 0:
        key_encoder = TriadNetTemporal(feature_dim, intents, emotions, behaviors)
        key_encoder.load_state_dict(model.state_dict())
        key_encoder.eval()
        key_opt = torch.optim.Adam(key_encoder.parameters(), lr=lr)
        for _ in range(contrastive_pre):
            for x, *_ in train_loader:
                query = model.encoder(x)
                with torch.no_grad():
                    key = key_encoder.encoder(x)
                que = F.normalize(query, dim=-1)
                key_n = F.normalize(key, dim=-1)
                neg = key_n[torch.randperm(key_n.size(0))] if key_n.size(0) > 1 else key_n
                loss = info_nce_loss(que, key_n, neg)
                key_opt.zero_grad()
                loss.backward()
                key_opt.step()
                momentum_update(key_encoder, model)

    opt = torch.optim.Adam(model.parameters(), lr=lr)
    history: list[dict[str, float]] = []
    best_val = -1.0
    best_state: dict | None = None

    for _ in range(epochs):
        total_loss = 0.0
        correct = 0
        n = 0
        for x, li, le, lb in train_loader:
            li_t = torch.tensor(li)
            le_t = torch.tensor(le)
            lb_t = torch.tensor(lb)
            li_raw, le_raw, lb_raw, arousal, valence = model(x)
            ce = F.cross_entropy(li_raw, li_t) + F.cross_entropy(le_raw, le_t) + F.cross_entropy(lb_raw, lb_t)
            ar_t, va_t = _regression_targets(li, x)
            reg = regression_loss(arousal, valence, ar_t, va_t)
            loss = ce + reg
            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += float(loss.detach()) * x.size(0)
            correct += int((li_raw.argmax(dim=1) == li_t).sum())
            n += x.size(0)
        val_correct = 0
        val_n = 0
        for x, li, *_ in val_loader:
            with torch.no_grad():
                li_raw, *_ = model(x)
            val_correct += int((li_raw.argmax(dim=1) == torch.tensor(li)).sum())
            val_n += x.size(0)
        val_acc = val_correct / max(val_n, 1)
        row = {"train_loss": total_loss / max(n, 1), "val_acc": val_acc}
        history.append(row)
        if val_acc >= best_val:
            best_val = val_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_state:
        model.load_state_dict(best_state)

    out = out_path or Path(__file__).resolve().parents[3] / "artifacts" / "models" / "default" / "triad_temporal.pt"
    metrics_out = out.parent / "train_temporal_metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out)
    metrics_out.write_text(json.dumps({"history": history, "best_val_acc": best_val}, indent=2), encoding="utf-8")

    last = history[-1] if history else {"train_loss": 0.0, "val_acc": 0.0}
    return {
        "variant": "temporal",
        "final_loss": last["train_loss"],
        "intent_acc": last.get("val_acc", 0.0),
        "best_val_acc": best_val,
        "path": str(out),
        "metrics_path": str(metrics_out),
        "epochs": epochs,
        "n_train": len(train_samples),
        "n_val": len(val_samples),
    }
