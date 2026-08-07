from __future__ import annotations

import csv
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.barkopedia import class_counts, load_barkopedia, read_wav  # noqa: E402


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


def _build_dataset(root: Path) -> None:
    _write_wav(root / "train/husky/husky_train_00000.wav", 300.0)
    _write_wav(root / "train/husky/husky_train_00001.wav", 400.0)
    _write_wav(root / "train/shiba/shiba_train_00000.wav", 500.0)
    with (root / "husky_train_labels.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["audio_id", "arousal", "valence"])
        writer.writeheader()
        writer.writerow({"audio_id": "husky_train_00000", "arousal": "High", "valence": "Positive"})
        writer.writerow({"audio_id": "husky_train_00001", "arousal": "Low", "valence": "Negative"})
    with (root / "shiba_train_labels.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["audio_id", "arousal", "valence"])
        writer.writeheader()
        writer.writerow({"audio_id": "shiba_train_00000", "arousal": "Medium", "valence": "Neutral"})


def test_read_wav_pcm16() -> None:
    p = Path("/tmp/aarf_test_wav_000.wav")
    _write_wav(p)
    audio = read_wav(p)
    assert audio.dtype == np.float32
    assert audio.size > 1000
    assert float(np.abs(audio).max()) > 0.1


def test_load_barkopedia_finds_labeled_clips(tmp_path: Path) -> None:
    _build_dataset(tmp_path)
    samples = load_barkopedia(tmp_path)
    assert len(samples) == 3
    assert {s.arousal for s in samples} == {"high", "low", "medium"}
    assert {s.valence for s in samples} == {"positive", "negative", "neutral"}


def test_load_barkopedia_respects_max_samples(tmp_path: Path) -> None:
    _build_dataset(tmp_path)
    samples = load_barkopedia(tmp_path, max_samples=2)
    assert len(samples) <= 2


def test_load_barkopedia_empty_dir(tmp_path: Path) -> None:
    assert load_barkopedia(tmp_path) == []


def test_class_counts(tmp_path: Path) -> None:
    _build_dataset(tmp_path)
    counts = class_counts(load_barkopedia(tmp_path))
    assert counts["arousal"]["high"] == 1
    assert counts["valence"]["neutral"] == 1
