"""Write a minimal CoreML placeholder bundle marker."""
from __future__ import annotations

import json
from pathlib import Path


def export_coreml(out_dir: Path, model_name: str = "triad") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    marker = out_dir / f"{model_name}.mlmodel.json"
    marker.write_text(
        json.dumps({"format": "coreml-placeholder", "model": model_name}),
        encoding="utf-8",
    )
    return marker
