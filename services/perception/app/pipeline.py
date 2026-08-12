"""Compose perception modules into a feature dict from a BGR frame."""
from __future__ import annotations

import numpy as np

from .dog_detect import MotionDogDetector, detect_dog

try:
    from .yolo_detect import YoloDogDetector, default_weights
except ImportError:
    YoloDogDetector = None  # type: ignore[misc, assignment]
    default_weights = None  # type: ignore[assignment]
try:
    from .breed import BreedClassifier
except ImportError:
    BreedClassifier = None  # type: ignore[misc, assignment]
from .face import estimate_face_signals
from .gaze import load_zones, score_gaze
from .pose import estimate_pose
from .scene import classify_scene
from .temporal import TemporalTracker
from .tracker import MultiDogTracker
from .tau import score_approach
from .deepfusion import advanced_defaults, compute_advanced_features, reset_trackers

_TRACKER = TemporalTracker()
_MULTI = MultiDogTracker()
_DETECTOR = MotionDogDetector()
_YOLO: object | None = None
_BREED: object | None = None
_ZONES = load_zones()


def _get_yolo() -> object | None:
    global _YOLO
    if YoloDogDetector is None or default_weights is None:
        return None
    if _YOLO is None and default_weights().exists():
        _YOLO = YoloDogDetector()
    return _YOLO


def _get_breed() -> object | None:
    global _BREED
    if BreedClassifier is None:
        return None
    if _BREED is None:
        _BREED = BreedClassifier()
    return _BREED if _BREED.available else None  # type: ignore[union-attr]


def _crop_bbox(frame_bgr: np.ndarray, bbox) -> np.ndarray | None:
    h, w = frame_bgr.shape[:2]
    x1 = max(0, int(bbox.x * w))
    y1 = max(0, int(bbox.y * h))
    x2 = min(w, int((bbox.x + bbox.w) * w))
    y2 = min(h, int((bbox.y + bbox.h) * h))
    if x2 - x1 < 8 or y2 - y1 < 8:
        return None
    return frame_bgr[y1:y2, x1:x2]


def _annotate_breed(frame_bgr: np.ndarray, bbox, base: dict) -> dict:
    clf = _get_breed()
    if clf is None:
        base["breed"] = None
        base["breed_conf"] = 0.0
        base["breed_top3"] = []
        return base
    crop = _crop_bbox(frame_bgr, bbox)
    if crop is None:
        base["breed"] = None
        base["breed_conf"] = 0.0
        base["breed_top3"] = []
        return base
    top = clf.classify_crop(crop, top_k=3)  # type: ignore[union-attr]
    base["breed_top3"] = [{"breed": name, "conf": round(conf, 3)} for name, conf in top]
    if top:
        base["breed"] = top[0][0]
        base["breed_conf"] = round(top[0][1], 3)
    else:
        base["breed"] = None
        base["breed_conf"] = 0.0
    return base


def _run_primary(primary, frame_bgr, motion: float, vx: float, vy: float, confirmed: bool = True) -> dict:
    bbox = primary.bbox
    pose = estimate_pose(bbox)
    gaze = score_gaze(bbox, _ZONES)
    approach = score_approach(bbox, vx, vy, _ZONES)
    scene = classify_scene(frame_bgr, motion_level=motion)
    face = estimate_face_signals(pose, arousal_proxy=scene.motion_level)

    advanced = compute_advanced_features(bbox, pose, face, frame_bgr, vx, vy)

    edge_left = bbox.x
    edge_right = 1.0 - (bbox.x + bbox.w)
    edge_top = bbox.y
    edge_bottom = 1.0 - (bbox.y + bbox.h)

    base = {
        # Motion-only detections have no object-class awareness (any moving
        # blob qualifies), so they're reported as unconfirmed rather than a
        # positive dog identification.
        "dog_present": 1.0 if confirmed else min(float(bbox.confidence), 0.4),
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
        "pose_head_y": pose.head_y,
        "pose_head_gaze_x": pose.head_gaze_x,
        "pose_body_stretch": pose.body_stretch,
        "pose_play_bow": pose.play_bow,
        "n_dogs": 1,
        "track_stability": float(getattr(primary, "stability", 1.0)),
        "scene": scene.tags,
    }
    base.update(advanced)

    if confirmed:
        _annotate_breed(frame_bgr, bbox, base)
    else:
        # Don't guess a breed on an unconfirmed (motion-only) crop — the
        # breed classifier has no "not a dog" class and will always return
        # a confident-looking label for whatever object triggered motion.
        base["breed"] = None
        base["breed_conf"] = 0.0
        base["breed_top3"] = []

    for name in ("door", "toy", "bowl"):
        base[f"tau_{name}"] = approach.tau.get(name, 0.0)
        base[f"closing_{name}"] = approach.closing.get(name, 0.0)
        base[f"heading_{name}"] = approach.heading.get(name, 0.0)
    return base


def run_pipeline_frame(frame_bgr: np.ndarray) -> dict:
    global _TRACKER, _MULTI, _DETECTOR, _ZONES
    gray_mean = float(np.mean(frame_bgr) / 255.0)
    yolo = _get_yolo()
    detections: list = []
    if yolo is not None:
        detections = yolo.detect_all(frame_bgr)  # type: ignore[union-attr]
    confirmed = bool(detections)
    if not detections:
        single = detect_dog(frame_bgr, _DETECTOR)
        if single is not None:
            detections = [single]

    if not detections:
        motion, vx, vy = _TRACKER.update(None, gray_mean)
        _MULTI.update([], frame_bgr)
        scene = classify_scene(frame_bgr, motion_level=motion)
        reset_trackers()
        base: dict = {
            "dog_present": 0.0,
            "breed": None,
            "breed_conf": 0.0,
            "breed_top3": [],
            "n_dogs": 0,
            "track_stability": 0.0,
            "pose_head_y": 0.5,
            "pose_head_gaze_x": 0.5,
            "pose_body_stretch": 0.0,
            "pose_play_bow": 0.0,
            "motion": motion,
            "velocity_x": vx,
            "velocity_y": vy,
            "brightness": scene.brightness,
            "contrast": scene.contrast,
            "scene": scene.tags,
            "arousal_proxy": motion,
        }
        base.update(advanced_defaults())
        return base

    tracks = _MULTI.update(detections, frame_bgr)
    primary = _MULTI.primary()
    motion, vx, vy = _TRACKER.update(primary.bbox if primary else detections[0], gray_mean)

    base = _run_primary(primary, frame_bgr, motion, vx, vy, confirmed=confirmed)
    base["n_dogs"] = min(len([t for t in tracks if t.alive]), 4)
    return base


def run_pipeline(frame_bytes: bytes, width: int = 64, height: int = 64) -> dict:
    """Backward-compatible bytes API for smoke tests."""
    if len(frame_bytes) < width * height * 3:
        arr = np.full((height, width, 3), 128, dtype=np.uint8)
    else:
        arr = np.frombuffer(frame_bytes[: width * height * 3], dtype=np.uint8).reshape(
            (height, width, 3)
        )
    return run_pipeline_frame(arr)
