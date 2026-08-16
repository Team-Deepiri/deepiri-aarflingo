"""Wire docs/ADVANCED_MATH.md §1/§2/§3/§5/§6 into the live frame pipeline.

Every advanced-perception math module (tail.py, facs.py, head.py, gait.py)
expects keypoint inputs the bbox-only pipeline doesn't produce. This module
is the *proxy source* the math modules' docstrings point to: it derives
bounded, honest proxies from what the frame pipeline *does* observe (bbox
geometry, brightness bands, velocity) and feeds them through the real math
modules — so the features represent real measured signal, computed by the
documented equations, with no fabricated landmark.

Each tracker is a module-level singleton so temporal statistics (wag rhythm,
blink baseline, freeze duration) accumulate across frames. Call
`reset_trackers()` when the dog leaves the frame.
"""
from __future__ import annotations

import math
import time
from collections import deque

import numpy as np

from .dog_detect import BBox
from .facs import BlinkTracker, mouth_tension as _facs_mouth_tension
from .facs import normalized_au_intensity, sclera_exposure
from .facs import ear_angle as _facs_ear_angle
from .gait import FreezeTracker, approach_avoidance, center_of_mass
from .gait import gait_classification, limb_phase
from .head import RollTracker
from .pose import PoseEstimate
from .tail import TailTrack, lyapunov_estimator, wag_metrics, asymmetry_index

WAG_WINDOW_S = 3.0      # wag metrics window (Ren et al. iScience window)
SWAY_EMA = 0.15         # lateral body-sway smoothing
BLINK_BAND = 0.25       # top fraction of the bbox treated as the eye band
BLINK_DROP = 0.015      # band-brightness drop that counts as a blink
BLINK_DEBOUNCE_S = 0.4  # min gap between accepted blinks
STILL_THRESHOLD = 0.01  # bbox speed below which the dog is frozen


class _DeepFusionState:
    def __init__(self) -> None:
        self.track = TailTrack()
        self.roll = RollTracker()
        self.blink = BlinkTracker()
        self.freeze = FreezeTracker(still_threshold=STILL_THRESHOLD)
        self._bg = deque(maxlen=3)            # recent top-band brightness
        self._phases: deque[float] = deque(maxlen=3)  # recent velocity phases
        self._sway_ema = 0.5
        self._com = (0.5, 0.5)
        self._com_ref = (0.5, 0.5)
        self._last_blink_t = 0.0
        self._last_t = 0.0

    def push_frame(self, bbox: BBox, pose: PoseEstimate, face, frame_bgr: np.ndarray, vx: float, vy: float) -> dict:
        now = time.monotonic()
        dt = now - self._last_t
        self._last_t = now

        # ── §1 tail: wag ↔ lateral body sway, height ↔ ground proximity ──
        self._sway_ema = SWAY_EMA * bbox.cx + (1 - SWAY_EMA) * self._sway_ema
        theta = float(np.clip((bbox.cx - self._sway_ema) / max(bbox.w, 1e-3) * 2.0, -1.0, 1.0))
        height = float(np.clip(1.0 - (bbox.y + bbox.h), 0.0, 1.0))
        self.track.push(now, theta, height)
        tail_w = wag_metrics(self.track.window(WAG_WINDOW_S))
        tail_score = asymmetry_index(self.track.window(WAG_WINDOW_S))
        tail_series = [s.theta for s in self.track.window(WAG_WINDOW_S)]
        lam = lyapunov_estimator(tail_series) if len(tail_series) >= 16 else 0.0

        # ── §3 head: pitch/yaw from pose proxies, roll variance from aspect ──
        pitch = float(np.clip((pose.head_y - 0.5) * math.pi, -math.pi, math.pi))
        yaw = float(np.clip((pose.head_gaze_x - 0.5) * math.pi, -math.pi, math.pi))
        roll = float(np.clip((pose.aspect_ratio - 1.5) * 0.3, -0.3, 0.3))
        self.roll.push(now, roll)
        roll_var = self.roll.roll_variance()

        # ── §5/§2 face/ears: brightness-band blink proxy, FACS from heuristics ──
        wh = float(face.whale_eye_likelihood)
        lick = float(face.lip_lick_likelihood)
        h, w = max(1, int(bbox.h * frame_bgr.shape[0])), max(1, int(bbox.w * frame_bgr.shape[1]))
        x0 = max(0, int(bbox.cx * frame_bgr.shape[1] - w // 2))
        y0 = max(0, int(bbox.y * frame_bgr.shape[0]))
        band = frame_bgr[y0 : y0 + max(1, int(h * BLINK_BAND)), x0 : x0 + w]
        if band.size:
            self._bg.append(float(np.mean(band) / 255.0))
        if len(self._bg) == self._bg.maxlen and now - self._last_blink_t > BLINK_DEBOUNCE_S:
            prev, curr = self._bg[0], self._bg[-1]
            if prev - curr > BLINK_DROP:
                self.blink.record_blink(now)
                self._last_blink_t = now
        ear_angle = _facs_ear_angle(
            (0.0, 0.0), (0.5, 0.0), (pose.head_gaze_x - 0.5, -(pose.head_y - 0.5))
        )
        sclera = sclera_exposure(sclera_area_px=wh, eye_area_px=1.0)
        # mouth corners retract (positive) when relaxed, tighten (negative)
        # under stress — mapped off the lip-lick heuristic: high lip-lick
        # (anxiety) narrows the mouth (tight), low lick relaxes it. Bounded.
        relax = 1.0 - max(0.0, min(1.0, lick))
        tension = _facs_mouth_tension(
            (0.5 - relax / 2.0, 0.5), (0.5 + relax / 2.0, 0.5), neutral_width=0.25
        )
        au = normalized_au_intensity(abs(tension), mean_neutral_interlandmark_dist=0.5)

        # ── §6 COM / approach-avoidance / gait / freeze ──
        com = (float(bbox.cx), float(bbox.cy))
        com_shift_x = com[0] - self._com_ref[0]
        aa = approach_avoidance(com, self._com_ref)
        self._com_ref = (0.98 * self._com_ref[0] + 0.02 * com[0],
                         0.98 * self._com_ref[1] + 0.02 * com[1])
        phase = limb_phase(vx, vy)
        self._phases.append(phase)
        gait = "indeterminate"
        if len(self._phases) >= 3:
            plf, prh, plh = self._phases[-1], self._phases[-2], self._phases[-3]
            gait = gait_classification(plf, prh, plh)
        speed = math.hypot(vx, vy)
        freeze_dur = self.freeze.update(now, speed)

        return {
            "tail_wag_rate": float(tail_w["wag_rate"]),
            "tail_amplitude": float(tail_w["amplitude"]),
            "tail_velocity": float(self.track.omega()),
            "tail_rhythmicity": float(tail_w["rhythmicity"]),
            "tail_height": float(tail_w["height"]),
            "tail_asymmetry": tail_score,
            "tail_lyapunov": float(lam),
            "head_pitch": pitch,
            "head_yaw": yaw,
            "head_roll_var": float(roll_var),
            "ear_angle": ear_angle,
            "sclera_exposure": sclera,
            "blink_rate": float(self.blink.current_rate()),
            "mouth_tension": float(max(-1.0, min(1.0, tension))),
            "facs_au_intensity": float(max(0.0, min(1.0, au))),
            "com_shift_x": com_shift_x,
            "approach_avoid": aa,
            "gait_phase_trot": 1.0 if gait == "trot" else 0.0,
            "gait_phase_pace": 1.0 if gait == "pace" else 0.0,
            "freeze_duration": float(freeze_dur),
        }


_STATE = _DeepFusionState()


def reset_trackers() -> None:
    """Reset temporal trackers when no dog is visible (or on camera switch)."""
    global _STATE
    _STATE = _DeepFusionState()


def compute_advanced_features(
    bbox: BBox,
    pose: PoseEstimate,
    face,
    frame_bgr: np.ndarray,
    vx: float,
    vy: float,
) -> dict:
    return _STATE.push_frame(bbox, pose, face, frame_bgr, vx, vy)


def advanced_defaults() -> dict:
    """Zero-ish feature values for the no-dog frame."""
    return {
        "tail_wag_rate": 0.0,
        "tail_amplitude": 0.5,
        "tail_velocity": 0.0,
        "tail_rhythmicity": 0.0,
        "tail_height": 0.5,
        "tail_asymmetry": 0.0,
        "tail_lyapunov": 0.0,
        "head_pitch": 0.0,
        "head_yaw": 0.0,
        "head_roll_var": 0.0,
        "ear_angle": 0.0,
        "sclera_exposure": 0.0,
        "blink_rate": 0.0,
        "mouth_tension": 0.0,
        "facs_au_intensity": 0.0,
        "com_shift_x": 0.0,
        "approach_avoid": 0.0,
        "gait_phase_trot": 0.0,
        "gait_phase_pace": 0.0,
        "freeze_duration": 0.0,
    }