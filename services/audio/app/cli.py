"""Typer CLI for audio service."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .train import SOURCES, train_vocal

app = typer.Typer(help="AARFLingo vocal encoder")


@app.command("list-sources")
def list_sources() -> None:
    typer.echo(json.dumps(list(SOURCES), indent=2))


@app.command()
def train(
    epochs: int = typer.Option(25, help="Training epochs"),
    out: Optional[str] = typer.Option(None, help="Checkpoint path"),
) -> None:
    result = train_vocal(epochs=epochs, out_path=Path(out) if out else None)
    typer.echo(json.dumps(result))


if __name__ == "__main__":
    app()
