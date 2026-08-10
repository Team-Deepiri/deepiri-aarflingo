"""Live inference engine: webcam → perception → forecast → gate."""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
import time
import types
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from app.paths import setup_paths

ROOT = setup_paths()


def _load_service_package(service: str, module: str):
    """Load services/{service}/app as an isolated package (no clash with runtime app)."""
    root = setup_paths()
    app_dir = root / "services" / service / "app"
    pkg_name = f"aarf_{service}"

    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(app_dir)]  # type: ignore[attr-defined]
        pkg.__package__ = pkg_name
        sys.modules[pkg_name] = pkg

    pending: list[tuple[object, object]] = []
    for py in sorted(app_dir.glob("*.py")):
        if py.name == "__init__.py":
            continue
        mod_name = f"{pkg_name}.{py.stem}"
        if mod_name in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(
            mod_name,
            py,
            submodule_search_locations=[str(app_dir)],
        )
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = pkg_name
        sys.modules[mod_name] = mod
        pending.append((spec, mod))

    loaded: set[object] = set()
    for _ in range(len(pending) + 2):
        for spec, mod in pending:
            if mod in loaded:
                continue
            try:
                spec.loader.exec_module(mod)
                loaded.add(mod)
            except ImportError:
                continue
        if len(loaded) == len(pending):
            break
    if len(loaded) != len(pending):
        raise ImportError(f"Failed to load all modules for services/{service}/app")

    key = f"{pkg_name}.{module}"
    if key not in sys.modules:
        raise ImportError(f"Module {key} not found under services/{service}/app")
    return sys.modules[key]


def _load_file(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_perception = _load_service_package("perception", "pipeline")
_forecast_infer = _load_service_package("forecast", "infer")
_forecast_triad = _load_service_package("forecast", "triad_model")
_feedback = _load_service_package("feedback", "store")
_fs = _load_file(ROOT / "core" / "feature_spec.py", "feature_spec")

vectorize = _fs.vectorize
run_pipeline_frame = _perception.run_pipeline_frame
infer_sequence = _forecast_infer.infer_sequence
heuristic_predict = _forecast_triad.heuristic_predict
TriadPrediction = _forecast_triad.TriadPrediction
FeedbackStore = _feedback.FeedbackStore

_VOICE_ENABLED = os.environ.get("VOICE_ENABLED", "0") == "1"
_VOICE = None
_VOICE_CONV = None
if _VOICE_ENABLED:
    try:
        _VOICE = _load_service_package("voice", "dog_voice")
        _VOICE_CONV = _load_service_package("voice", "conversation")
    except (ImportError, ModuleNotFoundError):
        _VOICE_ENABLED = False


@dataclass
class LiveState:
    running: bool = False
    session_id: str | None = None
    dog_id: str = "default"
    camera_index: int | str = 0
    sequence: deque = field(default_factory=lambda: deque(maxlen=15))
    last_prediction_id: str | None = None
    last_frame_jpeg: bytes | None = None
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    store: FeedbackStore | None = None
    latest_audio_modality: dict[str, float] = field(default_factory=dict)
    voice: object | None = None
    conversation: object | None = None   # ConversationEngine when VOICE_ENABLED
    mic_listener: object | None = None   # MicListener when VOICE_ENABLED
    started_at: float | None = None      # monotonic time live session began
    frame_count: int = 0                 # frames run through process_frame
    infer_count: int = 0                 # predictions produced
    infer_total_ms: float = 0.0          # cumulative inference latency

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = FeedbackStore(ROOT / "artifacts" / "feedback" / "aarf.db")


STATE = LiveState()


def update_audio_modality(audio_arousal: float = 0.0, audio_valence: float = 0.0, audio_bark_prob: float = 0.0) -> dict[str, float]:
    mod = {
        "audio_arousal": float(audio_arousal),
        "audio_valence": float(audio_valence),
        "audio_bark_prob": float(audio_bark_prob),
    }
    STATE.latest_audio_modality = mod
    return mod


def _load_coupling_matrix() -> dict:
    path = ROOT / "ethogram" / "coupling-matrix.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _ensure_conversation() -> None:
    """Lazily initialise DogVoice + ConversationEngine + MicListener."""
    if not _VOICE_ENABLED or _VOICE is None or _VOICE_CONV is None:
        return
    if STATE.voice is None:
        STATE.voice = _VOICE.DogVoice(_VOICE.SpeechClient())
    if STATE.conversation is None:
        STATE.conversation = _VOICE_CONV.ConversationEngine(
            voice=STATE.voice,
            store=STATE.store,
        )
    if STATE.mic_listener is None:
        _mic_mod = _load_service_package("voice", "mic_listener")
        import queue as _q
        bark_queue: _q.Queue = _q.Queue(maxsize=32)
        mic = _mic_mod.MicListener(bark_queue=bark_queue)

        # Wire the bark queue into the conversation engine via a drain thread
        import threading

        def _bark_drain() -> None:
            while STATE.running or not bark_queue.empty():
                try:
                    evt = bark_queue.get(timeout=0.2)
                    if STATE.conversation is not None:
                        result = STATE.conversation.on_bark(evt)
                        if result:
                            asyncio.run_coroutine_threadsafe(
                                broadcast({"type": "bark", **result}),
                                asyncio.get_event_loop(),
                            )
                except Exception:
                    pass

        mic.start()
        threading.Thread(target=_bark_drain, daemon=True, name="aarf-bark-drain").start()
        STATE.mic_listener = mic


def _conversation_speak(pred: TriadPrediction) -> dict | None:
    """Speak via ConversationEngine (learns from bark responses) when VOICE_ENABLED.

    Falls back to the legacy one-shot _speak_for when the conversation engine
    is not initialised.
    """
    if not _VOICE_ENABLED:
        return None
    _ensure_conversation()
    if STATE.conversation is None:
        return _speak_for_legacy(pred)
    result = STATE.conversation.on_prediction(pred)
    if not result:
        return None
    # save the audio file for playback / debugging
    audio = STATE.voice.client.synthesize(result["phrase"]) if STATE.voice else b""
    if audio:
        voice_dir = ROOT / "artifacts" / "voice"
        voice_dir.mkdir(parents=True, exist_ok=True)
        fp = voice_dir / f"utterance-{int(time.time() * 1000)}.wav"
        fp.write_bytes(audio)
        result["saved"] = str(fp)
    return result


def _speak_for_legacy(pred: TriadPrediction) -> dict | None:
    """Original one-shot speak (no learning). Kept as a fallback."""
    if not _VOICE_ENABLED or _VOICE is None:
        return None
    if STATE.voice is None:
        STATE.voice = _VOICE.DogVoice(_VOICE.SpeechClient())
    audio = STATE.voice.respond_to_prediction(pred)
    if not audio:
        return None
    voice_dir = ROOT / "artifacts" / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    fp = voice_dir / f"utterance-{int(time.time() * 1000)}.wav"
    fp.write_bytes(audio)
    return {"phrase": STATE.voice.last_phrase, "saved": str(fp)}


def gate_decision(pred: TriadPrediction) -> str:
    matrix = _load_coupling_matrix()
    forbidden = matrix.get("forbidden_pairs", [])
    for rule in forbidden:
        if rule.get("intent") == pred.intent_id and rule.get("behavior") == pred.behavior_id:
            return "reject"
        if rule.get("intent") == pred.intent_id and rule.get("emotion") == pred.emotion_id:
            return "reject"
    for triple in matrix.get("triples", []):
        if (
            triple["intent"] == pred.intent_id
            and triple["emotion"] == pred.emotion_id
            and triple["behavior"] == pred.behavior_id
        ):
            if pred.confidence >= 0.55:
                return "pass"
            return "review"
    return "review"


def process_frame(frame_bgr: np.ndarray, audio_modality: dict[str, float] | None = None) -> dict[str, Any]:
    if STATE.started_at is None:
        STATE.started_at = time.monotonic()
    STATE.frame_count += 1
    features = run_pipeline_frame(frame_bgr)
    if audio_modality:
        features.update(audio_modality)
    elif STATE.latest_audio_modality:
        features.update(STATE.latest_audio_modality)
    vec = vectorize(features)
    STATE.sequence.append(vec)
    seq = list(STATE.sequence)
    t0 = time.perf_counter()
    try:
        pred = infer_sequence(seq)
    except Exception:
        pred = heuristic_predict(features)
    STATE.infer_total_ms += (time.perf_counter() - t0) * 1000
    STATE.infer_count += 1

    gate = gate_decision(pred)
    voice = _conversation_speak(pred) if float(features.get("dog_present", 0)) >= 0.5 else None
    pid = None
    if STATE.store:
        if not STATE.session_id:
            STATE.session_id = STATE.store.start_session(dog_id=STATE.dog_id, source="browser")
        pid = STATE.store.log_prediction(
            STATE.session_id,
            pred.intent_id,
            pred.emotion_id,
            pred.behavior_id,
            pred.confidence,
            features,
            seq,
        )
        STATE.last_prediction_id = pid

    return {
        "ts_ms": int(time.time() * 1000),
        "prediction_id": pid,
        "intent": pred.intent_id,
        "emotion": pred.emotion_id,
        "behavior": pred.behavior_id,
        "confidence": pred.confidence,
        "margin": pred.margin,
        "intent_probs": pred.intent_probs or {},
        "gate": gate,
        "voice": voice,
        "features": {k: features[k] for k in features if k != "bbox"},
        "sequence": seq[-10:],
        "dog_present": bool(features.get("dog_present", 0)),
    }


def live_status() -> dict:
    """Streaming telemetry for the studio's live metrics rail."""
    now = time.monotonic()
    elapsed = (now - STATE.started_at) if STATE.started_at else 0.0
    fps = (STATE.frame_count / elapsed) if elapsed > 0 else 0.0
    avg_infer_ms = (STATE.infer_total_ms / STATE.infer_count) if STATE.infer_count else 0.0
    return {
        "running": STATE.running,
        "session_id": STATE.session_id,
        "dog_id": STATE.dog_id,
        "camera": str(STATE.camera_index),
        "frames": STATE.frame_count,
        "predictions": STATE.infer_count,
        "fps": round(fps, 1),
        "avg_infer_ms": round(avg_infer_ms, 1),
        "sequence_len": len(STATE.sequence),
        "sequence_capacity": STATE.sequence.maxlen,
        "uptime_s": round(elapsed, 1),
    }


async def broadcast(msg: dict) -> None:
    dead: list[asyncio.Queue] = []
    for q in STATE.subscribers:
        try:
            q.put_nowait(msg)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        STATE.subscribers.remove(q)


async def webcam_loop(camera: int | str) -> None:
    import cv2

    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        hint = ""
        if isinstance(camera, int):
            hint = " On WSL, start scripts/webcam/start_webcam_bridge.ps1 on Windows and use bridge mode."
        await broadcast({"type": "error", "message": f"Cannot open camera {camera}.{hint}"})
        STATE.running = False
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    STATE.running = True
    source = "bridge" if isinstance(camera, str) else "webcam"
    STATE.session_id = STATE.store.start_session(dog_id=STATE.dog_id, source=source)

    try:
        while STATE.running:
            ok, frame = cap.read()
            if not ok:
                await asyncio.sleep(0.05)
                continue
            _, jpeg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            STATE.last_frame_jpeg = jpeg.tobytes()
            payload = process_frame(frame)
            payload["type"] = "prediction"
            await broadcast(payload)
            await asyncio.sleep(1 / 15)
    finally:
        cap.release()
        STATE.running = False
        if STATE.mic_listener is not None:
            try:
                STATE.mic_listener.stop()
            except Exception:
                pass
        if STATE.conversation is not None:
            try:
                STATE.conversation.stop()
            except Exception:
                pass


def process_jpeg(jpeg_bytes: bytes) -> dict[str, Any]:
    import cv2

    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"type": "error", "message": "bad jpeg"}
    return process_frame(frame)
