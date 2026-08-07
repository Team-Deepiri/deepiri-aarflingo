"""Minimal PCM WAV decode (stdlib `wave`, no audio deps)."""
from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

TARGET_SR = 16000


def _resample(x: np.ndarray, src_sr: int, dst_sr: int = TARGET_SR) -> np.ndarray:
    if src_sr == dst_sr or x.size == 0:
        return x
    n_out = max(1, int(round(x.size * dst_sr / src_sr)))
    idx = np.linspace(0, x.size - 1, n_out)
    return np.interp(idx, np.arange(x.size), x).astype(np.float32)


def read_wav(path: Path, target_sr: int = TARGET_SR) -> np.ndarray:
    """Decode a PCM WAV to float32 mono at `target_sr`."""
    with wave.open(str(path), "rb") as wf:
        n_ch, sampwidth, framerate, n_frames = (
            wf.getnchannels(),
            wf.getsampwidth(),
            wf.getframerate(),
            wf.getnframes(),
        )
        raw = wf.readframes(n_frames)
    if sampwidth == 1:
        audio = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sampwidth == 2:
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        audio = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"unsupported sample width {sampwidth} for {path}")
    if n_ch > 1:
        audio = audio.reshape(-1, n_ch).mean(axis=1)
    return _resample(audio, framerate, target_sr).astype(np.float32)
