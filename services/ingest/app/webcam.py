"""OpenCV webcam capture for ingest service."""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class CaptureSession:
    camera_index: int
    width: int = 640
    height: int = 480
    fps: float = 30.0

    def frames(self, max_frames: int | None = None):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera {self.camera_index}")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        n = 0
        try:
            while max_frames is None or n < max_frames:
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.02)
                    continue
                yield frame
                n += 1
        finally:
            cap.release()

    def save_clip(self, out_dir: Path, seconds: float = 5.0) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"clip_{int(time.time())}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, self.fps, (self.width, self.height))
        limit = int(seconds * self.fps)
        for i, frame in enumerate(self.frames(max_frames=limit)):
            writer.write(frame)
            if i + 1 >= limit:
                break
        writer.release()
        return path


def probe_camera(index: int = 0) -> dict:
    cap = cv2.VideoCapture(index)
    ok = cap.isOpened()
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if ok else 0
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if ok else 0
    cap.release()
    return {"index": index, "open": ok, "width": w, "height": h}
