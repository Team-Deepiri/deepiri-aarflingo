#!/usr/bin/env python3
"""Verify Aarflingo training artifacts and run a live inference smoke."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _fail(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}), file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    ckpt = ROOT / "artifacts" / "models" / "default" / "triad.pt"
    onnx = ROOT / "artifacts" / "bundles" / "default" / "studio" / "triad.onnx"
    metrics_path = ROOT / "artifacts" / "models" / "default" / "train_metrics.json"
    manifest = ROOT / "artifacts" / "bundles" / "default" / "studio" / "manifest.json"

    if not ckpt.is_file() or ckpt.stat().st_size < 1000:
        _fail(f"checkpoint missing or too small: {ckpt}")
    if not onnx.is_file() or onnx.stat().st_size < 1000:
        _fail(f"onnx missing or too small: {onnx}")
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
    play_row.update({"dog_present": 1.0, "gaze_toy": 0.88, "motion": 0.2})
    pred = infer_sequence([vectorize(play_row)] * 15)
    if not pred.intent_id or pred.confidence <= 0:
        _fail("inference returned empty prediction")

    out = {
        "ok": True,
        "checkpoint_bytes": ckpt.stat().st_size,
        "onnx_bytes": onnx.stat().st_size,
        "best_val_acc": best_acc,
        "smoke_intent": pred.intent_id,
        "smoke_confidence": pred.confidence,
        "manifest_present": manifest.is_file(),
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
