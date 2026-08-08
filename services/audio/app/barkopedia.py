"""Load real Barkopedia clips (audio_id, arousal, valence) into training.

Dataset layout (ArlingtonCL2/BarkopediaDogEmotionClassification_Data):

    husky_train_labels.csv        # audio_id,arousal,valence
    shiba_train_labels.csv
    train/husky/husky_train_*.wav
    train/shiba/shiba_train_*.wav
    validation/{husky,shiba}/*.wav
    test/{husky,shiba}/*.wav

Fetch with: ./scripts/fetch_public_datasets.sh --barkopedia
"""
from __future__ import annotations

import csv
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .synth import AROUSAL_LEVELS, VALENCE_LEVELS

TARGET_SR = 16000


@dataclass
class BarkSample:
    waveform: np.ndarray
    arousal: str
    valence: str
    audio_id: str


def _resample(x: np.ndarray, src_sr: int, dst_sr: int = TARGET_SR) -> np.ndarray:
    if src_sr == dst_sr or x.size == 0:
        return x
    n_out = max(1, int(round(x.size * dst_sr / src_sr)))
    idx = np.linspace(0, x.size - 1, n_out)
    return np.interp(idx, np.arange(x.size), x).astype(np.float32)


def read_wav(path: Path, target_sr: int = TARGET_SR) -> np.ndarray:
    """Decode a PCM WAV via stdlib `wave` (no soundfile dependency)."""
    with wave.open(str(path), "rb") as wf:
        n_ch, sampwidth, framerate, n_frames = wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()
        raw = wf.readframes(n_frames)
    if sampwidth == 1:
        dtype = np.uint8
        audio = (np.frombuffer(raw, dtype=dtype).astype(np.float32) - 128.0) / 128.0
    elif sampwidth == 2:
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        audio = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"unsupported sample width {sampwidth} for {path}")
    if n_ch > 1:
        audio = audio.reshape(-1, n_ch).mean(axis=1)
    return _resample(audio, framerate, target_sr).astype(np.float32)


def _normalize_label(value: str, allowed: tuple[str, ...]) -> str | None:
    v = value.strip().lower()
    for allowed_v in allowed:
        if v == allowed_v.lower():
            return allowed_v
    return None


def _label_from_fallback(rel: Path) -> tuple[str | None, str | None]:
    """Infer arousal/valence from the audio_id / path when CSV missing."""
    text = (rel.stem + " " + rel.parent.name).lower()
    arousal: str | None = None
    valence: str | None = None
    for a in AROUSAL_LEVELS:
        if a.lower() in text:
            arousal = a
    for v in VALENCE_LEVELS:
        if v.lower() in text:
            valence = v
    return arousal, valence


def find_audio_files(data_dir: Path) -> dict[str, Path]:
    out: dict[str, Path] = {}
    for ext in ("*.wav", "*.mp3", "*.flac", "*.ogg"):
        for p in data_dir.rglob(ext):
            out.setdefault(p.stem, p)
    return out


def load_labels(data_dir: Path) -> dict[str, tuple[str, str]]:
    labels: dict[str, tuple[str, str]] = {}
    for csv_path in sorted(data_dir.rglob("*_labels.csv")):
        try:
            with csv_path.open(newline="", encoding="utf-8", errors="replace") as fh:
                for row in csv.DictReader(fh):
                    audio_id = (row.get("audio_id") or "").strip()
                    if not audio_id:
                        continue
                    arousal = _normalize_label(row.get("arousal") or "", AROUSAL_LEVELS)
                    valence = _normalize_label(row.get("valence") or "", VALENCE_LEVELS)
                    if arousal and valence:
                        labels[audio_id] = (arousal, valence)
        except (csv.Error, OSError):
            continue
    return labels


def load_barkopedia(data_dir: Path, max_samples: int = 0) -> list[BarkSample]:
    """Load labeled Barkopedia clips. max_samples=0 means all found."""
    if not data_dir.is_dir():
        return []
    audio_files = find_audio_files(data_dir)
    labels = load_labels(data_dir)
    if not labels:
        return []

    samples: list[BarkSample] = []
    for audio_id, (arousal, valence) in labels.items():
        if max_samples and len(samples) >= max_samples:
            break
        path = audio_files.get(audio_id)
        if path is None:
            continue
        try:
            waveform = read_wav(path)
        except (wave.Error, ValueError, OSError):
            continue
        if waveform.size < 160:
            continue
        samples.append(BarkSample(waveform=waveform, arousal=arousal, valence=valence, audio_id=audio_id))
    return samples


def class_counts(samples: list[BarkSample]) -> dict[str, dict[str, int]]:
    out: dict[str, dict[str, int]] = {}
    for key, allowed in (("arousal", AROUSAL_LEVELS), ("valence", VALENCE_LEVELS)):
        counts = {a: 0 for a in allowed}
        for s in samples:
            val = getattr(s, key)
            if val in counts:
                counts[val] += 1
        out[key] = counts
    return out
