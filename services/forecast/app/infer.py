"""Load checkpoint and run inference."""
from __future__ import annotations

from pathlib import Path

import torch

from .labels import behavior_labels, emotion_labels, intent_labels
from .temporal_math import TriadNetTemporal
from .triad_model import FEATURE_DIM, SEQUENCE_LEN, TriadNet, TriadPrediction, predict_from_model

_MODEL: TriadNet | None = None
_MODEL_PATH: Path | None = None
_MODEL_BROKEN: bool = False
_TEMPORAL_MODEL: TriadNetTemporal | None = None
_TEMPORAL_PATH: Path | None = None
_TEMPORAL_BROKEN: bool = False


def default_checkpoint() -> Path:
    root = Path(__file__).resolve().parents[3]
    return root / "artifacts" / "models" / "default" / "triad.pt"


def _check_flat_dim(state: dict, path: Path) -> None:
    """Fail fast with a clear message when a checkpoint predates the feature
    spec bump (FEATURE_DIM 43 -> 73) instead of a cryptic load_state_dict
    size-mismatch stack trace."""
    w = state.get("backbone.0.weight")
    expected = FEATURE_DIM * SEQUENCE_LEN
    if w is not None and w.size(1) != expected:
        raise ValueError(
            f"checkpoint {path.name} is incompatible with the current feature spec: "
            f"input dim {w.size(1)} != expected {expected} "
            f"(FEATURE_DIM={FEATURE_DIM}, SEQUENCE_LEN={SEQUENCE_LEN}). "
            f"Retrain against the current spec or re-export the ONNX bundle."
        )


def get_model() -> TriadNet | None:
    global _MODEL, _MODEL_PATH, _MODEL_BROKEN
    path = default_checkpoint()
    if _MODEL is not None and _MODEL_PATH == path:
        return _MODEL
    # An incompatible checkpoint (e.g. 43-dim) can never load under the current
    # spec — cache the failure so we don't re-attempt on every frame.
    if not path.exists() or _MODEL_BROKEN:
        return None
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    model = TriadNet(intents, emotions, behaviors)
    try:
        state = torch.load(path, map_location="cpu", weights_only=True)
        _check_flat_dim(state, path)
        model.load_state_dict(state)
    except Exception as exc:
        _MODEL_BROKEN = True
        print(f"[forecast] skipping incompatible checkpoint {path}: {exc}")
        return None
    model.eval()
    _MODEL = model
    _MODEL_PATH = path
    return model


def load_checkpoint(path: Path) -> TriadNet:
    global _MODEL, _MODEL_PATH, _MODEL_BROKEN
    _MODEL_BROKEN = False
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    model = TriadNet(intents, emotions, behaviors)
    state = torch.load(path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    _MODEL = model
    _MODEL_PATH = path
    return model


def reset_model_cache() -> None:
    """Drop cached model state + broken flags (used after retraining)."""
    global _MODEL, _MODEL_PATH, _MODEL_BROKEN
    global _TEMPORAL_MODEL, _TEMPORAL_PATH, _TEMPORAL_BROKEN
    _MODEL = None
    _MODEL_PATH = None
    _MODEL_BROKEN = False
    _TEMPORAL_MODEL = None
    _TEMPORAL_PATH = None
    _TEMPORAL_BROKEN = False


def get_temporal_model() -> TriadNetTemporal | None:
    """Lazily load the §9 TriadNetTemporal checkpoint if present.

    Falls back to None (flat TriadNet) when no temporal checkpoint exists —
    additive, never a breaking swap of the shipped architecture. An
    incompatible/broken temporal checkpoint is cached as failed so we don't
    retry loading it on every frame.
    """
    global _TEMPORAL_MODEL, _TEMPORAL_PATH, _TEMPORAL_BROKEN
    path = default_checkpoint().parent / "triad_temporal.pt"
    if _TEMPORAL_MODEL is not None and _TEMPORAL_PATH == path:
        return _TEMPORAL_MODEL
    if not path.exists() or _TEMPORAL_BROKEN:
        return None
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    model = TriadNetTemporal(FEATURE_DIM, intents, emotions, behaviors)
    try:
        state = torch.load(path, map_location="cpu", weights_only=True)
        model.load_state_dict(state)
    except Exception as exc:
        _TEMPORAL_BROKEN = True
        print(f"[forecast] skipping incompatible temporal checkpoint {path}: {exc}")
        return None
    model.eval()
    _TEMPORAL_MODEL = model
    _TEMPORAL_PATH = path
    return model


def predict_from_temporal(model: TriadNetTemporal, frames: list[list[float]]) -> TriadPrediction:
    """Inference through the temporal backbone (unflattened sequence input)."""
    import torch

    from core.triad_torch import triad_confidence, triad_margin

    x = torch.tensor([frames], dtype=torch.float32)
    model.eval()
    with torch.no_grad():
        logits_i, logits_e, logits_b, arousal, valence = model(x)
        pi = torch.softmax(logits_i, dim=-1)[0]
        pe = torch.softmax(logits_e, dim=-1)[0]
        pb = torch.softmax(logits_b, dim=-1)[0]
    ii = int(pi.argmax())
    ei = int(pe.argmax())
    bi = int(pb.argmax())
    conf = triad_confidence(pi, pe, pb, ii, ei, bi)
    margin = triad_margin(pi, pe, pb)
    return TriadPrediction(
        intent_id=model.intent_labels[ii],
        emotion_id=model.emotion_labels[ei],
        behavior_id=model.behavior_labels[bi],
        confidence=conf,
        margin=margin,
        intent_probs={model.intent_labels[j]: float(pi[j]) for j in range(len(model.intent_labels))},
    )


def infer_sequence(frames: list[list[float]]) -> TriadPrediction:
    temporal = get_temporal_model()
    if temporal is not None:
        return predict_from_temporal(temporal, frames)
    model = get_model()
    if model is None:
        from .triad_model import heuristic_predict

        names = [
            "dog_present", "bbox_cx", "bbox_cy", "bbox_w", "bbox_h", "motion",
            "velocity_x", "velocity_y", "gaze_door", "gaze_toy", "gaze_bowl",
            "gaze_center", "edge_left", "edge_right", "edge_top", "edge_bottom",
            "brightness", "contrast", "aspect_ratio", "arousal_proxy",
        ]
        last = frames[-1] if frames else [0.0] * len(names)
        feat = {names[i]: last[i] for i in range(min(len(names), len(last)))}
        return heuristic_predict(feat)
    return predict_from_model(model, frames)


def infer_batch(feature_rows: list[dict]) -> list[TriadPrediction]:
    from .features import vectorize
    from .triad_model import predict

    return [predict(row, [vectorize(row)]) for row in feature_rows]
