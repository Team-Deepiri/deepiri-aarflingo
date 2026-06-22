"""Typer CLI for forecast service."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from .infer import infer_batch
from .train import train_epochs

app = typer.Typer(help="AARFLingo forecast CLI")


@app.command()
def train(
    epochs: int = 25,
    feedback: Path | None = typer.Option(None, "--feedback"),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    result = train_epochs(epochs=epochs, feedback_path=feedback, out_path=out)
    typer.echo(json.dumps(result))


@app.command()
def build_default() -> None:
    result = train_epochs(epochs=30)
    typer.echo(json.dumps({"status": "ok", **result}))


@app.command()
def infer(features_json: str) -> None:
    rows = json.loads(features_json)
    preds = infer_batch(rows)
    typer.echo(json.dumps([p.__dict__ for p in preds]))


if __name__ == "__main__":
    app()
