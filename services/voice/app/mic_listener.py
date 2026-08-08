"""Background microphone listener: bark detection + arousal/valence classification.

Runs a background thread that continuously captures mic audio in short chunks.
When a bark-level energy burst is detected the chunk is classified (arousal,
valence) using the vocal encoder and a BarkEvent is pushed to a shared queue
for the ConversationEngine to consume.

No hard dependency on sounddevice / PyAudio — the listener gracefully
degrades to a no-op when no audio input device is available, so the runtime
still starts in CI or headless environments.

Usage::

    from app.mic_listener import MicListener, BarkEvent
    import queue

    q: queue.Queue[BarkEvent] = queue.Queue()
    listener = MicListener(bark_queue=q)
    listener.start()          # non-blocking
    # ...
    listener.stop()
"""
from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

# ── constants ──────────────────────────────────────────────────────────────
SAMPLE_RATE = 16_000        # Hz  — matches vocal encoder training
CHUNK_DURATION = 0.3        # seconds per capture window
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)
BARK_RMS_THRESHOLD = 0.05   # normalised RMS above which we classify a bark
BARK_ZCR_MIN = 0.02         # zero-crossing rate floor (filters pure hum / DC)
SILENCE_HOLD_S = 0.4        # ignore further bursts within this window (debounce)


@dataclass
class BarkEvent:
    ts: float                  # time.monotonic() when detected
    arousal: str               # "low" | "medium" | "high"
    valence: str               # "negative" | "neutral" | "positive"
    rms: float
    raw: np.ndarray = field(default_factory=lambda: np.zeros(0, dtype=np.float32))


# ── feature helpers (mirrors services/audio/app/mfcc.py, no cross-import) ──

def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x.astype(np.float64) ** 2))) if x.size else 0.0


def _zcr(x: np.ndarray) -> float:
    return float(np.mean(np.abs(np.diff(np.sign(x))))) / 2.0 if x.size > 1 else 0.0


def _mfcc_features(x: np.ndarray, n_coeff: int = 13) -> np.ndarray:
    x = x - np.mean(x)
    n_fft = 512
    hop = 256
    frames = []
    for start in range(0, max(1, len(x) - n_fft), hop):
        frame = x[start : start + n_fft]
        if frame.size < n_fft:
            frame = np.pad(frame, (0, n_fft - frame.size))
        spec = np.abs(np.fft.rfft(frame * np.hanning(n_fft)))
        frames.append(spec)
    if not frames:
        return np.zeros(n_coeff, dtype=np.float32)
    mel = np.mean(np.stack(frames), axis=0)
    mel = np.log1p(mel)
    idx = np.linspace(0, mel.size - 1, n_coeff).astype(int)
    return mel[idx].astype(np.float32)


def _heuristic_classify(x: np.ndarray) -> tuple[str, str]:
    """Classify arousal/valence from raw waveform without a trained model.

    Uses energy + spectral centroid as a cheap proxy when the vocal encoder
    is not loaded (CI, cold start, missing checkpoint).
    """
    rms = _rms(x)
    feats = _mfcc_features(x)
    centroid = float(np.mean(feats))

    if rms > 0.25:
        arousal = "high"
    elif rms > 0.10:
        arousal = "medium"
    else:
        arousal = "low"

    if centroid > 6.5:
        valence = "positive"
    elif centroid < 4.5:
        valence = "negative"
    else:
        valence = "neutral"

    return arousal, valence


# ── optional: try to load the trained vocal encoder ────────────────────────

def _load_encoder(root: Path):
    """Return a callable (waveform -> (arousal, valence)) using the vocal encoder.

    Returns None if the encoder module or checkpoint can't be loaded.
    """
    try:
        import importlib.util
        import sys
        import types

        audio_dir = root / "services" / "audio" / "app"
        pkg = "aarf_audio_mic"
        if pkg not in sys.modules:
            p = types.ModuleType(pkg)
            p.__path__ = [str(audio_dir)]  # type: ignore[attr-defined]
            p.__package__ = pkg
            sys.modules[pkg] = p

        for py in sorted(audio_dir.glob("*.py")):
            if py.name == "__init__.py":
                continue
            mname = f"{pkg}.{py.stem}"
            if mname in sys.modules:
                continue
            spec = importlib.util.spec_from_file_location(
                mname, py, submodule_search_locations=[str(audio_dir)]
            )
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                mod.__package__ = pkg
                sys.modules[mname] = mod
                try:
                    spec.loader.exec_module(mod)  # type: ignore[union-attr]
                except ImportError:
                    pass

        train_mod = sys.modules.get(f"{pkg}.train")
        synth_mod = sys.modules.get(f"{pkg}.synth")
        if train_mod is None or synth_mod is None:
            return None

        import torch

        model = train_mod.VocalEncoder()
        ckpt = train_mod.default_checkpoint()
        if not ckpt.exists():
            return None
        model.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=True))
        model.eval()

        arousal_levels = synth_mod.AROUSAL_LEVELS
        valence_levels = synth_mod.VALENCE_LEVELS

        def _classify(waveform: np.ndarray) -> tuple[str, str]:
            feat = train_mod._feature_tensor(waveform).unsqueeze(0)
            with torch.no_grad():
                a_logits, v_logits = model(feat)
            return arousal_levels[int(a_logits.argmax())], valence_levels[int(v_logits.argmax())]

        return _classify

    except Exception:
        return None


# ── MicListener ─────────────────────────────────────────────────────────────

class MicListener:
    """Captures mic audio in a background thread; pushes BarkEvents to a queue.

    Parameters
    ----------
    bark_queue:
        Queue to receive BarkEvent objects.
    root:
        Project root (auto-detected from this file's location). Used to find
        the vocal encoder checkpoint.
    rms_threshold:
        Normalised RMS above which a chunk is treated as a bark candidate.
    on_error:
        Optional callback(Exception) invoked when the audio stream errors.
    """

    def __init__(
        self,
        bark_queue: "queue.Queue[BarkEvent]",
        root: Path | None = None,
        rms_threshold: float = BARK_RMS_THRESHOLD,
        on_error: Callable[[Exception], None] | None = None,
    ) -> None:
        self.bark_queue = bark_queue
        self.root = root or Path(__file__).resolve().parents[3]
        self.rms_threshold = rms_threshold
        self.on_error = on_error

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_bark_ts: float = 0.0
        self._classify: Callable[[np.ndarray], tuple[str, str]] | None = None
        self._available: bool = True  # set False if no audio device

    # ── public API ──────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background capture thread (non-blocking)."""
        self._stop_event.clear()
        self._classify = _load_encoder(self.root)
        self._thread = threading.Thread(target=self._run, daemon=True, name="aarf-mic")
        self._thread.start()

    def stop(self) -> None:
        """Signal the background thread to stop and wait for it to exit."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    @property
    def available(self) -> bool:
        return self._available

    # ── capture loop ────────────────────────────────────────────────────────

    def _run(self) -> None:
        try:
            import sounddevice as sd  # optional dep
            self._run_sounddevice(sd)
        except Exception as exc:
            # No sounddevice or no device — run a silent no-op loop so the
            # thread stays alive and the runtime doesn't crash.
            self._available = False
            if self.on_error:
                self.on_error(exc)
            self._idle_loop()

    def _run_sounddevice(self, sd) -> None:
        buf: list[np.ndarray] = []

        def _callback(indata: np.ndarray, frames: int, t, status) -> None:
            buf.append(indata[:, 0].copy())

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=CHUNK_SAMPLES,
            callback=_callback,
        ):
            while not self._stop_event.is_set():
                if buf:
                    chunk = np.concatenate(buf)
                    buf.clear()
                    self._process(chunk)
                else:
                    time.sleep(0.01)

    def _idle_loop(self) -> None:
        """Run when no audio device is available — just waits for stop."""
        while not self._stop_event.is_set():
            time.sleep(0.1)

    def _process(self, chunk: np.ndarray) -> None:
        rms = _rms(chunk)
        zcr = _zcr(chunk)
        if rms < self.rms_threshold or zcr < BARK_ZCR_MIN:
            return
        now = time.monotonic()
        if now - self._last_bark_ts < SILENCE_HOLD_S:
            return  # debounce
        self._last_bark_ts = now

        if self._classify is not None:
            try:
                arousal, valence = self._classify(chunk)
            except Exception:
                arousal, valence = _heuristic_classify(chunk)
        else:
            arousal, valence = _heuristic_classify(chunk)

        evt = BarkEvent(ts=now, arousal=arousal, valence=valence, rms=rms, raw=chunk)
        try:
            self.bark_queue.put_nowait(evt)
        except queue.Full:
            pass  # drop if consumer is slow; bark is ephemeral

    # ── inject-for-testing ───────────────────────────────────────────────────

    def inject(self, chunk: np.ndarray) -> None:
        """Directly feed a waveform chunk (bypasses sounddevice — for tests)."""
        self._process(chunk)
