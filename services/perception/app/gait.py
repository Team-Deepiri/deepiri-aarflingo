"""Whole-body posture & gait (docs/ADVANCED_MATH.md §6).

Operates on supplied landmark positions/velocities — no keypoint detector
included here, same split as tail.py/facs.py/head.py.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

Point = tuple[float, float]


def center_of_mass(landmarks: list[Point], masses: list[float] | None = None) -> Point:
    """COM(t) = sum(m_i * p_i) / sum(m_i). Uniform mass per landmark if unset."""
    if not landmarks:
        return (0.0, 0.0)
    m = masses if masses is not None else [1.0] * len(landmarks)
    total_m = sum(m)
    if total_m <= 1e-9:
        return (0.0, 0.0)
    cx = sum(mi * p[0] for mi, p in zip(m, landmarks)) / total_m
    cy = sum(mi * p[1] for mi, p in zip(m, landmarks)) / total_m
    return (cx, cy)


def approach_avoidance(com_now: Point, com_ref: Point) -> float:
    """AA(t) = (COM_x(t) - COM_x(t0)) / ||COM(t) - COM(t0)||_2.

    AA > 0 -> forward lean / approach; AA < 0 -> backward lean / avoidance.
    Returns 0.0 when COM hasn't moved (no direction is defined).
    """
    dx = com_now[0] - com_ref[0]
    dy = com_now[1] - com_ref[1]
    dist = math.hypot(dx, dy)
    if dist <= 1e-9:
        return 0.0
    return dx / dist


def limb_phase(vx: float, vy: float) -> float:
    """phi_limb(t) = atan2(vy, vx) — foot-fall phase angle for one limb."""
    return math.atan2(vy, vx)


def _phase_diff(a: float, b: float) -> float:
    """Smallest signed angular difference between two phases, wrapped to [0, pi]."""
    d = abs(a - b) % (2 * math.pi)
    return min(d, 2 * math.pi - d)


def gait_classification(phase_lf: float, phase_rh: float, phase_lh: float, tol: float = math.pi / 6) -> str:
    """Trot (diagonal pairs ~pi out of phase) vs pace (lateral pairs ~pi out of phase).

    Trot: |phi_LF - phi_RH| ~ pi (relaxed, diagonal gait)
    Pace: |phi_LF - phi_LH| ~ pi (anxious/tense, lateral gait)
    Returns "trot", "pace", or "indeterminate" when neither pair is close to
    pi within `tol`.
    """
    trot_diff = _phase_diff(phase_lf, phase_rh)
    pace_diff = _phase_diff(phase_lf, phase_lh)
    trot_score = abs(math.pi - trot_diff)
    pace_score = abs(math.pi - pace_diff)
    if trot_score <= tol and trot_score <= pace_score:
        return "trot"
    if pace_score <= tol and pace_score < trot_score:
        return "pace"
    return "indeterminate"


@dataclass
class FreezeTracker:
    """Zero-velocity interval duration from optical-flow-derived motion magnitude.

    Sudden immobility (velocity below `still_threshold` sustained) -> high
    alert/fear.
    """

    still_threshold: float = 0.01
    _freeze_start: float | None = field(default=None, init=False)
    last_duration_s: float = field(default=0.0, init=False)

    def update(self, t: float, speed: float) -> float:
        if speed < self.still_threshold:
            if self._freeze_start is None:
                self._freeze_start = t
            self.last_duration_s = t - self._freeze_start
        else:
            self._freeze_start = None
            self.last_duration_s = 0.0
        return self.last_duration_s
