"""Export TriadNet to a CoreML model (from the ONNX artifact).

Requires `coremltools` + the ONNX export to exist. When coremltools is not
installed (e.g. Linux dev boxes), we write a marker so CI/bundle scripts fail
loudly instead of shipping a placeholder.

Note: CoreML model files are only produced on macOS (or a machine with
coremltools). The mobile bundle script, scripts/mobile/bundle-mobile-models.sh,
calls this target and copies the result into the iOS app.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def export_coreml(out_dir: Path, model_name: str = "triad") -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)

    from app.cli import _export_onnx_via_forecast  # lazy: avoids import cycle

    try:
        import coremltools as ct
    except ImportError:
        marker = out_dir / f"{model_name}.mlmodel.json"
        marker.write_text(
            json.dumps(
                {
                    "format": "coreml-unavailable",
                    "model": model_name,
                    "reason": "coremltools not installed — run on macOS: poetry install (coremltools extra)",
                }
            ),
            encoding="utf-8",
        )
        return marker

    onnx_path = _export_onnx_via_forecast(out_dir)
    mlmodel = ct.converters.onnx.convert(
        model=str(onnx_path),
        minimum_ios_deployment_target="16.0",
        convert_to="mlprogram",
    )
    out_path = out_dir / f"{model_name}.mlpackage"
    if out_path.exists():
        shutil.rmtree(out_path)
    mlmodel.save(str(out_path))
    return out_path


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/bundles/dev")
    p = export_coreml(out)
    print(json.dumps({"path": str(p), "format": p.suffix or "mlmodel"}))
