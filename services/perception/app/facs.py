"""DogFACS-style facial landmark math (docs/ADVANCED_MATH.md §2, §5).

Operates on 2D landmark positions supplied by the caller — this module has
no landmark *detector* of its own, matching tail.py's split between "the
math" and "the keypoint source" (pose.py is bbox-geometry only today; a
DogFLW-style landmark head is separate work). `face.py`'s heuristics stay
in place as the no-keypoint fallback, per the doc's own instruction.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


Point = tuple[float, float]


def landmark_displacement(current: Point, neutral: Point) -> float:
    """d_j(t) = ||L_j(t) - L_j(t0)||_2 — raw AU displacement from neutral."""
    return math.hypot(current[0] - neutral[0], current[1] - neutral[1])


def normalized_au_intensity(displacement: float, mean_neutral_interlandmark_dist: float) -> float:
    """I_j^norm = d_j / mean inter-landmark distance of *that dog's* neutral face.

    Normalizing by the dog's own neutral-face scale controls for breed
    morphology (a Chihuahua and a Great Dane have very different absolute
    distances for the same relative expression).
    """
    if mean_neutral_interlandmark_dist <= 1e-9:
        return 0.0
    return displacement / mean_neutral_interlandmark_dist


def decision_tree_split(value: float, threshold: float) -> str:
    """One DogFACS decision-tree node: v <= tau -> S1, v > tau -> S2.

    Boneh-Shitrit et al. (2022): deep learning reached >89% vs 71% for this
    tree, so treat it as an explainable fallback, not the primary estimator.
    """
    return "S1" if value <= threshold else "S2"


def linear_predictive_model(
    rbrow_var: float,
    ear_base_dist: float,
    mouth_open: float,
    weights: tuple[float, float, float] = (1.0, 1.0, 1.0),
    bias: float = 0.0,
) -> float:
    """P(emotion) = b0 + b1*RbrowVar + b2*EarBaseDist + b3*MouthOpen + ...

    Reported ~83% accuracy for emotion condition in the source paper.
    `weights`/`bias` are unfit placeholders (no per-dog calibration data
    yet) — this is the linear *form*, not a calibrated classifier. Output
    is squashed through a logistic so it reads as a probability-shaped
    [0, 1] value regardless of the (currently arbitrary) weight scale.
    """
    w0, w1, w2 = weights
    z = bias + w0 * rbrow_var + w1 * ear_base_dist + w2 * mouth_open
    return 1.0 / (1.0 + math.exp(-z))


def ear_angle(ear_base: Point, ear_tip: Point, skull_axis: Point) -> float:
    """Ear angle (radians) relative to the skull axis vector.

    Forward (small angle, aligned with skull_axis) -> attention/interest;
    flattened (large angle, near pi) -> fear/submission; mid-range -> neutral.
    """
    ear_vec = (ear_tip[0] - ear_base[0], ear_tip[1] - ear_base[1])
    ear_mag = math.hypot(*ear_vec)
    axis_mag = math.hypot(*skull_axis)
    if ear_mag < 1e-9 or axis_mag < 1e-9:
        return 0.0
    dot = ear_vec[0] * skull_axis[0] + ear_vec[1] * skull_axis[1]
    cos_theta = max(-1.0, min(1.0, dot / (ear_mag * axis_mag)))
    return math.acos(cos_theta)


def sclera_exposure(sclera_area_px: float, eye_area_px: float) -> float:
    """Exposed-sclera fraction ("whale eye"). Increased exposure -> stress/anxiety."""
    if eye_area_px <= 1e-9:
        return 0.0
    return max(0.0, min(1.0, sclera_area_px / eye_area_px))


@dataclass
class BlinkTracker:
    """Rolling blink-rate estimate with a 2-sigma distress flag.

    blink_flag = (instantaneous rate > mean + 2*std) — a sudden jump above
    the dog's own established baseline, not an absolute threshold, since
    baseline blink rate varies a lot by individual and breed.
    """

    window_s: float = 60.0
    _events: list[float] = None  # type: ignore[assignment]
    _rate_history: list[float] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self._events = []
        self._rate_history = []

    def record_blink(self, t: float) -> None:
        self._events.append(t)
        self._events = [e for e in self._events if e >= t - self.window_s]
        rate = len(self._events) / self.window_s
        self._rate_history.append(rate)
        if len(self._rate_history) > 120:
            self._rate_history.pop(0)

    def current_rate(self) -> float:
        return self._rate_history[-1] if self._rate_history else 0.0

    def blink_flag(self) -> bool:
        if len(self._rate_history) < 5:
            return False
        mean_b = sum(self._rate_history) / len(self._rate_history)
        var_b = sum((r - mean_b) ** 2 for r in self._rate_history) / len(self._rate_history)
        std_b = math.sqrt(var_b)
        return self._rate_history[-1] > mean_b + 2 * std_b


def mouth_tension(left_corner: Point, right_corner: Point, neutral_width: float) -> float:
    """Mouth-corner tension: retracted (wide relative to neutral) -> affiliative,
    tight/narrow -> fear/aggression. Returns a signed score around 0 (neutral
    width): positive -> retracted/relaxed, negative -> tight.
    """
    width = math.hypot(right_corner[0] - left_corner[0], right_corner[1] - left_corner[1])
    if neutral_width <= 1e-9:
        return 0.0
    return (width - neutral_width) / neutral_width
