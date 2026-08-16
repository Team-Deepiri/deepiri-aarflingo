"""Fuse per-frame perception + modality streams into synchrony features.

docs/ADVANCED_MATH.md §7 — cross-modal synchrony & latent-state fusion.
Moves the runtime from "each signal in isolation" to coupling:

  * phase-locking value between the two most emotionally-adjacent live
    streams we have every frame: tail-wag rhythm (proxy: body-sway phase)
    and audio-arousal phase;
  * normalized cross-correlation + best lag between motion and bark prob;
  * a linear-Gaussian Kalman filter fusing all streams into a continuous
    2D latent [arousal, valence] state (the "what is the dog's arousal-
    valence state right now" reframe from §7's architect note).

All module-level singletons so the state accumulates across the live
session and resets on camera/switch.
"""
from __future__ import annotations

import math
from collections import deque

import numpy as np

from core.synchrony import LatentStateKalman, cross_correlation, phase_locking_value

STATE_WINDOW = 60          # rolling samples for PLV / cross-correlation


class _SyncState:
    def __init__(self) -> None:
        self.kalman = LatentStateKalman()
        self._sway_phase: deque[float] = deque(maxlen=STATE_WINDOW)
        self._audio_phase: deque[float] = deque(maxlen=STATE_WINDOW)
        self._motion: deque[float] = deque(maxlen=STATE_WINDOW)
        self._bark: deque[float] = deque(maxlen=STATE_WINDOW)
        self._sway_acc = 0.0
        self._audio_acc = 0.0

    def push(self, features: dict) -> None:
        """Advance the fusion state with one frame's features."""
        # Phase proxy: integrate the stream's deviation from its mean so the
        # instantaneous angle rotates with the signal's own rhythm. A stream
        # that pulses accumulates phase; a flat stream accumulates ~0 and
        # pulls the PLV toward 0 (desync) while co-pulsing streams stay
        # locked — the coupling the doc asks for, without scipy.
        sway = float(features.get("tail_wag_rate", 0.0))
        audio = float(features.get("audio_arousal", 0.0))
        motion = float(features.get("motion", 0.0))
        bark = float(features.get("audio_bark_prob", 0.0))

        self._sway_acc = _step_phase(self._sway_acc, sway)
        self._audio_acc = _step_phase(self._audio_acc, audio)
        self._sway_phase.append(self._sway_acc)
        self._audio_phase.append(self._audio_acc)
        self._motion.append(motion)
        self._bark.append(bark)

        # Kalman: observation rows H = (w_arousal, w_valence) per modality.
        if len(self._motion) > 1:
            self.kalman.predict()
            self.kalman.update(motion, (1.0, 0.0))          # whole-body → arousal
            self.kalman.update(audio, (0.8, 0.2))           # audio arousal → arousal
            self.kalman.update(bark, (0.4, -0.3))           # stress barks → negative valence

    def features(self) -> dict[str, float]:
        """Latest synchrony/latent-state values (all bounded [0,1]/[-1,1])."""
        a = np.asarray(list(self._sway_phase))
        b = np.asarray(list(self._audio_phase))
        plv = phase_locking_value(a, b) if a.size > 2 and b.size > 2 else 0.0

        corr = 0.0
        lag = 0.0
        if len(self._motion) > 4 and len(self._bark) > 4:
            cc = cross_correlation(
                np.asarray(list(self._motion)), np.asarray(list(self._bark)), max_lag=5
            )
            corr = float(cc["correlation"])
            lag = float(cc["best_lag"])

        lat_a, lat_v = self.kalman.state()
        return {
            "sync_plv": float(max(0.0, min(1.0, plv))),
            "sync_corr": float(max(-1.0, min(1.0, corr))),
            "sync_latent_arousal": float(max(0.0, min(1.0, (lat_a + 1.0) / 2.0))),
            "sync_latent_valence": float(max(-1.0, min(1.0, lat_v))),
            "sync_lag": lag,  # telemetry only; not in the feature vector
        }


def _step_phase(prev: float, value: float) -> float:
    """Advance a running phase angle by the stream's current amplitude.

    The step is proportional to (value, positively biased so even a quiet
    stream keeps rotating slowly) and wrapped to [-pi, pi]. Co-modulated
    streams (tail wag going up while audio arousal goes up) advance at the
    same rate -> locked phase -> high PLV. A stream that goes quiet while
    the other stays loud advances at a different rate -> phase separation
    -> PLV collapses. Same step function on both streams preserves the
    coupling sign without scipy.
    """
    return (prev + 0.3 * value + 0.04 + math.pi) % (2 * math.pi) - math.pi


_STATE = _SyncState()


def reset_sync() -> None:
    global _STATE
    _STATE = _SyncState()


def update_sync(features: dict) -> None:
    _STATE.push(features)


def sync_features() -> dict:
    return _STATE.features()


def track_lag() -> float:
    """Best motion↔bark cross-correlation lag (samples)."""
    return _STATE.features().get("sync_lag", 0.0)