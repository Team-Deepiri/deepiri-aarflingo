"""Vocal encoder training: real Barkopedia clips flow in + per-source held-out acc."""
from __future__ import annotations

import csv
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.train import _balanced_real_subset, train_vocal
from app.barkopedia import load_barkopedia


def _write_wav(path: Path, freq: float = 300.0) -> None:
    sr = 16000
    t = np.linspace(0, 0.2, int(sr * 0.2), dtype=np.float32)
    data = (np.sin(2 * np.pi * freq * t) * 0.5 * 32767).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(data.tobytes())


def _build_dataset(root: Path, per_combo: int = 4) -> None:
    combos = [("High", "Positive"), ("Low", "Negative"), ("Medium", "Neutral")]
    for idx, (arousal, valence) in enumerate(combos):
        for n in range(per_combo):
            _write_wav(
                root / "train" / "husky" / f"husky_train_{idx}{n:02d}.wav",
                freq=300.0 + idx * 100.0 + n * 10.0,
            )
    with (root / "husky_train_labels.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["audio_id", "arousal", "valence"])
        writer.writeheader()
        for idx, (arousal, valence) in enumerate(combos):
            for n in range(per_combo):
                writer.writerow(
                    {"audio_id": f"husky_train_{idx}{n:02d}", "arousal": arousal, "valence": valence}
                )


def test_balanced_real_subset_covers_combos(tmp_path: Path) -> None:
    _build_dataset(tmp_path, per_combo=3)
    samples = load_barkopedia(tmp_path)
    subset = _balanced_real_subset(samples, per_combo=2, seed=1)
    assert len(subset) == 6
    combos = {(s.arousal, s.valence) for s in subset}
    assert combos == {("high", "positive"), ("low", "negative"), ("medium", "neutral")}


def test_train_with_real_data_reports_source_acc(tmp_path: Path) -> None:
    _build_dataset(tmp_path, per_combo=4)
    out = train_vocal(epochs=2, out_path=tmp_path / "vocal.pt", data_dir=tmp_path, seed=7)
    assert out["real_clips"] > 0
    assert out["real_total_available"] == 12
    assert out["best_val_acc_by_source"].get("real") is not None, out
    # metrics JSON carries the same per-source accuracy
    import json

    metrics = json.loads(Path(out["metrics_path"]).read_text(encoding="utf-8"))
    assert "best_val_acc_by_source" in metrics