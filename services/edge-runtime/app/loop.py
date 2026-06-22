"""Edge device inference loop (Jetson / collar pod)."""
from __future__ import annotations

import json
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _setup_imports(root: Path) -> None:
    for p in (str(root), str(root / "services" / "perception")):
        if p not in sys.path:
            sys.path.insert(0, p)


def run_edge(camera: str | int = 0, use_onnx: bool = True, max_frames: int | None = None) -> None:
    root = repo_root()
    _setup_imports(root)
    from core.feature_spec import SEQUENCE_LEN, vectorize  # noqa: E402
    from core.onnx_decode import decode_onnx_outputs  # noqa: E402
    from app.pipeline import run_pipeline_frame  # type: ignore  # noqa: E402

    onnx_path = root / "artifacts" / "bundles" / "default" / "studio" / "triad.onnx"
    session = None
    if use_onnx and onnx_path.exists():
        import onnxruntime as ort

        session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])

    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open camera {camera}")

    seq: deque[list[float]] = deque(maxlen=SEQUENCE_LEN)
    frames = 0
    print(json.dumps({"status": "edge_running", "onnx": session is not None, "camera": str(camera)}))
    while max_frames is None or frames < max_frames:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue
        features = run_pipeline_frame(frame)
        seq.append(vectorize(features))
        payload: dict = {
            "intent": "rest",
            "emotion": "calm",
            "behavior": "yawning",
            "confidence": 0.5,
            "dog_present": bool(features.get("dog_present", 0)),
        }
        if session and len(seq) == SEQUENCE_LEN:
            flat = np.array([sum(seq, [])], dtype=np.float32)
            intent_p, emotion_p, behavior_p = session.run(None, {"input": flat})
            decoded = decode_onnx_outputs(intent_p[0], emotion_p[0], behavior_p[0])
            payload.update(
                {
                    "intent": decoded.intent,
                    "emotion": decoded.emotion,
                    "behavior": decoded.behavior,
                    "confidence": decoded.confidence,
                    "intent_probs": decoded.intent_probs,
                }
            )
        print(json.dumps(payload))
        frames += 1
        time.sleep(1 / 15)
    cap.release()
