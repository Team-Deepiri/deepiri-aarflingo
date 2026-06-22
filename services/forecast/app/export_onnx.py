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
from .triad_model import TriadNet, flatten_sequence


class _OnnxWrapper(nn.Module):
    def __init__(self, model: TriadNet) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        li, le, lb = self.model(x)
        return torch.softmax(li, dim=-1), torch.softmax(le, dim=-1), torch.softmax(lb, dim=-1)


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

    dummy = flatten_sequence([[0.0] * 20] * 15)
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
