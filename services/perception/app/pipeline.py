"""Compose perception modules into a feature dict."""
from __future__ import annotations

from app.dog_detect import detect_dog
from app.face import estimate_face_signals
from app.gaze import gaze_aversion
from app.pose import estimate_pose
from app.scene import classify_scene


def run_pipeline(frame_bytes: bytes) -> dict:
    scene = classify_scene(frame_bytes)
    bbox = detect_dog(frame_bytes)
    if bbox is None:
        return {"dog_present": False, "scene": scene.tags}
    pose = estimate_pose(bbox)
    ga = gaze_aversion(pose)
    face = estimate_face_signals(pose, arousal_proxy=scene.motion_level)
    return {
        "dog_present": True,
        "bbox": bbox.__dict__,
        "gaze_aversion": ga,
        "whale_eye_likelihood": face.whale_eye_likelihood,
        "lip_lick_likelihood": face.lip_lick_likelihood,
        "scene": scene.tags,
    }
