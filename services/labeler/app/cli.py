"""Typer CLI for labeler service."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from app.anticipate import build_anticipation
from app.review import enqueue

app = typer.Typer(help="AARFLingo labeler CLI")


@app.command()
def review(
    event_id: str,
    prediction_json: str = typer.Option(..., help="JSON triad prediction"),
    threshold: float = 0.5,
) -> None:
    prediction = json.loads(prediction_json)
    item = enqueue(event_id, prediction, threshold)
    if item is None:
        typer.echo("ok: no review needed")
        raise typer.Exit(0)
    typer.echo(json.dumps({"event_id": item.event_id, "reason": item.reason}))


@app.command()
def anticipate(intent: str, emotion: str, behavior: str, ts: int = 0) -> None:
    label = build_anticipation(ts, intent, emotion, behavior)
    typer.echo(json.dumps(label.__dict__))


if __name__ == "__main__":
    app()
