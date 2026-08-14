"""Export TriadNet checkpoint to ONNX."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import torch
import torch.nn as nn

import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.feature_spec import FEATURE_DIM, SEQUENCE_LEN  # noqa: E402

from .labels import behavior_labels, emotion_labels, intent_labels
from .temporal_math import TriadNetTemporal
from .triad_model import TriadNet, flatten_sequence


class _OnnxWrapper(nn.Module):
    def __init__(self, model: TriadNet) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        li, le, lb = self.model(x)
        return torch.softmax(li, dim=-1), torch.softmax(le, dim=-1), torch.softmax(lb, dim=-1)


class _OnnxTemporalWrapper(nn.Module):
    """Wraps TriadNetTemporal for ONNX: consumes the unflattened (B, L, F) input.

    Exports the three classification heads (BiLSTM backbone + attention) as a
    drop-in for the studio/mobile on-device runtime, plus continuous arousal
    and valence outputs so the edge runtime can drive the §4/§9 regression.
    """

    def __init__(self, model: TriadNetTemporal) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        li, le, lb, arousal, valence = self.model(x)
        return torch.softmax(li, dim=-1), torch.softmax(le, dim=-1), torch.softmax(lb, dim=-1), arousal, valence


def default_checkpoint() -> Path:
    return Path(__file__).resolve().parents[3] / "artifacts" / "models" / "default" / "triad.pt"


def export_onnx(out_dir: Path, model_name: str = "triad", checkpoint: Path | None = None) -> Path:
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    model = TriadNet(intents, emotions, behaviors)
    ckpt = checkpoint or default_checkpoint()
    if ckpt.exists():
        model.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=True))
    wrapped = _OnnxWrapper(model)
    wrapped.eval()

    dummy = flatten_sequence([[0.0] * FEATURE_DIM] * 15)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{model_name}.onnx"
    torch.onnx.export(
        wrapped,
        dummy,
        str(out_path),
        input_names=["input"],
        output_names=["intent_probs", "emotion_probs", "behavior_probs"],
        dynamic_axes={"input": {0: "batch"}},
        opset_version=17,
    )
    manifest = {
        "model": model_name,
        "format": "onnx",
        "opset": 17,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "checkpoint": str(ckpt.resolve()) if ckpt.exists() else None,
        "intents": intents,
        "emotions": emotions,
        "behaviors": behaviors,
        "input_shape": [1, FEATURE_DIM * SEQUENCE_LEN],
        "outputs": ["intent_probs", "emotion_probs", "behavior_probs"],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out_path


def export_onnx_temporal(out_dir: Path, model_name: str = "triad_temporal", checkpoint: Path | None = None) -> Path:
    """Export the §9 BiLSTM+attention TriadNetTemporal to ONNX.

    If no checkpoint is supplied, falls back to the trained temporal
    checkpoint under artifacts/models/default; trains a fast one if neither
    exists so the bundle always contains a usable temporal variant.
    """
    intents = intent_labels()
    emotions = emotion_labels()
    behaviors = behavior_labels()
    model = TriadNetTemporal(FEATURE_DIM, intents, emotions, behaviors)
    ckpt = checkpoint or (default_checkpoint().parent / "triad_temporal.pt")
    if not ckpt.exists():
        from .train import train_temporal_epochs

        train_temporal_epochs(out_path=ckpt, epochs=5, contrastive_pre=1)
    model.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=True))
    wrapped = _OnnxTemporalWrapper(model)
    wrapped.eval()

    dummy = torch.zeros(1, SEQUENCE_LEN, FEATURE_DIM)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{model_name}.onnx"
    torch.onnx.export(
        wrapped,
        dummy,
        str(out_path),
        input_names=["input"],
        output_names=["intent_probs", "emotion_probs", "behavior_probs", "arousal", "valence"],
        # LSTM unrolling needs static sequence length; trace only batch dim.
        dynamic_axes={"input": {0: "batch"}},
        opset_version=17,
    )
    manifest = {
        "model": model_name,
        "format": "onnx",
        "opset": 17,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "checkpoint": str(ckpt.resolve()) if ckpt.exists() else None,
        "intents": intents,
        "emotions": emotions,
        "behaviors": behaviors,
        "input_shape": [1, SEQUENCE_LEN, FEATURE_DIM],
        "outputs": ["intent_probs", "emotion_probs", "behavior_probs", "arousal", "valence"],
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out_path
