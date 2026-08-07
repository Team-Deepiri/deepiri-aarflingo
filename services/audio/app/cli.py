"""Typer CLI for audio service."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer

from .barkopedia import class_counts, load_barkopedia
from .train import SOURCES, train_vocal

app = typer.Typer(help="AARFLingo vocal encoder")


@app.command("list-sources")
def list_sources() -> None:
    typer.echo(json.dumps(list(SOURCES), indent=2))


@app.command()
def train(
    epochs: int = typer.Option(25, help="Training epochs"),
    out: Optional[str] = typer.Option(None, help="Checkpoint path"),
    data: Optional[str] = typer.Option(None, help="Path to Barkopedia dataset root"),
    synth_per_combo: int = typer.Option(8, help="Synthetic clips per (arousal, valence) combo"),
) -> None:
    data_dir = Path(data) if data else None
    result = train_vocal(epochs=epochs, out_path=Path(out) if out else None, data_dir=data_dir, synth_per_combo=synth_per_combo)
    typer.echo(json.dumps(result))


@app.command("scan")
def scan(data: str = typer.Option(..., help="Path to Barkopedia dataset root")) -> None:
    samples = load_barkopedia(Path(data))
    typer.echo(
        json.dumps(
            {"found": len(samples), "by_class": class_counts(samples)},
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
