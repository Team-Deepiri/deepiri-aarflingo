"""Feedback CLI."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from .store import FeedbackStore

app = typer.Typer(help="AARFLingo feedback store")


def _db() -> FeedbackStore:
    root = Path(__file__).resolve().parents[3]
    return FeedbackStore(root / "artifacts" / "feedback" / "aarf.db")


@app.command()
def metrics() -> None:
    typer.echo(json.dumps(_db().metrics()))


@app.command()
def export(out: Path = typer.Option(..., "--out")) -> None:
    n = _db().export_training_json(out)
    typer.echo(json.dumps({"exported": n, "path": str(out)}))


@app.command()
def recent(limit: int = 20) -> None:
    typer.echo(json.dumps(_db().recent_predictions(limit)))


if __name__ == "__main__":
    app()
