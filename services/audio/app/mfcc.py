"""Acoustic feature extraction for bark / whimper classification."""
from __future__ import annotations

import numpy as np


def mfcc_like_features(waveform: np.ndarray, sample_rate: int = 16000, n_coeff: int = 13) -> np.ndarray:
    """Lightweight spectral features (MFCC-shaped) without librosa."""
    if waveform.size == 0:
        return np.zeros(n_coeff, dtype=np.float32)
    x = waveform.astype(np.float32)
    x = x - np.mean(x)
    n_fft = 512
    hop = 256
    frames = []
    for start in range(0, max(1, len(x) - n_fft), hop):
        frame = x[start : start + n_fft]
        if frame.size < n_fft:
            frame = np.pad(frame, (0, n_fft - frame.size))
        spec = np.abs(np.fft.rfft(frame * np.hanning(n_fft)))
        frames.append(spec)
    if not frames:
        return np.zeros(n_coeff, dtype=np.float32)
    mel = np.mean(np.stack(frames), axis=0)
    mel = np.log1p(mel)
    # Downsample spectrum bins to n_coeff pseudo-MFCCs.
    idx = np.linspace(0, mel.size - 1, n_coeff).astype(int)
    return mel[idx].astype(np.float32)


def summarize_audio(waveform: np.ndarray, sample_rate: int = 16000) -> dict[str, float]:
    coeffs = mfcc_like_features(waveform, sample_rate)
    rms = float(np.sqrt(np.mean(waveform.astype(np.float64) ** 2))) if waveform.size else 0.0
    zcr = float(np.mean(np.abs(np.diff(np.sign(waveform))))) / 2.0 if waveform.size > 1 else 0.0
    return {
        "rms": min(1.0, rms * 8.0),
        "zcr": min(1.0, zcr),
        "spectral_centroid": float(np.mean(coeffs)),
        "coeffs": coeffs,
    }
