"""Dog profile — traits, personality archetype, and vitals baseline.

Persisted per dog_id as JSON under artifacts/dog/{dog_id}.json so the studio
can show (and the user can edit) a stable identity across sessions.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

ARTIFACTS = Path(__file__).resolve().parents[3] / "artifacts" / "dog"

TRAIT_KEYS: list[str] = [
    "energy",
    "excitability",
    "friendliness",
    "independence",
    "vocal_tendency",
    "guardiness",
]

PERSONALITIES: list[str] = [
    "Eager Explorer",
    "Gentle Guardian",
    "Reserved Thinker",
    "Bubbly Clown",
    "Steady Companion",
    "Watchful Sentinel",
]


@dataclass
class DogProfile:
    dog_id: str = "default"
    name: str = ""
    breed: str = ""
    age_years: float = 0.0
    weight_kg: float = 0.0
    traits: dict[str, int] = field(default_factory=dict)
    personality: str = "Eager Explorer"
    baseline_hr_bpm: float = 80.0
    baseline_tail_deg: float = 35.0
    notes: str = ""
    updated_ms: int = 0

    def __post_init__(self) -> None:
        for key in TRAIT_KEYS:
            if key not in self.traits:
                self.traits[key] = 5

    @property
    def display_name(self) -> str:
        return self.name or self.dog_id


def profile_path(dog_id: str) -> Path:
    return ARTIFACTS / f"{dog_id}.json"


def load_profile(dog_id: str = "default") -> DogProfile:
    path = profile_path(dog_id)
    if not path.exists():
        return DogProfile(dog_id=dog_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("dog_id", None)
        return DogProfile(dog_id=dog_id, **data)
    except (json.JSONDecodeError, TypeError):
        return DogProfile(dog_id=dog_id)


def save_profile(profile: DogProfile) -> DogProfile:
    profile.updated_ms = int(time.time() * 1000)
    profile_path(profile.dog_id).parent.mkdir(parents=True, exist_ok=True)
    profile_path(profile.dog_id).write_text(
        json.dumps(asdict(profile), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return profile
