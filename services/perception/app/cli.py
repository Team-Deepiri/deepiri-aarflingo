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


@app.command("track-demo")
def track_demo(
    camera: int = typer.Option(0, help="Camera index"),
    frames: int = typer.Option(120, help="Number of frames to process"),
) -> None:
    """Stream webcam frames through the multi-dog tracker and print tracks."""
    import cv2

    from .pipeline import run_pipeline_frame

    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise typer.Exit("cannot open camera")
    for _ in range(frames):
        ok, frame = cap.read()
        if not ok:
            break
        feats = run_pipeline_frame(frame)
        print(
            json.dumps(
                {
                    "n_dogs": feats.get("n_dogs"),
                    "pose_head_y": round(float(feats.get("pose_head_y", 0)), 3),
                    "pose_play_bow": round(float(feats.get("pose_play_bow", 0)), 3),
                    "track_stability": round(float(feats.get("track_stability", 0)), 3),
                    "motion": round(float(feats.get("motion", 0)), 3),
                }
            )
        )
    cap.release()


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
