"""PyTorch tensor helpers for IEB triad training and inference."""
from __future__ import annotations

from typing import Sequence

import torch
import torch.nn.functional as F

from core.triad_math import flatten_sequence_rows, triad_confidence_scalar


def softmax_probs(logits: torch.Tensor) -> torch.Tensor:
    return F.softmax(logits, dim=-1)


def cross_entropy_from_logits(logits: torch.Tensor, target: int) -> torch.Tensor:
    return F.cross_entropy(logits, torch.tensor([target], device=logits.device))


def flatten_sequence_tensor(frames: Sequence[Sequence[float]]) -> torch.Tensor:
    return torch.tensor([flatten_sequence_rows(frames)], dtype=torch.float32)


def flatten_sequence_batch(sequences: Sequence[Sequence[Sequence[float]]]) -> torch.Tensor:
    return torch.stack([flatten_sequence_tensor(seq)[0] for seq in sequences])


def triad_confidence(
    intent_probs: torch.Tensor,
    emotion_probs: torch.Tensor,
    behavior_probs: torch.Tensor,
    intent_idx: int,
    emotion_idx: int,
    behavior_idx: int,
) -> float:
    return triad_confidence_scalar(
        float(intent_probs[intent_idx]),
        float(emotion_probs[emotion_idx]),
        float(behavior_probs[behavior_idx]),
    )


def margin_from_probs(probs: torch.Tensor) -> float:
    """Top-1 minus top-2 probability of a distribution."""
    top2 = torch.topk(probs, k=min(2, probs.numel())).values
    if top2.numel() < 2:
        return float(top2[0]) if top2.numel() == 1 else 0.0
    return float(top2[0] - top2[1])


def triad_margin(
    intent_probs: torch.Tensor,
    emotion_probs: torch.Tensor,
    behavior_probs: torch.Tensor,
) -> float:
    return (
        margin_from_probs(intent_probs)
        + margin_from_probs(emotion_probs)
        + margin_from_probs(behavior_probs)
    ) / 3.0
