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


def lf_hf_ratio(rr_ms: np.ndarray, resample_hz: float = 4.0) -> dict[str, float]:
    """Frequency-domain HRV: LF/HF power ratio (docs/ADVANCED_MATH.md §8).

    RR intervals are unevenly spaced in time (one sample per heartbeat), so
    they're first resampled onto an even time grid (the "tachogram") before
    an FFT periodogram is meaningful. Dog frequency bands per the veterinary
    HRV literature: LF 0.04-0.15 Hz, HF 0.15-0.40 Hz. `resample_hz=4.0` gives
    a 2 Hz Nyquist limit, comfortably above the 0.40 Hz HF edge.
    """
    empty = {"lf_power": 0.0, "hf_power": 0.0, "lf_hf_ratio": 0.0}
    if rr_ms.size < 4:
        return empty
    rr_s = rr_ms.astype(np.float64) / 1000.0
    beat_times = np.cumsum(rr_s)
    beat_times -= beat_times[0]
    duration = float(beat_times[-1])
    if duration <= 0:
        return empty
    even_times = np.arange(0.0, duration, 1.0 / resample_hz)
    if even_times.size < 8:
        return empty
    tachogram = np.interp(even_times, beat_times, rr_s)
    tachogram = tachogram - np.mean(tachogram)
    windowed = tachogram * np.hanning(tachogram.size)
    spectrum = np.fft.rfft(windowed)
    psd = (np.abs(spectrum) ** 2) / (resample_hz * tachogram.size)
    freqs = np.fft.rfftfreq(tachogram.size, d=1.0 / resample_hz)
    lf_mask = (freqs >= 0.04) & (freqs < 0.15)
    hf_mask = (freqs >= 0.15) & (freqs < 0.40)
    lf_power = float(np.trapezoid(psd[lf_mask], freqs[lf_mask])) if lf_mask.any() else 0.0
    hf_power = float(np.trapezoid(psd[hf_mask], freqs[hf_mask])) if hf_mask.any() else 0.0
    ratio = lf_power / hf_power if hf_power > 1e-9 else 0.0
    return {"lf_power": lf_power, "hf_power": hf_power, "lf_hf_ratio": ratio}


def ecg_window_features(ecg: np.ndarray, sample_rate: float = DEFAULT_SAMPLE_RATE) -> dict[str, float]:
    peaks = detect_r_peaks(ecg, sample_rate)
    rr_ms = rr_intervals_ms(peaks, sample_rate)
    feats = hrv_features(rr_ms)
    feats["hr_norm"] = min(1.0, max(0.0, (feats["hr_bpm"] - DOG_HR_BPM_RANGE[0]) / (DOG_HR_BPM_RANGE[1] - DOG_HR_BPM_RANGE[0])))
    feats.update(lf_hf_ratio(rr_ms))
    return feats
