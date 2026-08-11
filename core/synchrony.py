"""Cross-modal synchrony & simple state fusion (docs/ADVANCED_MATH.md §7).

Pure signal-processing/estimation math over supplied per-modality time
series — no sensor-specific code (GSR isn't wired into aarf-physio's
sensor set yet; this module doesn't need it to be).
"""
from __future__ import annotations

import numpy as np


def phase_locking_value(phase_a: np.ndarray, phase_b: np.ndarray) -> float:
    """PLV = |mean(exp(i*(phase_a - phase_b)))| in [0, 1].

    1.0 -> perfectly phase-locked (coherent emotional state, e.g. tail-wag
    and respiration rhythms aligned); 0.0 -> phases drift independently
    (desync / conflicting signals). Inputs are instantaneous phase angles
    (radians), not raw signals — use `np.angle(scipy.signal.hilbert(x))`-
    style phase extraction upstream, or zero-crossing-derived phase for a
    quasi-periodic series like a wag-angle trace.
    """
    n = min(phase_a.size, phase_b.size)
    if n == 0:
        return 0.0
    diff = phase_a[:n] - phase_b[:n]
    return float(np.abs(np.mean(np.exp(1j * diff))))


def cross_correlation(series_a: np.ndarray, series_b: np.ndarray, max_lag: int) -> dict[str, float]:
    """Normalized cross-correlation, searched over +/- max_lag samples.

    Returns the lag (samples) and correlation value at the best match.
    Positive lag means series_b leads series_a by that many samples.
    """
    n = min(series_a.size, series_b.size)
    if n < 2 or max_lag < 0:
        return {"best_lag": 0.0, "correlation": 0.0}
    a = series_a[:n] - np.mean(series_a[:n])
    b = series_b[:n] - np.mean(series_b[:n])
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm < 1e-12:
        return {"best_lag": 0.0, "correlation": 0.0}

    best_lag = 0
    best_corr = -np.inf
    max_lag = min(max_lag, n - 1)
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            aa, bb = a[: n - lag], b[lag:n]
        else:
            aa, bb = a[-lag:n], b[: n + lag]
        if aa.size == 0:
            continue
        corr = float(np.dot(aa, bb) / norm)
        if corr > best_corr:
            best_corr = corr
            best_lag = lag
    return {"best_lag": float(best_lag), "correlation": float(best_corr)}


class LatentStateKalman:
    """Linear-Gaussian Kalman filter fusing multiple 1D modality signals into
    a 2D latent [arousal, valence] state.

    State transition is a random walk (A = I): cheap, online, and doesn't
    assume a dynamics model we don't have data to fit. Each modality is an
    independent noisy linear observation of the latent state via its own
    row of H — e.g. HRV maps mostly to arousal, tail asymmetry mostly to
    valence, so H's rows are (arousal_weight, valence_weight) per modality.
    """

    def __init__(
        self,
        process_var: float = 1e-3,
        obs_var: float = 0.05,
        initial_state: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self.x = np.array(initial_state, dtype=float)  # [arousal, valence]
        self.P = np.eye(2) * 1.0
        self.Q = np.eye(2) * process_var
        self.obs_var = obs_var

    def predict(self) -> None:
        # A = I (random walk): P = A P A^T + Q = P + Q
        self.P = self.P + self.Q

    def update(self, observation: float, h_row: tuple[float, float]) -> None:
        """Fuse one scalar modality observation with weights h_row=(w_arousal, w_valence)."""
        h = np.array(h_row, dtype=float).reshape(1, 2)
        y = observation - float((h @ self.x).item())
        s = float((h @ self.P @ h.T).item()) + self.obs_var
        if s <= 1e-12:
            return
        k = (self.P @ h.T) / s  # Kalman gain, shape (2, 1)
        self.x = self.x + (k.flatten() * y)
        self.P = self.P - k @ h @ self.P

    def state(self) -> tuple[float, float]:
        return float(self.x[0]), float(self.x[1])
