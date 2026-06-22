"""ECG waveform synthesis and HRV feature extraction (PhysioZoo-shaped)."""
from __future__ import annotations

import numpy as np

# Published resting dog HR ~60–120 bpm; SDNN ~20–80 ms (PhysioZoo / veterinary HRV literature).
DOG_HR_BPM_RANGE = (60.0, 120.0)
DOG_SDNN_MS_RANGE = (20.0, 80.0)
DEFAULT_SAMPLE_RATE = 500.0  # PhysioZoo dog recordings


def synthesize_ecg(
    duration_s: float = 10.0,
    hr_bpm: float = 90.0,
    sdnn_ms: float = 45.0,
    sample_rate: float = DEFAULT_SAMPLE_RATE,
    seed: int | None = None,
) -> np.ndarray:
    """Generate a simple QRS-like ECG trace with variable RR intervals."""
    rng = np.random.default_rng(seed)
    n = int(duration_s * sample_rate)
    signal = np.zeros(n, dtype=np.float32)
    mean_rr = 60.0 / hr_bpm
    rr_jitter = (sdnn_ms / 1000.0) * 0.5
    t = 0.0
    while t < duration_s:
        idx = int(t * sample_rate)
        if 0 <= idx < n - 20:
            width = 12
            qrs = np.exp(-np.linspace(-2, 2, width) ** 2)
            signal[idx : idx + width] += qrs.astype(np.float32)
        rr = mean_rr + rng.normal(0.0, rr_jitter)
        t += max(0.35, rr)
    noise = rng.normal(0.0, 0.02, size=n).astype(np.float32)
    return signal + noise


def detect_r_peaks(ecg: np.ndarray, sample_rate: float = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    """Lightweight R-peak detector for synthetic / clean ECG."""
    if ecg.size < int(sample_rate):
        return np.array([], dtype=np.int64)
    kernel = max(3, int(sample_rate * 0.08))
    smoothed = np.convolve(ecg, np.ones(kernel) / kernel, mode="same")
    threshold = float(np.mean(smoothed) + 0.6 * np.std(smoothed))
    min_dist = int(sample_rate * 0.3)
    peaks: list[int] = []
    for i in range(1, len(smoothed) - 1):
        if smoothed[i] > threshold and smoothed[i] >= smoothed[i - 1] and smoothed[i] >= smoothed[i + 1]:
            if not peaks or i - peaks[-1] >= min_dist:
                peaks.append(i)
    return np.array(peaks, dtype=np.int64)


def rr_intervals_ms(peaks: np.ndarray, sample_rate: float = DEFAULT_SAMPLE_RATE) -> np.ndarray:
    if peaks.size < 2:
        return np.array([], dtype=np.float32)
    return (np.diff(peaks) / sample_rate * 1000.0).astype(np.float32)


def hrv_features(rr_ms: np.ndarray) -> dict[str, float]:
    if rr_ms.size < 2:
        return {"hr_bpm": 0.0, "sdnn_ms": 0.0, "rmssd_ms": 0.0, "stress_score": 0.5}
    mean_rr = float(np.mean(rr_ms))
    hr_bpm = 60000.0 / max(mean_rr, 1.0)
    sdnn = float(np.std(rr_ms))
    diff = np.diff(rr_ms)
    rmssd = float(np.sqrt(np.mean(diff**2))) if diff.size else 0.0
    # Higher HR + lower HRV → elevated stress proxy (maps to Zenodo stress / cortisol studies).
    stress = min(1.0, max(0.0, (hr_bpm - 70.0) / 60.0 + (50.0 - sdnn) / 80.0))
    return {
        "hr_bpm": hr_bpm,
        "sdnn_ms": sdnn,
        "rmssd_ms": rmssd,
        "stress_score": stress,
    }


def ecg_window_features(ecg: np.ndarray, sample_rate: float = DEFAULT_SAMPLE_RATE) -> dict[str, float]:
    peaks = detect_r_peaks(ecg, sample_rate)
    feats = hrv_features(rr_intervals_ms(peaks, sample_rate))
    feats["hr_norm"] = min(1.0, max(0.0, (feats["hr_bpm"] - DOG_HR_BPM_RANGE[0]) / (DOG_HR_BPM_RANGE[1] - DOG_HR_BPM_RANGE[0])))
    return feats
