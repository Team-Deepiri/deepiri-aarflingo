"""YOLOv8 dog detector — COCO pretrained class 16 (dog)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .dog_detect import BBox, MotionDogDetector, detect_dog

# COCO class index for dog in YOLOv8.
YOLO_DOG_CLASS_ID = 16


def default_weights(root: Path | None = None) -> Path:
    base = root or Path(__file__).resolve().parents[3]
    return base / "artifacts" / "models" / "vision" / "yolov8n.pt"


def default_onnx(root: Path | None = None) -> Path:
    base = root or Path(__file__).resolve().parents[3]
    return base / "artifacts" / "bundles" / "default" / "studio" / "dog_yolo.onnx"


def prepare_yolo_weights(out_path: Path | None = None) -> Path:
    """Download YOLOv8n weights if missing (ultralytics auto-fetch)."""
    out = out_path or default_weights()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and out.stat().st_size > 1_000_000:
        return out
    from ultralytics import YOLO

    model = YOLO("yolov8n.pt")
    src = Path(getattr(model, "ckpt_path", "yolov8n.pt"))
    if not src.is_file():
        src = Path("yolov8n.pt")
    if src.is_file():
        out.write_bytes(src.read_bytes())
    return out


def export_dog_onnx(weights: Path | None = None, out_path: Path | None = None) -> Path:
    from ultralytics import YOLO

    w = weights or default_weights()
    if not w.exists():
        prepare_yolo_weights(w)
    out = out_path or default_onnx()
    out.parent.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(w))
    model.export(format="onnx", imgsz=640, simplify=True, opset=17)
    exported = w.with_suffix(".onnx")
    if exported.exists():
        out.write_bytes(exported.read_bytes())
    return out


class YoloDogDetector:
    def __init__(self, weights: Path | None = None) -> None:
        from ultralytics import YOLO

        w = weights or default_weights()
        if not w.exists():
            prepare_yolo_weights(w)
        self._model = YOLO(str(w))
        self._motion_fallback = MotionDogDetector()

    def detect(self, frame_bgr: np.ndarray) -> BBox | None:
        h, w = frame_bgr.shape[:2]
        results = self._model.predict(frame_bgr, verbose=False, classes=[YOLO_DOG_CLASS_ID])
        if not results:
            return self._motion_fallback.detect(frame_bgr)
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return self._motion_fallback.detect(frame_bgr)
        best = None
        best_conf = -1.0
        for box in boxes:
            conf = float(box.conf[0])
            if conf > best_conf:
                best_conf = conf
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                best = BBox(
                    x=float(x1 / w),
                    y=float(y1 / h),
                    w=float((x2 - x1) / w),
                    h=float((y2 - y1) / h),
                    confidence=conf,
                )
        return best


def detect_dog_yolo(frame_bgr: np.ndarray, detector: YoloDogDetector | None = None) -> BBox | None:
    if frame_bgr is None or frame_bgr.size == 0:
        return None
    det = detector or YoloDogDetector()
    return det.detect(frame_bgr)
