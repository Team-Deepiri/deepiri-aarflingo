"""Real dog image ingestion: breed parsing, collection, JSONL round-trip."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np

from app.vision_data import (
    collect_features,
    find_images,
    load_jsonl,
    parse_breed,
    summarize_rows,
    write_jsonl,
)


def _make_image(root: Path, rel: str, color=(120, 80, 60)) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), np.full((64, 64, 3), color, np.uint8))
    return path


def test_parse_breed_from_stanford_folder() -> None:
    p = Path("images/n02085620-Chihuahua/n02085620_1012.jpg")
    assert parse_breed(p) == "Chihuahua"
    assert parse_breed(Path("images/n02099601-Golden_retriever/n02099601_1001.jpg")) == "Golden retriever"
    assert parse_breed(Path("photos/dog.jpg")) is None


def test_find_images_walks_and_ignores_non_images(tmp_path: Path) -> None:
    _make_image(tmp_path, "images/n02085620-Chihuahua/n02085620_1012.jpg")
    (tmp_path / "images" / "readme.txt").write_text("hello")
    imgs = list(find_images(tmp_path))
    assert len(imgs) == 1
    assert imgs[0].breed == "Chihuahua"


def test_collect_features_filters_non_float_keys(tmp_path: Path) -> None:
    _make_image(tmp_path, "images/n02085620-Chihuahua/n02085620_1012.jpg")

    def fake_pipeline(frame):
        return {"dog_present": 1.0, "motion": 0.02, "bbox": {"x": 0}, "scene": ["bright"]}

    rows = collect_features(tmp_path, fake_pipeline, limit=5)
    assert len(rows) == 1
    assert rows[0].breed == "Chihuahua"
    assert "bbox" not in rows[0].features
    assert "scene" not in rows[0].features
    assert rows[0].features["dog_present"] == 1.0


def test_collect_features_skips_undecodable(tmp_path: Path) -> None:
    bad = tmp_path / "images" / "n02085620-Chihuahua" / "broken.jpg"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"not an image")
    _make_image(tmp_path, "images/n02085620-Chihuahua/n02085620_1012.jpg")

    rows = collect_features(tmp_path, lambda f: {"dog_present": 1.0}, limit=5)
    assert len(rows) == 1


def test_jsonl_round_trip_and_summary(tmp_path: Path) -> None:
    _make_image(tmp_path, "images/n02085620-Chihuahua/n02085620_1012.jpg")
    rows = collect_features(tmp_path, lambda f: {"dog_present": 1.0, "motion": 0.0}, limit=5)
    out = tmp_path / "feats.jsonl"
    written = write_jsonl(rows, out)
    assert written == out and out.exists()
    loaded = load_jsonl(out)
    assert len(loaded) == 1
    summary = summarize_rows(loaded)
    assert summary["images"] == 1
    assert summary["dog_present"] == 1.0
    assert "Chihuahua" in summary["breeds"]
    assert summary["feature_dim"] == 2
