"""Export TriadNet to ONNX for studio + edge."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import torch
import torch.nn as nn


def _load_forecast(module: str):
    root = Path(__file__).resolve().parents[3]
    path = root / "services" / "forecast" / "app" / f"{module}.py"
    spec = importlib.util.spec_from_file_location(f"forecast_{module}", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(root / "services" / "forecast"))
    sys.path.insert(0, str(root))
    spec.loader.exec_module(mod)
    return mod


_labels = _load_forecast("labels")
_triad = _load_forecast("triad_model")
TriadNet = _triad.TriadNet
flatten_sequence = _triad.flatten_sequence


class _OnnxWrapper(nn.Module):
    def __init__(self, model: TriadNet) -> None:
        super().__init__()
        self.model = model

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        li, le, lb = self.model(x)
        return torch.softmax(li, dim=-1), torch.softmax(le, dim=-1), torch.softmax(lb, dim=-1)


def export_onnx(out_dir: Path, model_name: str = "triad") -> Path:
    intents = _labels.intent_labels()
    emotions = _labels.emotion_labels()
    behaviors = _labels.behavior_labels()
    model = TriadNet(intents, emotions, behaviors)
    ckpt = Path(__file__).resolve().parents[3] / "artifacts" / "models" / "default" / "triad.pt"
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
    return out_path
