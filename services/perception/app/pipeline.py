"""Compose perception modules into a feature dict from a BGR frame."""
from __future__ import annotations

import numpy as np

from .dog_detect import MotionDogDetector, detect_dog

try:
    from .yolo_detect import YoloDogDetector, default_weights
except ImportError:
    YoloDogDetector = None  # type: ignore[misc, assignment]
    default_weights = None  # type: ignore[assignment]
from .face import estimate_face_signals
from .gaze import load_zones, score_gaze
from .pose import estimate_pose
from .scene import classify_scene
from .temporal import TemporalTracker

_TRACKER = TemporalTracker()
_DETECTOR = MotionDogDetector()
_YOLO: object | None = None
_ZONES = load_zones()


def _get_yolo() -> object | None:
    global _YOLO
    if YoloDogDetector is None or default_weights is None:
        return None
    if _YOLO is None and default_weights().exists():
        _YOLO = YoloDogDetector()
    return _YOLO


def run_pipeline_frame(frame_bgr: np.ndarray) -> dict:
    global _TRACKER, _DETECTOR, _ZONES
    gray_mean = float(np.mean(frame_bgr) / 255.0)
    yolo = _get_yolo()
    bbox = None
    if yolo is not None:
        bbox = yolo.detect(frame_bgr)  # type: ignore[union-attr]
    if bbox is None:
        bbox = detect_dog(frame_bgr, _DETECTOR)

    if bbox is None:
        motion, vx, vy = _TRACKER.update(None, gray_mean)
        scene = classify_scene(frame_bgr, motion_level=motion)
        return {
            "dog_present": 0.0,
            "motion": motion,
            "velocity_x": vx,
            "velocity_y": vy,
            "brightness": scene.brightness,
            "contrast": scene.contrast,
            "scene": scene.tags,
            "arousal_proxy": motion,
        }

    motion, vx, vy = _TRACKER.update(bbox, gray_mean)
    pose = estimate_pose(bbox)
    gaze = score_gaze(bbox, _ZONES)
    scene = classify_scene(frame_bgr, motion_level=motion)
    face = estimate_face_signals(pose, arousal_proxy=scene.motion_level)

    edge_left = bbox.x
    edge_right = 1.0 - (bbox.x + bbox.w)
    edge_top = bbox.y
    edge_bottom = 1.0 - (bbox.y + bbox.h)

    return {
        "dog_present": 1.0,
        "bbox": bbox.__dict__,
        "bbox_cx": bbox.cx,
        "bbox_cy": bbox.cy,
        "bbox_w": bbox.w,
        "bbox_h": bbox.h,
        "vision_yolo_dog_conf": float(bbox.confidence),
        "motion": motion,
        "velocity_x": vx,
        "velocity_y": vy,
        "gaze_door": gaze.door,
        "gaze_toy": gaze.toy,
        "gaze_bowl": gaze.bowl,
        "gaze_center": gaze.center,
        "gaze_aversion": gaze.aversion,
        "edge_left": edge_left,
        "edge_right": edge_right,
        "edge_top": edge_top,
        "edge_bottom": edge_bottom,
        "brightness": scene.brightness,
        "contrast": scene.contrast,
        "aspect_ratio": pose.aspect_ratio,
        "arousal_proxy": max(scene.motion_level, face.lip_lick_likelihood),
        "whale_eye_likelihood": face.whale_eye_likelihood,
        "lip_lick_likelihood": face.lip_lick_likelihood,
        "scene": scene.tags,
    }


def run_pipeline(frame_bytes: bytes, width: int = 64, height: int = 64) -> dict:
    """Backward-compatible bytes API for smoke tests."""
    if len(frame_bytes) < width * height * 3:
        arr = np.full((height, width, 3), 128, dtype=np.uint8)
    else:
        arr = np.frombuffer(frame_bytes[: width * height * 3], dtype=np.uint8).reshape(
            (height, width, 3)
        )
    return run_pipeline_frame(arr)
