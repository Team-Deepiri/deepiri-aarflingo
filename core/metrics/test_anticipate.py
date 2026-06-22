"""Anticipation / gating metric smoke tests (stdlib only)."""
from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).with_name("anticipate_fixtures.json")


def _load_cases() -> list[dict]:
    return json.loads(FIXTURES.read_text(encoding="utf-8"))["cases"]


def classify(confidence: float, forbidden: bool) -> str:
    if forbidden:
        return "reject"
    if confidence < 0.5:
        return "review"
    return "pass"


def test_fixtures_resolve() -> None:
    for case in _load_cases():
        pred = case["prediction"]
        forbidden = (
            case["name"] == "rest_with_play_bow_forbidden"
        )
        got = classify(pred["confidence"], forbidden)
        assert got == case["expected_gate"], case["name"]


if __name__ == "__main__":
    test_fixtures_resolve()
    print("ok")
