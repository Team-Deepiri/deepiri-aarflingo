"""Training data from synthetic heuristics + feedback export."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.feature_spec import BASE_FEATURE_NAMES, SEQUENCE_LEN, vectorize  # noqa: E402
from core.modality_spec import MODALITY_NAMES, modality_defaults  # noqa: E402


@dataclass
class TriadSample:
    sequence: list[list[float]]
    intent_id: str
    emotion_id: str
    behavior_id: str


def _modality_for_intent(intent: str) -> dict[str, float]:
    m = modality_defaults()
    if intent == "outside":
        m.update({
            "vision_yolo_dog_conf": 0.85, "ecg_stress": 0.7, "audio_arousal": 0.6, "imu_activity": 0.35,
            # §4 prosody: high f0 + HNR -> tense vocalization
            "audio_f0": 0.55, "audio_hnr": 0.3, "audio_formant_f1": 0.5, "audio_burstiness": 0.45,
            # §8 ECG HRV: stress is linked to low RMSSD / distorted LF:HF ratio
            "ecg_lfhf": 0.75, "ecg_rmssd_norm": 0.35,
            # §7 synchrony: body+voice rise together -> coupling near 1
            "sync_plv": 0.85, "sync_corr": 0.8, "sync_latent_arousal": 0.7, "sync_latent_valence": -0.3,
        })
    elif intent == "play":
        m.update({
            "vision_yolo_dog_conf": 0.92, "audio_arousal": 0.85, "audio_valence": 0.8, "audio_bark_prob": 0.75, "imu_activity": 0.8,
            "audio_f0": 0.6, "audio_hnr": 0.55, "audio_formant_f1": 0.55, "audio_burstiness": 0.8,
            "ecg_lfhf": 0.4, "ecg_rmssd_norm": 0.7,
            "sync_plv": 0.75, "sync_corr": 0.7, "sync_latent_arousal": 0.85, "sync_latent_valence": 0.7,
        })
    elif intent == "food":
        m.update({
            "vision_yolo_dog_conf": 0.88, "audio_arousal": 0.35, "imu_activity": 0.25, "imu_posture_static": 0.7,
            "audio_f0": 0.4, "audio_hnr": 0.6, "audio_formant_f1": 0.5, "audio_burstiness": 0.15,
            "ecg_lfhf": 0.55, "ecg_rmssd_norm": 0.6,
            "sync_plv": 0.6, "sync_corr": 0.5, "sync_latent_arousal": 0.3, "sync_latent_valence": 0.15,
        })
    elif intent == "avoid":
        m.update({
            "vision_yolo_dog_conf": 0.8, "ecg_stress": 0.85, "audio_valence": 0.1, "audio_bark_prob": 0.4, "imu_posture_static": 0.85,
            "audio_f0": 0.7, "audio_hnr": 0.2, "audio_formant_f1": 0.65, "audio_burstiness": 0.35,
            "ecg_lfhf": 0.8, "ecg_rmssd_norm": 0.25,
            "sync_plv": 0.2, "sync_corr": 0.1, "sync_latent_arousal": 0.75, "sync_latent_valence": -0.7,
        })
    else:
        m.update({
            "vision_yolo_dog_conf": 0.75, "ecg_hr_norm": 0.35, "ecg_stress": 0.2, "imu_posture_static": 0.9, "imu_activity": 0.1,
            "audio_f0": 0.35, "audio_hnr": 0.55, "audio_formant_f1": 0.45, "audio_burstiness": 0.1,
            "ecg_lfhf": 0.5, "ecg_rmssd_norm": 0.55,
            "sync_plv": 0.55, "sync_corr": 0.55, "sync_latent_arousal": 0.2, "sync_latent_valence": 0.2,
        })
    return m


def _synth_row(intent: str) -> tuple[dict, str, str, str]:
    r = random.random
    base = {name: r() * 0.2 for name in BASE_FEATURE_NAMES}
    base["dog_present"] = 1.0
    base["n_dogs"] = 1
    base["track_stability"] = 0.7 + r() * 0.3
    base.update(_modality_for_intent(intent))
    tail = {
        # §1 tail dynamics; play -> fast rhythmic wag, outside -> tense low sweep
        "tail_wag_rate": 0.7 + r() * 0.2 if intent == "play" else 0.1 + r() * 0.3,
        "tail_amplitude": 0.5 + r() * 0.3 if intent == "play" else 0.2 + r() * 0.2,
        "tail_velocity": 0.6 + r() * 0.2 if intent == "play" else 0.15 + r() * 0.2,
        "tail_rhythmicity": 0.7 + r() * 0.2 if intent == "play" else 0.3 + r() * 0.2,
        "tail_height": 0.5 + r() * 0.3 if intent == "play" else 0.25 + r() * 0.2,
        "tail_asymmetry": 0.2 + r() * 0.2 if intent == "play" else 0.4 + r() * 0.3,
        "tail_lyapunov": 0.1 + r() * 0.2,
    }
    if intent == "avoid":
        tail.update({"tail_wag_rate": 0.05, "tail_amplitude": 0.1, "tail_height": 0.15})
    elif intent in ("rest", "food"):
        tail.update({"tail_wag_rate": 0.1 + r() * 0.1, "tail_height": 0.3 + r() * 0.1})
    base.update(tail)
    face = {
        # §2/§5 facial + head dynamics; avoid -> high mouth tension (lip lick)
        "facs_au_intensity": 0.3 + r() * 0.2 if intent == "play" else 0.15 + r() * 0.15,
        "ear_angle": 0.5 + r() * 0.2 if intent == "play" else 0.4 + r() * 0.2,
        "sclera_exposure": 0.5 + r() * 0.25 if intent == "play" else 0.3 + r() * 0.2,
        "blink_rate": 0.4 + r() * 0.2 if intent == "avoid" else 0.2 + r() * 0.15,
        "mouth_tension": 0.75 + r() * 0.2 if intent == "avoid" else 0.1 + r() * 0.15,
        "head_pitch": 0.6 + r() * 0.2 if intent == "play" else 0.3 + r() * 0.15,
        "head_yaw": 0.5 + r() * 0.2,
        "head_roll_var": 0.2 if intent in ("rest", "food") else 0.4 + r() * 0.3,
    }
    base.update(face)
    body = {
        # §6 gait / posture dynamics
        "com_shift_x": 0.5 + r() * 0.25 if intent == "play" else 0.3 + r() * 0.2,
        "approach_avoid": 0.75 + r() * 0.2 if intent == "outside" else 0.25 + r() * 0.2,
        "gait_phase_trot": 0.55 + r() * 0.3 if intent == "play" else 0.1 + r() * 0.15,
        "gait_phase_pace": 0.5 + r() * 0.3 if intent == "outside" else 0.15 + r() * 0.15,
        "freeze_duration": 0.8 + r() * 0.15 if intent == "avoid" else 0.05 + r() * 0.1,
    }
    base.update(body)
    if intent == "outside":
        base.update({"gaze_door": 0.7 + r() * 0.2, "motion": 0.08 + r() * 0.1})
        base.update({"pose_head_y": 0.3 + r() * 0.2, "pose_head_gaze_x": 0.7 + r() * 0.2, "pose_body_stretch": 0.4 + r() * 0.3})
        base.update({"tau_door": 0.5 + r() * 0.4, "closing_door": 0.5 + r() * 0.4, "heading_door": 0.6 + r() * 0.3})
        return base, "outside", "anxious", "freeze"
    if intent == "play":
        base.update({"gaze_toy": 0.75 + r() * 0.2, "motion": 0.15 + r() * 0.15})
        base.update({"pose_play_bow": 0.7 + r() * 0.3, "pose_head_y": 0.6 + r() * 0.2, "pose_body_stretch": 0.5 + r() * 0.3})
        base.update({"tau_toy": 0.5 + r() * 0.4, "closing_toy": 0.5 + r() * 0.4, "heading_toy": 0.6 + r() * 0.3})
        return base, "play", "excited", "play_bow"
    if intent == "food":
        base.update({"gaze_bowl": 0.7 + r() * 0.2, "motion": 0.04 + r() * 0.05})
        base.update({"pose_head_y": 0.4 + r() * 0.2, "pose_head_gaze_x": 0.7 + r() * 0.2})
        base.update({"tau_bowl": 0.5 + r() * 0.4, "closing_bowl": 0.5 + r() * 0.4, "heading_bowl": 0.6 + r() * 0.3})
        return base, "food", "content", "sniff_ground"
    if intent == "avoid":
        base.update({"gaze_aversion": 0.8, "motion": 0.05})
        base.update({"pose_head_y": 0.25 + r() * 0.15, "pose_head_gaze_x": 0.1 + r() * 0.2, "track_stability": 0.5 + r() * 0.3})
        base.update({"tau_door": r() * 0.15, "tau_toy": r() * 0.15, "tau_bowl": r() * 0.15})
        base.update({"heading_door": -0.3 - r() * 0.4, "heading_toy": -0.3 - r() * 0.4, "heading_bowl": -0.3 - r() * 0.4})
        return base, "avoid", "fearful", "tail_tucked"
    base.update({"motion": 0.02})
    base.update({"pose_head_y": 0.3 + r() * 0.2, "pose_body_stretch": 0.3 + r() * 0.2, "pose_play_bow": 0.0})
    return base, "rest", "calm", "yawning"


def load_synthetic_dataset(n_per_class: int = 40) -> list[TriadSample]:
    random.seed(42)
    samples: list[TriadSample] = []
    for intent in ("outside", "play", "food", "avoid", "rest"):
        for _ in range(n_per_class):
            seq: list[list[float]] = []
            for _ in range(SEQUENCE_LEN):
                row, iid, eid, bid = _synth_row(intent)
                seq.append(vectorize(row))
            samples.append(TriadSample(seq, iid, eid, bid))
    return samples


def load_feedback_dataset(feedback_db: Path) -> list[TriadSample]:
    if not feedback_db.exists():
        return []
    rows = json.loads(feedback_db.read_text(encoding="utf-8"))
    out: list[TriadSample] = []
    for row in rows.get("samples", []):
        seq = row.get("sequence")
        if not seq:
            continue
        out.append(
            TriadSample(
                sequence=seq,
                intent_id=row["intent_id"],
                emotion_id=row["emotion_id"],
                behavior_id=row["behavior_id"],
            )
        )
    return out
