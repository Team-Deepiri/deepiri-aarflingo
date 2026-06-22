"""Train vitals encoder on PhysioZoo-shaped ECG + Mendeley-shaped IMU synthesis."""
from __future__ import annotations

import json
import random
from pathlib import Path

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from .ecg import DOG_HR_BPM_RANGE, DOG_SDNN_MS_RANGE, ecg_window_features, synthesize_ecg
from .imu import POSTURES, imu_window_features, synthesize_imu_window
from .model import VitalsEncoder, default_checkpoint, features_to_tensor


class VitalsSample(Dataset):
    def __init__(self, rows: list[tuple[torch.Tensor, int, float]]) -> None:
        self.rows = rows

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int, float]:
        return self.rows[idx]


def _build_samples(n: int = 400, seed: int = 42) -> list[tuple[torch.Tensor, int, float]]:
    random.seed(seed)
    rows: list[tuple[torch.Tensor, int, float]] = []
    for i in range(n):
        stressed = i % 2 == 0
        hr = random.uniform(95.0, 125.0) if stressed else random.uniform(60.0, 90.0)
        sdnn = random.uniform(15.0, 35.0) if stressed else random.uniform(45.0, 80.0)
        ecg = synthesize_ecg(hr_bpm=hr, sdnn_ms=sdnn, seed=seed + i)
        ecg_feats = ecg_window_features(ecg)
        posture = "walking" if stressed else random.choice(("standing", "sitting", "lying"))
        imu = synthesize_imu_window(posture=posture, seed=seed + i + 1000)
        imu_feats = imu_window_features(imu)
        x = features_to_tensor(ecg_feats, imu_feats)
        label = 1 if stressed else 0
        stress_target = ecg_feats["stress_score"]
        rows.append((x, label, stress_target))
    return rows


def train_vitals(
    epochs: int = 20,
    lr: float = 1e-3,
    out_path: Path | None = None,
    seed: int = 42,
) -> dict:
    torch.manual_seed(seed)
    samples = _build_samples(seed=seed)
    split = int(len(samples) * 0.8)
    train_rows = samples[:split]
    val_rows = samples[split:]

    model = VitalsEncoder()
    opt = torch.optim.Adam(model.parameters(), lr=lr)

    def run_batch(rows: list[tuple[torch.Tensor, int, float]], train: bool) -> tuple[float, float]:
        total_loss = 0.0
        correct = 0
        for x, label, stress_tgt in rows:
            xb = x.unsqueeze(0)
            out = model(xb)
            cls_logits = out[0, :2]
            stress_pred = out[0, 2]
            loss = F.cross_entropy(cls_logits.unsqueeze(0), torch.tensor([label])) + F.mse_loss(
                torch.sigmoid(stress_pred), torch.tensor(stress_tgt)
            )
            if train:
                opt.zero_grad()
                loss.backward()
                opt.step()
            total_loss += float(loss)
            correct += int(cls_logits.argmax().item() == label)
        n = max(len(rows), 1)
        return total_loss / n, correct / n

    best_acc = -1.0
    best_state = None
    history: list[dict[str, float]] = []
    for _ in range(epochs):
        tr_loss, tr_acc = run_batch(train_rows, train=True)
        va_loss, va_acc = run_batch(val_rows, train=False)
        history.append({"train_loss": tr_loss, "val_loss": va_loss, "val_acc": va_acc})
        if va_acc >= best_acc:
            best_acc = va_acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    if best_state:
        model.load_state_dict(best_state)

    out = out_path or default_checkpoint()
    metrics_path = out.parent / "vitals_metrics.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), out)
    metrics_path.write_text(
        json.dumps(
            {
                "history": history,
                "best_val_acc": best_acc,
                "sources": ["physiozoo-dog-ecg", "mendeley-dog-posture-imu", "mendeley-dog-behavior-imu"],
                "hr_bpm_range": DOG_HR_BPM_RANGE,
                "sdnn_ms_range": DOG_SDNN_MS_RANGE,
                "imu_postures": list(POSTURES),
            },
            indent=2,
        ),
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
