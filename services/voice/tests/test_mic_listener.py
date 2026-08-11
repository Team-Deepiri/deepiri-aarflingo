"""MicListener: continuous audio modality feed for the frame pipeline."""
from __future__ import annotations

import queue
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from app.mic_listener import AROUSAL_NUM, VALENCE_NUM, MicListener


def test_modality_callback_fires_on_every_chunk() -> None:
    received: list[dict[str, float]] = []
    mic = MicListener(
        bark_queue=queue.Queue(maxsize=4),
        modality_callback=received.append,
    )
    loud = np.full(4800, 0.3, dtype=np.float32)
    quiet = np.zeros(4800, dtype=np.float32)
    mic._process(loud)
    mic._process(quiet)

    assert len(received) == 2
    loud_mod, quiet_mod = received
    # loud chunk: heuristic rms 0.3 > 0.25 -> high arousal, high bark_prob
    assert loud_mod["audio_arousal"] == AROUSAL_NUM["high"]
    assert loud_mod["audio_bark_prob"] == 1.0
    # quiet chunk: low arousal, no bark
    assert quiet_mod["audio_arousal"] == AROUSAL_NUM["low"]
    assert quiet_mod["audio_bark_prob"] == 0.0


def test_bark_event_still_emitted_and_carries_raw() -> None:
    q: queue.Queue = queue.Queue(maxsize=4)
    mic = MicListener(bark_queue=q)
    mic._last_bark_ts = 0.0
    loud = np.full(4800, 0.5, dtype=np.float32)
    loud[::2] = -0.5  # non-zero ZCR so it passes the bark gate
    mic._process(loud)

    assert q.qsize() == 1
    evt = q.get()
    assert evt.raw.size == 4800
