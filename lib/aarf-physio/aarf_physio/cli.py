"""Typer CLI for aarf-physio."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .sources import PUBLIC_DATASETS
from .train import train_vitals

app = typer.Typer(help="Canine vitals (ECG/IMU) encoder")


@app.command("list-sources")
def list_sources() -> None:
    typer.echo(json.dumps([s.__dict__ for s in PUBLIC_DATASETS], indent=2))


@app.command()
def train(
    epochs: int = typer.Option(20, help="Training epochs"),
    out: Optional[str] = typer.Option(None, help="Checkpoint path"),
) -> None:
    result = train_vitals(epochs=epochs, out_path=Path(out) if out else None)
    typer.echo(json.dumps(result))


if __name__ == "__main__":
    app()
