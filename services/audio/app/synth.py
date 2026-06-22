"""Synthetic bark waveforms shaped after DogSpeak / Barkopedia arousal-valence labels."""
from __future__ import annotations

import numpy as np

AROUSAL_LEVELS = ("low", "medium", "high")
VALENCE_LEVELS = ("negative", "neutral", "positive")


def synthesize_bark(
    arousal: str = "medium",
    valence: str = "neutral",
    duration_s: float = 0.6,
    sample_rate: int = 16000,
    seed: int | None = None,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(duration_s * sample_rate)
    t = np.linspace(0, duration_s, n, dtype=np.float32)
    base_freq = {"low": 180.0, "medium": 320.0, "high": 480.0}[arousal]
    if valence == "negative":
        base_freq *= 0.9
    elif valence == "positive":
        base_freq *= 1.1
    bursts = max(1, {"low": 1, "medium": 2, "high": 4}[arousal])
    wave = np.zeros(n, dtype=np.float32)
    for b in range(bursts):
        start = int(n * (b / (bursts + 1)))
        length = int(sample_rate * 0.12)
        seg_t = np.linspace(0, 0.12, length, dtype=np.float32)
        bark = np.sin(2 * np.pi * base_freq * seg_t) * np.exp(-seg_t * 12)
        end = min(n, start + length)
        wave[start:end] += bark[: end - start]
    wave += rng.normal(0.0, 0.01, size=n).astype(np.float32)
    peak = np.max(np.abs(wave)) or 1.0
    return (wave / peak * 0.8).astype(np.float32)
