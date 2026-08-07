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


if __name__ == "__main__":
    app()
