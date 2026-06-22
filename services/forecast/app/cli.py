"""Typer CLI for forecast service."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .export_onnx import export_onnx
from .infer import infer_batch
from .train import train_epochs

app = typer.Typer(help="AARFLingo forecast CLI")


@app.command()
def train(
    epochs: int = typer.Option(default=25, help="Training epochs"),
    feedback: Optional[str] = typer.Option(default=None, help="Feedback export JSON path"),
    out: Optional[str] = typer.Option(default=None, help="Checkpoint .pt path"),
) -> None:
    result = train_epochs(
        epochs=epochs,
        feedback_path=Path(feedback) if feedback else None,
        out_path=Path(out) if out else None,
    )
    typer.echo(json.dumps(result))


@app.command()
def build_default() -> None:
    result = train_epochs(epochs=30)
    typer.echo(json.dumps({"status": "ok", **result}))


@app.command("export-onnx")
def export_onnx_cmd(
    out: Optional[str] = typer.Option(None, "--out", help="Output directory for triad.onnx"),
) -> None:
    root = Path(__file__).resolve().parents[3]
    out_dir = Path(out) if out else root / "artifacts" / "bundles" / "default" / "studio"
    path = export_onnx(out_dir)
    typer.echo(json.dumps({"status": "ok", "path": str(path)}))


@app.command()
def infer(features_json: str) -> None:
    rows = json.loads(features_json)
    preds = infer_batch(rows)
    typer.echo(json.dumps([p.__dict__ for p in preds]))


if __name__ == "__main__":
    app()
