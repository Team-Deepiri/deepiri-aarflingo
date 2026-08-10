"""Prepare vision artifacts (YOLOv8 dog detector + Stanford Dogs breed classifier)."""
from __future__ import annotations

import json
from pathlib import Path

from .breed import default_breed_labels, default_breed_weights
from .yolo_detect import default_onnx, default_weights, export_dog_onnx, prepare_yolo_weights


def train_vision(out_dir: Path | None = None) -> dict:
    root = Path(__file__).resolve().parents[3]
    weights = prepare_yolo_weights(default_weights(root))
    onnx_path = export_dog_onnx(weights, default_onnx(root))
    manifest = {
        "model": "yolov8n",
        "coco_class": "dog",
        "class_id": 16,
        "weights": str(weights),
        "onnx": str(onnx_path),
        "breed_weights": str(default_breed_weights(root)),
        "breed_labels": str(default_breed_labels(root)),
        "sources": ["coco-pretrained", "ultralytics-yolov8", "stanford-dogs"],
        "notes": "Fine-tune on home camera clips via services/perception when labeled data is available.",
    }
    out = out_dir or root / "artifacts" / "manifests"
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "vision-yolo.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"weights": str(weights), "onnx": str(onnx_path), "manifest": str(manifest_path)}
