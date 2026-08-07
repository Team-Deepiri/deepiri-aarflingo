"""Multi-dog tracker: IoU association + HSV appearance Re-ID.

Improves on TemporalTracker (single bbox velocity) by maintaining stable
per-dog identities across frames and occlusions using a cheap color
histogram embedding. No external tracking dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .dog_detect import BBox

MAX_MISSES = 12
APPEARANCE_BINS = 32
APPEARANCE_WEIGHT = 0.35
IOU_THRESHOLD = 0.3
MAX_NEW_TRACKS = 4


@dataclass
class Track:
    track_id: int
    bbox: BBox
    confidence: float
    hits: int = 1
    misses: int = 0
    age: int = 1
    appearance: np.ndarray | None = None
    last_bbox: BBox | None = None
    velocity_x: float = 0.0
    velocity_y: float = 0.0

    @property
    def alive(self) -> bool:
        return self.misses < MAX_MISSES

    @property
    def stability(self) -> float:
        return min(1.0, self.hits / max(self.age, 1))


def iou(a: BBox, b: BBox) -> float:
    ax1, ay1 = a.x, a.y
    ax2, ay2 = a.x + a.w, a.y + a.h
    bx1, by1 = b.x, b.y
    bx2, by2 = b.x + b.w, b.y + b.h
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(1e-9, a.w * a.h)
    area_b = max(1e-9, b.w * b.h)
    return inter / (area_a + area_b - inter)


def appearance_hist(frame_bgr: np.ndarray | None, bbox: BBox) -> np.ndarray | None:
    """Normalized HSV color histogram over the bbox crop (Re-ID embedding)."""
    if frame_bgr is None or frame_bgr.size == 0:
        return None
    import cv2

    h, w = frame_bgr.shape[:2]
    x1 = max(0, int(bbox.x * w))
    y1 = max(0, int(bbox.y * h))
    x2 = min(w, int((bbox.x + bbox.w) * w))
    y2 = min(h, int((bbox.y + bbox.h) * h))
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None
    crop = frame_bgr[y1:y2, x1:x2]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [APPEARANCE_BINS, APPEARANCE_BINS], [0, 180, 0, 256])
    cv2.normalize(hist, hist)
    return hist.flatten().astype(np.float32)


def appearance_similarity(a: np.ndarray | None, b: np.ndarray | None) -> float:
    if a is None or b is None:
        return 0.0
    return float(cv2_compare_hist(a, b))


def cv2_compare_hist(a: np.ndarray, b: np.ndarray) -> float:
    import cv2

    return cv2.compareHist(a, b, cv2.HISTCMP_BHATTACHARYYA)


class MultiDogTracker:
    """IoU + appearance association with greedy matching.

    Each detection is matched against live tracks by a combined score of
    IoU and HSV histogram similarity; unmatched detections spawn new tracks.
    """

    def __init__(
        self,
        iou_threshold: float = IOU_THRESHOLD,
        appearance_weight: float = APPEARANCE_WEIGHT,
        max_misses: int = MAX_MISSES,
    ) -> None:
        self._tracks: list[Track] = []
        self._next_id = 0
        self._iou_threshold = iou_threshold
        self._appearance_weight = appearance_weight
        self._max_misses = max_misses

    @property
    def tracks(self) -> list[Track]:
        return list(self._tracks)

    def update(self, detections: list[BBox], frame_bgr: np.ndarray | None = None) -> list[Track]:
        for det in detections:
            self._associate(det, frame_bgr)
        for t in self._tracks:
            t.age += 1
        self._prune()
        return self.tracks

    def _associate(self, det: BBox, frame_bgr: np.ndarray | None) -> None:
        best: Track | None = None
        best_score = self._iou_threshold
        hist = appearance_hist(frame_bgr, det)
        for t in self._tracks:
            if not t.alive:
                continue
            iou_score = iou(t.bbox, det)
            app_score = appearance_similarity(t.appearance, hist)
            score = (1.0 - self._appearance_weight) * iou_score + self._appearance_weight * app_score
            if score > best_score:
                best = t
                best_score = score
        if best is not None:
            best.last_bbox = best.bbox
            best.bbox = det
            best.confidence = det.confidence
            best.hits += 1
            best.misses = 0
            best.age = 1
            if hist is not None:
                if best.appearance is None:
                    best.appearance = hist
                else:
                    best.appearance = 0.8 * best.appearance + 0.2 * hist
            if best.last_bbox is not None:
                best.velocity_x = det.cx - best.last_bbox.cx
                best.velocity_y = det.cy - best.last_bbox.cy
            return
        if len([t for t in self._tracks if t.alive]) < MAX_NEW_TRACKS:
            self._spawn(det, hist)

    def _spawn(self, det: BBox, hist: np.ndarray | None) -> None:
        self._tracks.append(
            Track(track_id=self._next_id, bbox=det, confidence=det.confidence, appearance=hist)
        )
        self._next_id += 1

    def _prune(self) -> None:
        for t in self._tracks:
            if not t.alive:
                t.misses += 1
        self._tracks = [t for t in self._tracks if t.alive]

    def primary(self) -> Track | None:
        """Highest-stability live track (ties broken by confidence)."""
        live = [t for t in self._tracks if t.alive]
        if not live:
            return None
        return max(live, key=lambda t: (t.stability, t.confidence))
