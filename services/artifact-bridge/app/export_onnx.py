"""Write a minimal ONNX placeholder bundle marker."""
from __future__ import annotations

import json
from pathlib import Path


def export_onnx(out_dir: Path, model_name: str = "triad") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    marker = out_dir / f"{model_name}.onnx.json"
    marker.write_text(
        json.dumps({"format": "onnx-placeholder", "model": model_name, "opset": 17}),
        encoding="utf-8",
    )
    return marker
