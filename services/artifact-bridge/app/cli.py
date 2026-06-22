"""Export ONNX/CoreML artifacts and manifests (delegates ONNX to forecast)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import typer

from app.export_coreml import export_coreml
from app.manifest import build_manifest

app = typer.Typer(help="AARFLingo artifact bridge CLI")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _export_onnx_via_forecast(out_dir: Path) -> Path:
    root = _repo_root()
    forecast = root / "services" / "forecast"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.cli",
            "export-onnx",
            "--out",
            str(out_dir),
        ],
        cwd=str(forecast),
        env={**dict(**__import__("os").environ), "PYTHONPATH": f"{root}:{forecast}"},
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    return Path(payload["path"])


@app.command()
def export(
    out: Path = typer.Option(Path("artifacts/bundles/dev"), "--out", help="Output bundle directory"),
    target: str = typer.Option("onnx", "--target", help="onnx or coreml"),
) -> None:
    if target == "coreml":
        path = export_coreml(out)
    else:
        path = _export_onnx_via_forecast(out)
    manifest = build_manifest(out)
    (out / "manifest.json").write_text(manifest.to_json(), encoding="utf-8")
    typer.echo(f"exported {path}")


if __name__ == "__main__":
    app()
