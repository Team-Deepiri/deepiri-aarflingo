"""Breed classifier: label mapping, breed-name parsing, and crop classification path."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from app.breed import IMAGENET_DOG_INDICES, _imagenet_names


def test_imagenet_dog_indices_are_breeds() -> None:
    names = _imagenet_names()
    assert len(names) >= 151
    # ImageNet classes 151-268 are the dog-breed synsets (Chihuahua .. Mexican hairless).
    assert names[151].lower() == "chihuahua"
    assert names[268].lower() == "mexican hairless"
    assert len(IMAGENET_DOG_INDICES) == 268 - 151 + 1


def test_imagenet_names_file_present() -> None:
    p = Path(__file__).resolve().parents[1] / "app" / "imagenet_classes.txt"
    assert p.exists(), "imagenet_classes.txt must ship with the breed classifier"


def test_classify_crop_returns_empty_when_unavailable(tmp_path) -> None:
    """A classifier with no weights and no bundled classes returns [] gracefully."""
    from app.breed import BreedClassifier

    clf = BreedClassifier()
    if clf.available:
        return  # model present on this machine — skip the negative-path assertion
    crop = np.zeros((224, 224, 3), dtype=np.uint8)
    assert clf.classify_crop(crop, top_k=3) == []
