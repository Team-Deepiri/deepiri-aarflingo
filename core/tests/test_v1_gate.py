"""v1.0 readiness gate — written first. The 95% bar must not pass on synthetic acc."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_dog_split_metrics_need_three_dogs_and_ignore_perfect_two() -> None:
    from core.v1_gate import dog_split_metrics, meets_accuracy_bar

    rows = [
        {"dog_id": "a", "y_true": "play", "y_pred": "play"},
        {"dog_id": "b", "y_true": "rest", "y_pred": "rest"},
    ]
    m = dog_split_metrics(rows)
    assert m["n_dogs"] == 2
    assert m["accuracy"] == 1.0
    assert meets_accuracy_bar(m) is False


def test_dog_split_metrics_three_dogs_at_95_passes_accuracy_only() -> None:
    from core.v1_gate import dog_split_metrics, meets_accuracy_bar

    rows = []
    for dog, label in (("a", "play"), ("b", "rest"), ("c", "outside")):
        for _ in range(19):
            rows.append({"dog_id": dog, "y_true": label, "y_pred": label})
        rows.append({"dog_id": dog, "y_true": label, "y_pred": "avoid"})
    m = dog_split_metrics(rows)
    assert m["n_dogs"] == 3
    assert m["accuracy"] == pytest.approx(0.95)
    assert meets_accuracy_bar(m) is True


def test_empty_eval_does_not_meet_bar() -> None:
    from core.v1_gate import dog_split_metrics, meets_accuracy_bar

    m = dog_split_metrics([])
    assert m["n_dogs"] == 0
    assert m["accuracy"] is None
    assert meets_accuracy_bar(m) is False


def test_synthetic_triad_acc_does_not_count() -> None:
    from core.v1_gate import collect_report

    report = collect_report(ROOT)
    triad = report["metrics"]["triad"]
    assert triad["counts_toward_bar"] is False
    assert report["bar_met"] is False
    assert "dog-split" in " ".join(report["blockers"]).lower() or "home" in " ".join(
        report["blockers"]
    ).lower()


def test_jetson_dockerfile_is_hub_not_wearable() -> None:
    from core.v1_gate import jetson_ready

    text = (ROOT / "infra" / "docker" / "jetson.Dockerfile").read_text(encoding="utf-8")
    info = jetson_ready(ROOT)
    assert "edge-runtime" in text
    assert info["ok"] is True
    assert info["is_wearable"] is False
    assert "app.cli" in text
    assert "firmware/collar" not in text.split("CMD")[-1]


def test_paper_scaffold_lists_required_files() -> None:
    from core.v1_gate import paper_ready

    info = paper_ready(ROOT)
    assert set(info["required"]) >= {"METHODS.md", "RESULTS.md", "DATASHEET.md", "reproduce.md"}
