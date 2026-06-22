"""Typer CLI for perception service."""
from __future__ import annotations

import json

import typer

from .vision_train import train_vision

app = typer.Typer(help="AARFLingo perception")


@app.command("prepare-vision")
def prepare_vision() -> None:
    result = train_vision()
    typer.echo(json.dumps(result))


if __name__ == "__main__":
    app()
