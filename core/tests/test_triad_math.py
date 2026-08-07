"""Unit tests mirroring notebooks/01_triad_math_simulation.ipynb (PyTorch)."""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from core.feature_spec import FEATURE_DIM, SEQUENCE_LEN
from core.triad_math import (
    margin_confidence,
    numpy_cross_entropy,
    numpy_softmax,
    triad_margin_scalar,
)
from core.triad_torch import (
    cross_entropy_from_logits,
    flatten_sequence_tensor,
    softmax_probs,
    triad_confidence,
    triad_margin,
)


def test_softmax_matches_numpy() -> None:
    logits = torch.tensor([[1.0, 2.0, 0.5]])
    pt = softmax_probs(logits)[0].tolist()
    np = numpy_softmax([1.0, 2.0, 0.5])
    for a, b in zip(pt, np):
        assert abs(a - b) < 1e-5


def test_cross_entropy_matches_numpy() -> None:
    logits = torch.tensor([[2.0, 0.5, -1.0]])
    probs = numpy_softmax([2.0, 0.5, -1.0])
    ce_np = numpy_cross_entropy(probs, 0)
    ce_pt = float(cross_entropy_from_logits(logits, 0))
    assert abs(ce_np - ce_pt) < 1e-4


def test_triad_confidence_mean() -> None:
    pi = torch.tensor([0.8, 0.1, 0.1])
    pe = torch.tensor([0.2, 0.7, 0.1])
    pb = torch.tensor([0.3, 0.3, 0.4])
    conf = triad_confidence(pi, pe, pb, 0, 1, 2)
    assert abs(conf - (0.8 + 0.7 + 0.4) / 3) < 1e-6


def test_flatten_sequence_tensor_shape() -> None:
    t = flatten_sequence_tensor([[float(i)] * FEATURE_DIM for i in range(5)])
    assert t.shape == (1, FEATURE_DIM * SEQUENCE_LEN)


def test_margin_confidence_is_top1_minus_top2() -> None:
    assert abs(margin_confidence([0.8, 0.1, 0.1]) - 0.7) < 1e-6
    assert abs(margin_confidence([0.45, 0.4, 0.15]) - 0.05) < 1e-6


def test_tied_distribution_has_small_margin() -> None:
    assert margin_confidence([0.5, 0.5, 0.0]) < 1e-6


def test_triad_margin_torch_matches_scalar() -> None:
    pi = torch.tensor([0.7, 0.2, 0.1])
    pe = torch.tensor([0.4, 0.4, 0.2])
    pb = torch.tensor([0.9, 0.05, 0.05])
    scalar = triad_margin_scalar(
        pi.tolist(), pe.tolist(), pb.tolist()
    )
    torch_margin = triad_margin(pi, pe, pb)
    assert abs(scalar - torch_margin) < 1e-6
    assert torch_margin < (0.9 + 0.7) / 3  # tied emotion head drags it down
