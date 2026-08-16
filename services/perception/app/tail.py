"""Tail biomechanics beyond wag rate (docs/ADVANCED_MATH.md §1).

Operates on a time series of tail-tip angle theta(t) (radians, right = positive)
sampled at a known rate. This module is deliberately decoupled from *how*
theta(t) is obtained — `pose.py` is bbox-geometry only today and has no
tail-tip keypoint, so a keypoint head (or an IMU-derived proxy per the doc's
"outsider loop") is a separate piece of work. Once either exists, feed its
samples through `TailTrack.push` and read off `wag_metrics` /
`asymmetry_index` / `lyapunov_estimator`.

Sources: Ren et al. 2022 (iScience) for attractor dynamics; Quaranta et al.
2007 (Current Biology) for the lateralisation asymmetry index.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class TailSample:
    t: float
    theta: float
    height: float = 0.5


@dataclass
class TailTrack:
    """Rolling buffer of tail-tip samples with derived kinematic state."""

    max_samples: int = 300
    samples: list[TailSample] = field(default_factory=list)

    def push(self, t: float, theta: float, height: float = 0.5) -> None:
        self.samples.append(TailSample(t=t, theta=theta, height=height))
        if len(self.samples) > self.max_samples:
            self.samples.pop(0)

    def omega(self) -> float:
        """Angular velocity dtheta/dt at the most recent sample (finite diff)."""
        if len(self.samples) < 2:
            return 0.0
        a, b = self.samples[-2], self.samples[-1]
        dt = b.t - a.t
        if dt <= 0:
            return 0.0
        return (b.theta - a.theta) / dt

    def alpha(self) -> float:
        """Angular acceleration d^2theta/dt^2 at the most recent sample."""
        if len(self.samples) < 3:
            return 0.0
        a, b, c = self.samples[-3], self.samples[-2], self.samples[-1]
        dt1 = b.t - a.t
        dt2 = c.t - b.t
        if dt1 <= 0 or dt2 <= 0:
            return 0.0
        w1 = (b.theta - a.theta) / dt1
        w2 = (c.theta - b.theta) / dt2
        return (w2 - w1) / dt2

    def window(self, duration_s: float) -> list[TailSample]:
        if not self.samples:
            return []
        cutoff = self.samples[-1].t - duration_s
        return [s for s in self.samples if s.t >= cutoff]


def _zero_crossing_times(samples: list[TailSample]) -> list[float]:
    crossings: list[float] = []
    for a, b in zip(samples, samples[1:]):
        if a.theta == 0.0 or (a.theta < 0) != (b.theta < 0):
            if b.theta == a.theta:
                continue
            frac = -a.theta / (b.theta - a.theta)
            crossings.append(a.t + frac * (b.t - a.t))
    return crossings


def wag_metrics(samples: list[TailSample]) -> dict[str, float]:
    """Wag rate, amplitude, rhythmicity (CV of inter-wag intervals), mean height."""
    if len(samples) < 3:
        return {"wag_rate": 0.0, "amplitude": 0.0, "rhythmicity": 0.0, "height": 0.5}
    duration = samples[-1].t - samples[0].t
    crossings = _zero_crossing_times(samples)
    wag_rate = (len(crossings) / duration) if duration > 0 else 0.0

    thetas = [s.theta for s in samples]
    amplitude = max(thetas) - min(thetas)

    intervals = [b - a for a, b in zip(crossings, crossings[1:])]
    if len(intervals) >= 2:
        mean_i = sum(intervals) / len(intervals)
        var_i = sum((i - mean_i) ** 2 for i in intervals) / len(intervals)
        rhythmicity = (math.sqrt(var_i) / mean_i) if mean_i > 0 else 0.0
    else:
        rhythmicity = 0.0

    height = sum(s.height for s in samples) / len(samples)
    return {
        "wag_rate": wag_rate,
        "amplitude": amplitude,
        "rhythmicity": rhythmicity,
        "height": height,
    }


def asymmetry_index(samples: list[TailSample]) -> float:
    """Lateralisation valence bias (Quaranta et al. 2007).

    AI = integral(theta_right - theta_left) / integral(theta_right + theta_left)
    over the supplied window, with theta_right/theta_left the positive/negative
    parts of theta(t). AI > 0 -> approach/positive; AI < 0 -> withdrawal/negative.
    Bounded in [-1, 1] by construction (it's a normalized difference of two
    non-negative integrals), so no clamping is needed here.
    """
    if len(samples) < 2:
        return 0.0
    num = 0.0
    den = 0.0
    for a, b in zip(samples, samples[1:]):
        dt = b.t - a.t
        if dt <= 0:
            continue
        theta_mid = (a.theta + b.theta) / 2.0
        right = max(theta_mid, 0.0)
        left = max(-theta_mid, 0.0)
        num += (right - left) * dt
        den += (right + left) * dt
    return num / den if den > 1e-9 else 0.0


def lyapunov_estimator(
    series: list[float],
    delay: int = 3,
    dim: int = 3,
    fit_len: int = 10,
) -> float:
    """Largest Lyapunov exponent via a simplified Rosenstein-style estimate.

    Embeds the scalar series into `dim`-dimensional phase space with delay
    `delay` (Takens' theorem), finds each embedded point's nearest neighbor
    (excluding temporally close points, which would trivially "diverge" from
    almost the same state), tracks how those neighbor-pair distances grow
    over `fit_len` steps, and returns the average log-growth rate.

    lambda < 0 -> stable attractor (relaxed, predictable wagging)
    lambda > 0 -> chaotic / transitional (emotional shift, uncertainty)
    lambda ~ 0 -> marginal, boundary between states

    Domain of validity: needs a reasonably long, evenly-sampled series
    (>= ~50 points for `dim=3, delay=3, fit_len=10` to leave enough embedded
    points and divergence steps); returns 0.0 (no signal) below that.
    """
    n = len(series)
    embed_len = n - (dim - 1) * delay
    min_needed = 2 * fit_len + 5
    if embed_len < min_needed:
        return 0.0

    embedded = [
        tuple(series[i + k * delay] for k in range(dim)) for i in range(embed_len)
    ]

    def dist(p: tuple, q: tuple) -> float:
        return math.sqrt(sum((pi - qi) ** 2 for pi, qi in zip(p, q)))

    min_temporal_sep = max(delay * dim, 1)
    divergences: list[list[float]] = []
    for i in range(embed_len - fit_len):
        best_j = -1
        best_d = math.inf
        for j in range(embed_len):
            if abs(j - i) <= min_temporal_sep or j + fit_len >= embed_len:
                continue
            d = dist(embedded[i], embedded[j])
            if 0.0 < d < best_d:
                best_d = d
                best_j = j
        if best_j < 0 or best_d <= 0:
            continue
        traj = []
        for step in range(fit_len):
            d_step = dist(embedded[i + step], embedded[best_j + step])
            if d_step > 0:
                traj.append(math.log(d_step))
        if len(traj) >= 2:
            divergences.append(traj)

    if not divergences:
        return 0.0

    # Average log-divergence curve across all reference points, then the
    # exponent is its slope (least-squares fit against step index).
    max_len = min(len(t) for t in divergences)
    avg_curve = [
        sum(t[step] for t in divergences) / len(divergences) for step in range(max_len)
    ]
    xs = list(range(max_len))
    mean_x = sum(xs) / max_len
    mean_y = sum(avg_curve) / max_len
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, avg_curve))
    den = sum((x - mean_x) ** 2 for x in xs)
    return num / den if den > 1e-9 else 0.0
