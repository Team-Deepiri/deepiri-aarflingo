"""Dog YOLO fine-tune tooling — capture, prep, and train on the user's dog.

End-to-end flow (all commands under `aarflingo-perception`):

  1. `capture-frames`      grab webcam frames into data/dog/captures
  2. label them            rects go in a JSONL: {file, cls, x, y, w, h} (normalized 0–1)
  3. `prep-dog-yolo`       build the YOLO layout (images/ + labels/ + data.yaml)
  4. `finetune-dog-yolo`   ultralytics train + export dog_yolo.onnx

The resulting ONNX replaces the generic COCO dog detector with one that is
tuned to this specific dog, improving downstream breed + behavior features.
"""
from __future__ import annotations

import json
import random
import shutil
from pathlib import Path

import yaml

DEFAULT_CAPTURES = Path("data/dog/captures")
DEFAULT_LABELS = Path("data/dog/captures/labels.jsonl")
DEFAULT_DATASET = Path("artifacts/dog_yolo_dataset")
DEFAULT_CLASSES = ["dog"]


# ── capture ────────────────────────────────────────────────────────────────

def capture_frames(
    out_dir: Path = DEFAULT_CAPTURES,
    camera: int = 0,
    frames: int = 200,
    interval: float = 0.2,
) -> dict:
    """Grab `frames` webcam frames into `out_dir` (jpg). Motion-skipped."""
    import cv2

    out_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open camera {camera}")
    written = 0
    prev_gray: object | None = None
    for i in range(frames):
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Skip near-duplicate frames — labels are wasted on them.
        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            if float(diff.mean()) < 3.0:
                prev_gray = gray
                continue
        prev_gray = gray
        path = out_dir / f"frame_{written:05d}.jpg"
        cv2.imwrite(str(path), frame)
        written += 1
        if interval:
            import time

            time.sleep(interval)
    cap.release()
    return {"out": str(out_dir), "captured": written, "camera": camera}


# ── labeling / prep ───────────────────────────────────────────────────────

def load_labels(path: Path = DEFAULT_LABELS) -> list[dict]:
    """Load rect labels. Rows: {"file", "cls", "x", "y", "w", "h"} normalized 0–1."""
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if "file" not in obj:
            continue
        rows.append(obj)
    return rows


def prep_dog_yolo(
    captures_dir: Path = DEFAULT_CAPTURES,
    labels_path: Path = DEFAULT_LABELS,
    out_dir: Path = DEFAULT_DATASET,
    classes: list[str] | None = None,
    train_frac: float = 0.85,
    seed: int = 42,
) -> dict:
    """Convert captures + JSONL labels into a YOLO layout: images/ + labels/ + data.yaml.

    Labels with a `.txt` next to the image (already YOLO format) are used
    verbatim; JSONL rects are converted to YOLO txt. Files without a label get
    an empty label file (background class) and are still usable for a dog-only
    detector.
    """
    classes = classes or DEFAULT_CLASSES
    class_index = {c: i for i, c in enumerate(classes)}

    out_dir.mkdir(parents=True, exist_ok=True)
    for split in ("train", "val"):
        for sub in ("images", "labels"):
            (out_dir / split / sub).mkdir(parents=True, exist_ok=True)

    images = sorted(p for p in captures_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not images:
        raise RuntimeError(f"no images in {captures_dir}")
    rng = random.Random(seed)
    rng.shuffle(images)
    n_train = max(1, int(len(images) * train_frac))
    splits = {"train": images[:n_train], "val": images[n_train:]}

    jsonl_rows = load_labels(labels_path)
    by_file = {Path(r["file"]).name: r for r in jsonl_rows}

    converted = 0
    for split, files in splits.items():
        for src in files:
            dst_img = out_dir / split / "images" / src.name
            shutil.copy2(src, dst_img)
            label_txt = src.with_suffix(".txt")
            out_txt = out_dir / split / "labels" / src.with_suffix(".txt").name
            row = by_file.get(src.name)
            if label_txt.exists():
                shutil.copy2(label_txt, out_txt)
                continue
            if row:
                cls = row.get("cls", classes[0])
                idx = class_index.get(cls, 0)
                x = float(row.get("x", 0))
                y = float(row.get("y", 0))
                w = float(row.get("w", 0.5))
                h = float(row.get("h", 0.5))
                # YOLO wants cx, cy, w, h; JSONL accepts either x,y (center) or x,y (top-left).
                # We document x,y as CENTER to match YOLO semantics.
                out_txt.write_text(f"{idx} {x:.6f} {y:.6f} {w:.6f} {h:.6f}\n", encoding="utf-8")
                converted += 1
            else:
                out_txt.write_text("", encoding="utf-8")

    data_yaml = out_dir / "data.yaml"
    data_yaml.write_text(
        yaml.safe_dump(
            {
                "path": str(out_dir),
                "train": "train/images",
                "val": "val/images",
                "names": classes,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return {
        "dataset": str(out_dir),
        "images": len(images),
        "train": len(splits["train"]),
        "val": len(splits["val"]),
        "labels_converted": converted,
        "classes": classes,
        "data_yaml": str(data_yaml),
    }


# ── train ──────────────────────────────────────────────────────────────────

def finetune_dog_yolo(
    dataset_dir: Path = DEFAULT_DATASET,
    epochs: int = 30,
    imgsz: int = 640,
    out_onnx: Path | None = None,
    weights: str = "yolov8n.pt",
) -> dict:
    """Fine-tune YOLOv8n on the user's dog dataset and export a dog ONNX."""
    data_yaml = dataset_dir / "data.yaml"
    if not data_yaml.exists():
        raise RuntimeError(f"run prep-dog-yolo first (missing {data_yaml})")
    from ultralytics import YOLO

    model = YOLO(weights)
    results = model.train(data=str(data_yaml), epochs=epochs, imgsz=imgsz, verbose=False)
    best = Path(results.save_dir) / "weights" / "best.pt"
    if not best.exists():
        raise RuntimeError(f"training finished but best.pt missing: {best}")

    out = out_onnx or (Path("artifacts") / "models" / "vision" / "dog_yolo.pt")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, out)

    # Export the fine-tuned detector to ONNX for the runtime + mobile bundles.
    trained = YOLO(str(out))
    trained.export(format="onnx", imgsz=imgsz, simplify=True, opset=17)
    exported = out.with_suffix(".onnx")
    if exported.exists():
        shutil.move(str(exported), str(exported))
    return {
        "weights": str(out),
        "onnx": str(out.with_suffix(".onnx")) if out.with_suffix(".onnx").exists() else None,
        "epochs": epochs,
        "dataset": str(dataset_dir),
    }
