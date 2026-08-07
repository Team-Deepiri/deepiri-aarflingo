"""Typer CLI for perception service."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from .vision_train import train_vision
from .vision_data import (
    collect_features,
    find_images,
    load_jsonl,
    summarize_rows,
    write_jsonl,
)

app = typer.Typer(help="AARFLingo perception")


@app.command("prepare-vision")
def prepare_vision() -> None:
    result = train_vision()
    typer.echo(json.dumps(result))


@app.command("collect-real")
def collect_real(
    directory: str = typer.Option("data/raw/dog_images", help="Root of real dog images (Stanford Dogs layout)"),
    out: str = typer.Option("artifacts/real/vision_features.jsonl", help="JSONL output path"),
    limit: int = typer.Option(0, help="Max images to process (0 = all)"),
) -> None:
    """Run the runtime pipeline over real dog images and persist feature rows."""
    from .pipeline import run_pipeline_frame

    root = Path(directory)
    rows = collect_features(root, run_pipeline_frame, limit=limit)
    written = write_jsonl(rows, Path(out))
    summary = summarize_rows([r.to_dict() for r in rows])
    typer.echo(
        json.dumps(
            {
                "scanned": sum(1 for _ in find_images(root)),
                "collected": len(rows),
                "out": str(written),
                **summary,
            },
            indent=2,
        )
    )


@app.command("verify-real")
def verify_real(
    file: str = typer.Option("artifacts/real/vision_features.jsonl", help="JSONL produced by collect-real"),
) -> None:
    rows = load_jsonl(Path(file))
    typer.echo(json.dumps({"file": file, **summarize_rows(rows)}, indent=2))


if __name__ == "__main__":
    app()
