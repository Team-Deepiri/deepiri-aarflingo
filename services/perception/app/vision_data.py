"""Ingest real dog images into the perception pipeline as real feature data.

Real dog images (e.g. Stanford Dogs) are decoded and run through the same
detection → tracking → pose → approach-geometry pipeline used at runtime.
The resulting feature rows are persisted as JSONL so they can be audited,
calibrated, or folded into feedback-driven TriadNet retraining.

Stanford Dogs layout:  images/n02085620-Chihuahua/n02085620_1012.jpg
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator

import numpy as np

IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
SCENE_KEYS = ("bbox", "scene")


@dataclass
class RealImage:
    path: Path
    breed: str | None = None


@dataclass
class RealFeatureRow:
    image: str
    breed: str | None
    features: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload: dict = {"image": self.image, "breed": self.breed}
        payload.update(self.features)
        return payload


def parse_breed(path: Path) -> str | None:
    """Extract a human-readable breed from a Stanford Dogs style folder name.

    'images/n02085620-Chihuahua/n02085620_1012.jpg' -> 'Chihuahua'
    """
    parts = path.parts
    for part in parts:
        if "-" in part and part.split("-", 1)[0].startswith("n0"):
            return part.split("-", 1)[1].replace("_", " ")
    return None


def find_images(root: Path) -> Iterator[RealImage]:
    if not root.is_dir():
        return
    for p in sorted(root.rglob("*")):
        if p.suffix.lower() in IMAGE_EXTS and not p.name.startswith("."):
            yield RealImage(path=p, breed=parse_breed(p))


def decode_image(path: Path, target_size: int = 224) -> np.ndarray:
    """Decode an image file to a BGR uint8 frame with the pipeline's scale.

    Falls back to nearest-neighbor padding when the pipeline expects a
    fixed square input so real frames of any aspect ratio still run.
    """
    import cv2

    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"cannot decode image {path}")
    h, w = img.shape[:2]
    if h == w == target_size:
        return img
    scale = target_size / max(h, w)
    nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
    canvas[:nh, :nw] = resized
    return canvas


def collect_features(
    root: Path,
    pipeline_fn: Callable[[np.ndarray], dict],
    limit: int = 0,
) -> list[RealFeatureRow]:
    """Run the runtime pipeline over real dog images, emitting feature rows.

    Non-feature dict entries (bbox, scene, ...) are stripped so the JSONL
    is a flat feature map compatible with core.vectorize().
    """
    rows: list[RealFeatureRow] = []
    for item in find_images(root):
        if limit and len(rows) >= limit:
            break
        try:
            frame = decode_image(item.path)
        except (ValueError, OSError):
            continue
        try:
            feats = pipeline_fn(frame)
        except Exception:
            continue
        clean = {k: float(v) for k, v in feats.items() if k not in SCENE_KEYS and isinstance(v, (int, float))}
        rows.append(RealFeatureRow(image=str(item.path), breed=item.breed, features=clean))
    return rows


def write_jsonl(rows: list[RealFeatureRow], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row.to_dict()) + "\n")
    return out


def load_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def summarize_rows(rows: list[dict]) -> dict:
    n = len(rows)
    if not n:
        return {"images": 0}
    present = sum(1 for r in rows if float(r.get("dog_present", 0)) > 0.5)
    breeds = {r.get("breed") for r in rows if r.get("breed")}
    keys = sorted({k for r in rows for k in r if k not in ("image", "breed")})
    return {
        "images": n,
        "dog_present": round(present / n, 3),
        "breeds": sorted(breeds),
        "feature_keys": keys,
        "feature_dim": len(keys),
    }
