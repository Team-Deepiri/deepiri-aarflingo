"""Motion- and contour-based dog region (no GPU weights required)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BBox:
    x: float
    y: float
    w: float
    h: float
    confidence: float

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cy(self) -> float:
        return self.y + self.h / 2


class MotionDogDetector:
    def __init__(self) -> None:
        import cv2

        self._bg = cv2.createBackgroundSubtractorMOG2(history=120, varThreshold=32, detectShadows=False)
        self._last: BBox | None = None

    def detect(self, frame_bgr: np.ndarray) -> BBox | None:
        import cv2

        h, w = frame_bgr.shape[:2]
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        fg = self._bg.apply(gray)
        _, thresh = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return self._last

        best = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(best)
        if area < (w * h) * 0.01:
            return self._last

        x, y, bw, bh = cv2.boundingRect(best)
        bbox = BBox(
            x=x / w,
            y=y / h,
            w=bw / w,
            h=bh / h,
            confidence=min(0.99, area / (w * h) * 4),
        )
        self._last = bbox
        return bbox


def detect_dog(frame_bgr: np.ndarray, detector: MotionDogDetector | None = None) -> BBox | None:
    if frame_bgr is None or frame_bgr.size == 0:
        return None
    det = detector or MotionDogDetector()
    return det.detect(frame_bgr)
