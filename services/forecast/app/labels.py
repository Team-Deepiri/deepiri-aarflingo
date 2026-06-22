"""Load ethogram label ids for model heads."""
from __future__ import annotations

from pathlib import Path

import yaml


def _load_list(path: Path, key: str) -> list[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [item["id"] for item in data[key]]


def ethogram_root() -> Path:
    return Path(__file__).resolve().parents[3] / "ethogram"


def intent_labels() -> list[str]:
    labels = _load_list(ethogram_root() / "intents.yaml", "intents")
    for extra in ("outside", "play", "food"):
        if extra not in labels:
            labels.append(extra)
    return labels


def emotion_labels() -> list[str]:
    return _load_list(ethogram_root() / "emotions.yaml", "emotions")


def behavior_labels() -> list[str]:
    return _load_list(ethogram_root() / "behaviors.yaml", "behaviors")
