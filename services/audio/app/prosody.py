"""Psychoacoustic descriptors beyond MFCCs (docs/ADVANCED_MATH.md §4).

All numpy-only, no librosa, matching mfcc.py's dependency footprint.
"""
from __future__ import annotations

import numpy as np

# Dog bark/whine fundamentals sit roughly in this band (Yin & McCowan 2004).
F0_MIN_HZ = 80.0
F0_MAX_HZ = 2000.0


def estimate_f0(waveform: np.ndarray, sample_rate: int = 16000) -> float:
    """Autocorrelation-based fundamental frequency estimate.

    Higher F0 -> arousal/distress; lower -> threat/calm (Yin & McCowan 2004).
    Returns 0.0 when no clear periodicity is found (silence, noise, or a
    signal too short to resolve F0_MIN_HZ).
    """
    x = waveform.astype(np.float64)
    if x.size < int(sample_rate / F0_MIN_HZ) + 1:
        return 0.0
    x = x - np.mean(x)
    if np.max(np.abs(x)) < 1e-6:
        return 0.0
    x = x * np.hanning(x.size)

    corr = np.correlate(x, x, mode="full")
    corr = corr[corr.size // 2 :]
    if corr[0] <= 0:
        return 0.0
    corr = corr / corr[0]

    lag_min = int(sample_rate / F0_MAX_HZ)
    lag_max = min(int(sample_rate / F0_MIN_HZ), corr.size - 1)
    if lag_max <= lag_min:
        return 0.0

    search = corr[lag_min:lag_max]
    peak_idx = int(np.argmax(search)) + lag_min
    if corr[peak_idx] < 0.3:  # too weak a periodicity to trust
        return 0.0
    return float(sample_rate / peak_idx)


def harmonic_to_noise_ratio(waveform: np.ndarray, sample_rate: int = 16000) -> float:
    """Cepstral HNR (dB): tonality vs. noise.

    Do not read as monotonic in valence — dogs in positive contexts (food
    anticipation) can show *lower* HNR than negative contexts (separation),
    per the psychoacoustics literature cited in the doc. Treat as one input
    among several, not a standalone valence signal.
    """
    x = waveform.astype(np.float64)
    if x.size < int(sample_rate / F0_MIN_HZ) + 1:
        return 0.0
    x = x - np.mean(x)
    if np.max(np.abs(x)) < 1e-6:
        return 0.0
    windowed = x * np.hanning(x.size)

    spectrum = np.fft.rfft(windowed)
    log_power = np.log(np.abs(spectrum) ** 2 + 1e-12)
    cepstrum = np.fft.irfft(log_power)

    quefrency_min = int(sample_rate / F0_MAX_HZ)
    quefrency_max = min(int(sample_rate / F0_MIN_HZ), cepstrum.size // 2)
    if quefrency_max <= quefrency_min:
        return 0.0

    search = cepstrum[quefrency_min:quefrency_max]
    if search.size < 3:
        return 0.0
    # The band trends smoothly (formant/envelope shape) even with no
    # periodicity at all, so a raw peak-vs-rest comparison is dominated by
    # that trend rather than by actual harmonic structure. Detrend first,
    # then the peak-to-residual ratio isolates the periodicity spike.
    idx = np.arange(search.size)
    slope, intercept = np.polyfit(idx, search, 1)
    residual = search - (slope * idx + intercept)
    peak_i = int(np.argmax(np.abs(residual)))
    peak_energy = float(residual[peak_i] ** 2)
    rest = np.delete(residual, peak_i)
    noise_energy = float(np.mean(rest**2)) if rest.size else 1e-12
    return float(10.0 * np.log10(max(peak_energy, 1e-12) / max(noise_energy, 1e-12)))


def formants(waveform: np.ndarray, sample_rate: int = 16000, order: int = 12) -> tuple[float, float]:
    """F1, F2 via LPC (Levinson-Durbin) root-finding.

    Vocal-tract resonances shaping sound color; snarling/howling have lower
    F1. Returns (0.0, 0.0) when the signal is too short or too quiet for a
    stable LPC fit (need > `order` samples with real energy).
    """
    x = waveform.astype(np.float64)
    if x.size <= order:
        return 0.0, 0.0
    x = x - np.mean(x)
    if np.max(np.abs(x)) < 1e-6:
        return 0.0, 0.0
    x = x * np.hanning(x.size)

    autocorr = np.correlate(x, x, mode="full")[x.size - 1 :]
    if autocorr[0] <= 0:
        return 0.0, 0.0

    # Levinson-Durbin recursion for LPC coefficients.
    a = np.zeros(order + 1)
    a[0] = 1.0
    e = autocorr[0]
    for i in range(1, order + 1):
        acc = autocorr[i] + np.sum(a[1:i] * autocorr[i - 1 : 0 : -1])
        if e <= 1e-12:
            break
        k = -acc / e
        a_prev = a.copy()
        a[i] = k
        for j in range(1, i):
            a[j] = a_prev[j] + k * a_prev[i - j]
        e *= 1 - k * k

    roots = np.roots(a)
    roots = roots[np.imag(roots) >= 0]
    angles = np.angle(roots)
    freqs = sorted(f for f in (angles * sample_rate / (2 * np.pi)) if 0 < f < sample_rate / 2)
    freqs = [f for f in freqs if f > 50.0]  # drop near-DC spurious roots
    f1 = freqs[0] if len(freqs) >= 1 else 0.0
    f2 = freqs[1] if len(freqs) >= 2 else 0.0
    return float(f1), float(f2)


def burstiness(event_times_s: list[float]) -> float:
    """Bark train modeled as a point process: CV of inter-burst intervals.

    Short rapid barks (low CV, small mean interval) -> alarm; long spaced
    barks -> loneliness/boredom. Returns 0.0 with fewer than 3 events (not
    enough intervals to characterize a distribution's spread).
    """
    if len(event_times_s) < 3:
        return 0.0
    times = sorted(event_times_s)
    intervals = np.diff(times)
    mean_i = float(np.mean(intervals))
    if mean_i <= 1e-9:
        return 0.0
    return float(np.std(intervals) / mean_i)


def audio_arousal_continuous(rms: float, eps: float = 1e-6) -> float:
    """Continuous arousal regression target: log-mapped RMS energy."""
    return float(np.log10(max(rms, 0.0) + eps))


def audio_valence_continuous(
    spectral_centroid: float,
    zcr: float,
    rms: float,
    emotion_prior: float = 0.0,
    alpha: float = 1.0,
    beta: float = -1.0,
    gamma: float = 0.5,
    eps: float = 1e-6,
) -> float:
    """Continuous valence regression target: weighted spectral combo + prior.

    V = alpha*centroid + beta*ZCR + gamma*log(RMS) + prior(emotion)

    Sign convention here (beta < 0): higher zero-crossing rate -> harsher/
    noisier bark texture -> pulls valence negative, matching the doc's
    framing of bark emotion as continuous regression rather than discrete
    classes. `alpha`/`beta`/`gamma` are unfit free weights (no per-dog
    calibration data yet) — treat this as a structurally-motivated
    placeholder, not a calibrated model.
    """
    return float(
        alpha * spectral_centroid
        + beta * zcr
        + gamma * np.log10(max(rms, 0.0) + eps)
        + emotion_prior
    )
