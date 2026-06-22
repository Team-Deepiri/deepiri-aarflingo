#!/usr/bin/env python3
"""Verify multimodal Aarflingo training artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _fail(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}), file=sys.stderr)
    raise SystemExit(1)


def _check_file(path: Path, min_bytes: int, label: str) -> int:
    if not path.is_file() or path.stat().st_size < min_bytes:
        _fail(f"{label} missing or too small: {path}")
    return path.stat().st_size


def main() -> None:
    ckpt = ROOT / "artifacts" / "models" / "default" / "triad.pt"
    onnx = ROOT / "artifacts" / "bundles" / "default" / "studio" / "triad.onnx"
    vocal = ROOT / "artifacts" / "models" / "default" / "vocal.pt"
    vitals = ROOT / "artifacts" / "models" / "default" / "vitals.pt"
    yolo_onnx = ROOT / "artifacts" / "bundles" / "default" / "studio" / "dog_yolo.onnx"
    metrics_path = ROOT / "artifacts" / "models" / "default" / "train_metrics.json"
    manifest = ROOT / "artifacts" / "bundles" / "default" / "studio" / "manifest.json"

    ckpt_bytes = _check_file(ckpt, 1000, "triad checkpoint")
    onnx_bytes = _check_file(onnx, 1000, "triad onnx")
    vocal_bytes = _check_file(vocal, 500, "vocal checkpoint")
    vitals_bytes = _check_file(vitals, 500, "vitals checkpoint")

    yolo_bytes = 0
    if yolo_onnx.is_file():
        yolo_bytes = yolo_onnx.stat().st_size

    if not metrics_path.is_file():
        _fail(f"train metrics missing: {metrics_path}")

    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    best_acc = float(metrics.get("best_val_acc", 0.0))
    if best_acc < 0.5:
        _fail(f"best_val_acc below threshold: {best_acc}")

    forecast = ROOT / "services" / "forecast"
    for p in (str(ROOT), str(forecast)):
        if p not in sys.path:
            sys.path.insert(0, p)

    from app.infer import infer_sequence, load_checkpoint  # type: ignore
    from core.feature_spec import FEATURE_NAMES, vectorize

    load_checkpoint(ckpt)
    play_row = {name: 0.1 for name in FEATURE_NAMES}
    play_row.update(
        {
            "dog_present": 1.0,
            "gaze_toy": 0.88,
            "motion": 0.2,
            "vision_yolo_dog_conf": 0.9,
            "audio_arousal": 0.85,
            "audio_valence": 0.75,
            "audio_bark_prob": 0.7,
            "ecg_hr_norm": 0.55,
            "ecg_stress": 0.2,
            "imu_activity": 0.75,
            "imu_posture_static": 0.3,
        }
    )
    pred = infer_sequence([vectorize(play_row)] * 15)
    if not pred.intent_id or pred.confidence <= 0:
        _fail("inference returned empty prediction")

    out = {
        "ok": True,
        "checkpoint_bytes": ckpt_bytes,
        "onnx_bytes": onnx_bytes,
        "vocal_bytes": vocal_bytes,
        "vitals_bytes": vitals_bytes,
        "yolo_onnx_bytes": yolo_bytes,
        "best_val_acc": best_acc,
        "smoke_intent": pred.intent_id,
        "smoke_confidence": pred.confidence,
        "manifest_present": manifest.is_file(),
        "feature_dim": len(FEATURE_NAMES),
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
