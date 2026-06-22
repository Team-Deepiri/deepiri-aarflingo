"""Live inference engine: webcam → perception → forecast → gate."""
from __future__ import annotations

import asyncio
import importlib.util
import json
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

    def __post_init__(self) -> None:
        if self.store is None:
            self.store = FeedbackStore(ROOT / "artifacts" / "feedback" / "aarf.db")


STATE = LiveState()


def _load_coupling_matrix() -> dict:
    path = ROOT / "ethogram" / "coupling-matrix.json"
    return json.loads(path.read_text(encoding="utf-8"))


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


def process_frame(frame_bgr: np.ndarray) -> dict[str, Any]:
    features = run_pipeline_frame(frame_bgr)
    vec = vectorize(features)
    STATE.sequence.append(vec)
    seq = list(STATE.sequence)
    try:
        pred = infer_sequence(seq)
    except Exception:
        pred = heuristic_predict(features)

    gate = gate_decision(pred)
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
        "intent_probs": pred.intent_probs or {},
        "gate": gate,
        "features": {k: features[k] for k in features if k != "bbox"},
        "dog_present": bool(features.get("dog_present", 0)),
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


def process_jpeg(jpeg_bytes: bytes) -> dict[str, Any]:
    import cv2

    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"type": "error", "message": "bad jpeg"}
    return process_frame(frame)
