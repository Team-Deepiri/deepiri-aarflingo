"""Edge device inference loop (Jetson / collar pod)."""
from __future__ import annotations

import json
import time
from pathlib import Path

import cv2
import numpy as np


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def run_edge(camera: str | int = 0, use_onnx: bool = True) -> None:
    root = repo_root()
    onnx_path = root / "artifacts" / "bundles" / "default" / "studio" / "triad.onnx"
    session = None
    if use_onnx and onnx_path.exists():
        import onnxruntime as ort

        session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])

    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open camera {camera}")

    import sys

    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "services" / "perception"))
    from app.pipeline import run_pipeline_frame  # type: ignore

    seq: list[list[float]] = []
    from core.feature_spec import vectorize, SEQUENCE_LEN  # type: ignore

    print(json.dumps({"status": "edge_running", "onnx": session is not None}))
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05)
            continue
        features = run_pipeline_frame(frame)
        vec = vectorize(features)
        seq.append(vec)
        if len(seq) > SEQUENCE_LEN:
            seq = seq[-SEQUENCE_LEN:]
        payload = {"intent": "rest", "confidence": 0.5}
        if session and len(seq) == SEQUENCE_LEN:
            flat = np.array([sum(seq, [])], dtype=np.float32)
            out = session.run(None, {"input": flat})
            payload["raw"] = [o.tolist() for o in out]
        print(json.dumps(payload))
        time.sleep(1 / 15)
