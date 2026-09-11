"""Typer CLI for perception service."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from .vision_train import train_vision
from .breed_train import train_breed
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


@app.command("train-breed")
def train_breed_cmd(
    data_dir: str = typer.Option("data/raw/dog_images/Images", help="Stanford Dogs Images root"),
    epochs: int = typer.Option(12, help="Training epochs"),
    freeze_backbone: int = typer.Option(2, help="Epochs of head-only training before unfreezing"),
    lr: float = typer.Option(2e-3, help="Peak learning rate"),
    out: str = typer.Option("", help="Output weights path (default: artifacts/models/vision/breed.pt)"),
    extra_dir: str = typer.Option("", help="Personal stills dir (<Breed>/*.jpg) merged into training — e.g. data/my_dog/breed"),
) -> None:
    """Fine-tune MobileNetV3-Large on Stanford Dogs for 120-way breed ID."""
    result = train_breed(
        data_dir=Path(data_dir),
        out_weights=Path(out) if out else None,
        epochs=epochs,
        freeze_backbone=freeze_backbone,
        lr=lr,
        extra_dir=Path(extra_dir) if extra_dir else None,
    )
    typer.echo(json.dumps(result, indent=2))


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


@app.command("capture-frames")
def capture_frames_cmd(
    out: str = typer.Option("data/dog/captures", help="Output capture directory"),
    camera: int = typer.Option(0, help="Camera index (used when --source is empty)"),
    frames: int = typer.Option(200, help="Number of frames to capture"),
    interval: float = typer.Option(0.2, help="Seconds between frames (motion-skipped)"),
    source: str = typer.Option("", help="Capture source override: MJPEG URL (e.g. WSL bridge http://host:8766/video/stream) or camera index"),
) -> None:
    """Grab webcam frames of your dog for fine-tuning (YOLO / breed)."""
    from .dog_dataset import capture_frames

    result = capture_frames(Path(out), camera=camera, frames=frames, interval=interval, source=source or None)
    typer.echo(json.dumps(result, indent=2))


@app.command("auto-label-dog")
def auto_label_dog_cmd(
    captures: str = typer.Option("data/dog/captures", help="Captured frames dir"),
    labels: str = typer.Option("data/dog/captures/labels.jsonl", help="Rect labels JSONL to write"),
    conf: float = typer.Option(0.25, help="Min YOLO confidence for a dog box"),
    weights: str = typer.Option("yolov8n.pt", help="Detector weights (COCO classes)"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Replace existing labels instead of keeping them"),
) -> None:
    """Model-assisted labeling: pre-fill labels.jsonl with dog boxes for review."""
    from .dog_dataset import auto_label

    result = auto_label(
        captures_dir=Path(captures),
        labels_path=Path(labels),
        conf=conf,
        weights=weights,
        overwrite=overwrite,
    )
    typer.echo(json.dumps(result, indent=2))


@app.command("prep-dog-yolo")
def prep_dog_yolo_cmd(
    captures: str = typer.Option("data/dog/captures", help="Captured frames dir"),
    labels: str = typer.Option("data/dog/captures/labels.jsonl", help="Rect labels JSONL"),
    out: str = typer.Option("artifacts/dog_yolo_dataset", help="Output YOLO dataset dir"),
    classes: str = typer.Option("dog", help="Comma-separated class names"),
) -> None:
    """Build a YOLO dataset layout (images/ + labels/ + data.yaml) from captures."""
    from .dog_dataset import prep_dog_yolo

    result = prep_dog_yolo(
        captures_dir=Path(captures),
        labels_path=Path(labels),
        out_dir=Path(out),
        classes=[c.strip() for c in classes.split(",") if c.strip()],
    )
    typer.echo(json.dumps(result, indent=2))


@app.command("finetune-dog-yolo")
def finetune_dog_yolo_cmd(
    dataset: str = typer.Option("artifacts/dog_yolo_dataset", help="YOLO dataset dir (prep-dog-yolo output)"),
    epochs: int = typer.Option(30, help="Training epochs"),
    imgsz: int = typer.Option(640, help="Training image size"),
    out: str = typer.Option("artifacts/models/vision/dog_yolo.pt", help="Output weights path"),
) -> None:
    """Fine-tune YOLOv8n on your dog and export dog_yolo.onnx for the runtime."""
    from .dog_dataset import finetune_dog_yolo

    result = finetune_dog_yolo(
        dataset_dir=Path(dataset),
        epochs=epochs,
        imgsz=imgsz,
        out_onnx=Path(out),
    )
    typer.echo(json.dumps(result, indent=2))


@app.command("verify-real")
def verify_real(
    file: str = typer.Option("artifacts/real/vision_features.jsonl", help="JSONL produced by collect-real"),
) -> None:
    rows = load_jsonl(Path(file))
    typer.echo(json.dumps({"file": file, **summarize_rows(rows)}, indent=2))


if __name__ == "__main__":
    app()
