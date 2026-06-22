from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.mfcc import summarize_audio
from app.synth import synthesize_bark


def test_bark_features_nonzero() -> None:
    wave = synthesize_bark("high", "positive", seed=1)
    summary = summarize_audio(wave)
    assert summary["rms"] > 0.05
