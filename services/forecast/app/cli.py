"""Typer CLI for forecast service."""
from __future__ import annotations

import json

import typer

from app.infer import infer_batch
from app.train import train_epoch

app = typer.Typer(help="AARFLingo forecast CLI")


@app.command()
def train() -> None:
    loss = train_epoch()
    typer.echo(json.dumps({"loss": loss}))


@app.command()
def infer(features_json: str) -> None:
    rows = json.loads(features_json)
    preds = infer_batch(rows)
    typer.echo(json.dumps([p.__dict__ for p in preds]))


if __name__ == "__main__":
    app()
