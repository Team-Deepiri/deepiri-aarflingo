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

def _nameserver_ip(resolv_text: str) -> str | None:
    """First nameserver from resolv.conf text (WSL NAT-mode host IP)."""
    for line in resolv_text.splitlines():
        line = line.strip()
        if line.startswith("nameserver"):
            parts = line.split()
            if len(parts) >= 2:
                return parts[1]
    return None


def bridge_stream_candidates(port: int = 8766) -> list[str]:
    """Webcam-bridge base URLs to try, in order (WSL mirrored loopback → NAT host)."""
    urls = [f"http://127.0.0.1:{port}"]
    try:
        ns = _nameserver_ip(Path("/etc/resolv.conf").read_text(encoding="utf-8"))
    except OSError:
        ns = None
    if ns and f"http://{ns}:{port}" not in urls:
        urls.append(f"http://{ns}:{port}")
    return urls


def _bridge_healthy(base_url: str, timeout: float = 1.5) -> bool:
    import urllib.request

    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=timeout) as r:
            return r.status == 200 and b"ok" in r.read(512).lower()
    except Exception:
        return False


def resolve_capture_source(camera: int = 0, source: str | None = None) -> str | int:
    """Resolve a capture source: explicit `source` wins; else the local camera
    when it opens; else the Windows MJPEG bridge when its health endpoint
    answers (WSL has no /dev/video*). Raises with guidance when nothing works."""
    if source:
        return source
    import cv2

    probe = cv2.VideoCapture(camera)
    ok = probe.isOpened()
    probe.release()
    if ok:
        return camera
    for base in bridge_stream_candidates():
        if _bridge_healthy(base):
            return f"{base}/video/stream"
    raise RuntimeError(
        f"cannot open camera {camera} and no webcam bridge answered "
        f"(tried {', '.join(bridge_stream_candidates())}). Start "
        "scripts/webcam/start_webcam_bridge.ps1 on Windows, or pass --source URL."
    )


def capture_frames(
    out_dir: Path = DEFAULT_CAPTURES,
    camera: int = 0,
    frames: int = 200,
    interval: float = 0.2,
    source: str | None = None,
) -> dict:
    """Grab `frames` webcam frames into `out_dir` (jpg). Motion-skipped.

    `source` may be a camera index string or an MJPEG URL (e.g. the WSL
    bridge at http://<host>:8766/video/stream). When omitted we try the
    local camera first, then auto-detect the bridge.
    """
    import cv2

    out_dir.mkdir(parents=True, exist_ok=True)
    src = resolve_capture_source(camera=camera, source=source)
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        raise RuntimeError(f"cannot open capture source {src!r}")
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
    return {"out": str(out_dir), "captured": written, "camera": camera, "source": str(src)}


# ── model-assisted labeling ───────────────────────────────────────────────

def yolo_rows_from_result(result: object, conf: float = 0.25) -> list[dict]:
    """Convert one ultralytics Results object into JSONL rect rows.

    Rows are center-normalized ({file, cls, x, y, w, h}) matching
    `load_labels`/`prep_dog_yolo` semantics. Pure helper so tests can pass a
    stub result without loading YOLO.
    """
    rows: list[dict] = []
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return rows

    def _plain(v: object) -> list:
        return v.tolist() if hasattr(v, "tolist") else list(v)  # type: ignore[attr-defined]

    names = getattr(result, "names", {}) or {}
    clss = _plain(boxes.cls)
    confs = _plain(boxes.conf)
    xywhn = [list(b) for b in _plain(boxes.xywhn)]
    for cls_id, cf, (x, y, w, h) in zip(clss, confs, xywhn):
        if float(cf) < conf:
            continue
        name = names.get(int(cls_id), str(int(cls_id))) if isinstance(names, dict) else str(int(cls_id))
        rows.append(
            {
                "file": Path(getattr(result, "path", "frame.jpg")).name,
                "cls": name,
                "x": float(x),
                "y": float(y),
                "w": float(w),
                "h": float(h),
            }
        )
    return rows


def auto_label(
    captures_dir: Path = DEFAULT_CAPTURES,
    labels_path: Path = DEFAULT_LABELS,
    conf: float = 0.25,
    weights: str = "yolov8n.pt",
    overwrite: bool = False,
) -> dict:
    """Pre-fill labels.jsonl with COCO-YOLO dog boxes for human review.

    Model-assisted labeling: every detection above `conf` becomes a row.
    Review/correct the JSONL in any text editor, then run prep-dog-yolo.
    Files that already have rows are kept as-is unless `overwrite`.
    """
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - env-dependent
        raise RuntimeError("ultralytics is required for auto-labeling (pip install ultralytics)") from exc

    images = sorted(p for p in captures_dir.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if not images:
        raise RuntimeError(f"no images in {captures_dir}")

    existing: dict[str, list[dict]] = {}
    if labels_path.exists() and not overwrite:
        for r in load_labels(labels_path):
            existing.setdefault(Path(r["file"]).name, []).append(r)

    model = YOLO(weights)
    labeled = files_kept = boxes_total = 0
    rows_out: list[dict] = []
    results = model.predict(source=str(captures_dir), stream=True, conf=conf, verbose=False)
    for result in results:
        name = Path(result.path).name
        prior = existing.get(name)
        if prior:
            files_kept += 1
            rows_out.extend(prior)
            continue
        rows = yolo_rows_from_result(result, conf=conf)
        boxes_total += len(rows)
        labeled += 1
        rows_out.extend(rows)

    labels_path.parent.mkdir(parents=True, exist_ok=True)
    with labels_path.open("w", encoding="utf-8") as fh:
        for r in rows_out:
            fh.write(json.dumps(r) + "\n")
    return {
        "labels": str(labels_path),
        "images": len(images),
        "files_labeled": labeled,
        "files_kept_existing": files_kept,
        "boxes": boxes_total,
        "conf": conf,
    }


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
    rows_by_file: dict[str, list[dict]] = {}
    for r in jsonl_rows:
        rows_by_file.setdefault(Path(r["file"]).name, []).append(r)

    converted = 0
    for split, files in splits.items():
        for src in files:
            dst_img = out_dir / split / "images" / src.name
            shutil.copy2(src, dst_img)
            label_txt = src.with_suffix(".txt")
            out_txt = out_dir / split / "labels" / src.with_suffix(".txt").name
            rows = rows_by_file.get(src.name)
            if label_txt.exists():
                shutil.copy2(label_txt, out_txt)
                continue
            if rows:
                lines = []
                for row in rows:
                    cls = row.get("cls", classes[0])
                    idx = class_index.get(cls, 0)
                    x = float(row.get("x", 0))
                    y = float(row.get("y", 0))
                    w = float(row.get("w", 0.5))
                    h = float(row.get("h", 0.5))
                    # YOLO wants cx, cy, w, h; JSONL x,y is CENTER (normalized 0–1).
                    lines.append(f"{idx} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
                out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
                converted += len(rows)
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
    return {
        "weights": str(out),
        "onnx": str(out.with_suffix(".onnx")) if out.with_suffix(".onnx").exists() else None,
        "epochs": epochs,
        "dataset": str(dataset_dir),
    }
