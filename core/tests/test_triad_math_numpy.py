"""Math-only tests (no torch required)."""
from __future__ import annotations

from core.feature_spec import FEATURE_DIM, SEQUENCE_LEN
from core.triad_math import (
    coupling_loss_weight,
    flatten_sequence_rows,
    numpy_cross_entropy,
    numpy_softmax,
    total_loss_scalar,
)


def test_flatten_sequence_padding() -> None:
    rows = flatten_sequence_rows([[1.0] * FEATURE_DIM] * 3)
    assert len(rows) == FEATURE_DIM * SEQUENCE_LEN
    assert rows[0] == 0.0


def test_numpy_softmax_sums_to_one() -> None:
    p = numpy_softmax([1.0, 2.0, 3.0])
    assert abs(sum(p) - 1.0) < 1e-9


def test_coupling_loss_monotonic() -> None:
    assert coupling_loss_weight(0.9) < coupling_loss_weight(0.1)
    assert coupling_loss_weight(0.0) == 10.0


def test_total_loss_composition() -> None:
    loss = total_loss_scalar(0.5, 0.4, 0.3, couple_weight=0.85, confidence=0.9)
    expected = 1.2 + 0.3 * coupling_loss_weight(0.85)
    assert abs(loss - expected) < 1e-9


def test_numpy_cross_entropy() -> None:
    probs = numpy_softmax([2.0, 0.5, -1.0])
    ce = numpy_cross_entropy(probs, 0)
    assert ce > 0
