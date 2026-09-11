"""Home-capture tooling: bridge source resolution, auto-label rows, YOLO prep, breed extra stills."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.breed_train import merge_extra_stills
from app.dog_dataset import (
    _nameserver_ip,
    auto_label,
    load_labels,
    prep_dog_yolo,
    yolo_rows_from_result,
)


# ── nameserver / bridge candidates ────────────────────────────────────────

def test_nameserver_ip_parses_first_entry():
    text = "# comment\nnameserver 10.255.255.254\nnameserver 1.1.1.1\n"
    assert _nameserver_ip(text) == "10.255.255.254"


def test_nameserver_ip_none_when_absent():
    assert _nameserver_ip("search lan\noptions edns0\n") is None


def test_bridge_candidates_dedupe_loopback():
    from app.dog_dataset import bridge_stream_candidates

    urls = bridge_stream_candidates(port=9999)
    assert urls[0] == "http://127.0.0.1:9999"
    assert len(urls) == len(set(urls))


# ── yolo result → jsonl rows ──────────────────────────────────────────────

def _fake_result(path: str, boxes: list[tuple[int, float, tuple[float, float, float, float]]]):
    """boxes: (cls_id, conf, (cx, cy, w, h)) — plain lists exercise the non-tensor path."""
    return SimpleNamespace(
        path=path,
        names={16: "dog", 15: "cat"},
        boxes=SimpleNamespace(
            cls=[b[0] for b in boxes],
            conf=[b[1] for b in boxes],
            xywhn=[list(b[2]) for b in boxes],
        ),
    )


def test_yolo_rows_filters_low_conf_and_maps_names():
    result = _fake_result(
        "/x/frame_00001.jpg",
        [(16, 0.9, (0.5, 0.5, 0.4, 0.6)), (16, 0.1, (0.2, 0.2, 0.1, 0.1)), (15, 0.8, (0.7, 0.7, 0.2, 0.2))],
    )
    rows = yolo_rows_from_result(result, conf=0.25)
    # low-conf dog dropped; cat kept (any class is labelable)
    assert len(rows) == 2
    dog = next(r for r in rows if r["cls"] == "dog")
    assert (dog["x"], dog["y"], dog["w"], dog["h"]) == (0.5, 0.5, 0.4, 0.6)
    assert dog["file"] == "frame_00001.jpg"


def test_yolo_rows_empty_when_no_boxes():
    result = SimpleNamespace(path="/x/f.jpg", names={}, boxes=None)
    assert yolo_rows_from_result(result) == []


# ── auto_label merge policy ───────────────────────────────────────────────

def test_auto_label_keeps_existing_rows_without_overwrite(tmp_path, monkeypatch):
    captures = tmp_path / "captures"
    captures.mkdir()
    for i in range(3):
        (captures / f"frame_{i:05d}.jpg").write_bytes(b"jpg")

    labels = tmp_path / "labels.jsonl"
    labels.write_text(json.dumps({"file": "frame_00000.jpg", "cls": "dog", "x": 0.5, "y": 0.5, "w": 0.3, "h": 0.3}) + "\n")

    class FakeModel:
        def __init__(self, weights):
            self.weights = weights

        def predict(self, source, stream=False, conf=0.25, verbose=False):
            def gen():
                for i in range(3):
                    yield _fake_result(str(captures / f"frame_{i:05d}.jpg"), [(16, 0.9, (0.4, 0.4, 0.2, 0.2))])

            return gen()

    monkeypatch.setitem(sys.modules, "ultralytics", SimpleNamespace(YOLO=FakeModel))
    out = auto_label(captures_dir=captures, labels_path=labels, overwrite=False)

    rows = load_labels(labels)
    assert out["files_kept_existing"] == 1
    assert out["files_labeled"] == 2
    kept = [r for r in rows if r["file"] == "frame_00000.jpg"]
    assert len(kept) == 1 and kept[0]["x"] == 0.5  # prior row preserved verbatim


def test_auto_label_requires_images(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    try:
        auto_label(captures_dir=empty, labels_path=tmp_path / "l.jsonl")
    except RuntimeError as e:
        assert "no images" in str(e)
    else:
        raise AssertionError("expected RuntimeError for empty captures dir")


# ── prep_dog_yolo multi-rect + splits ─────────────────────────────────────

def test_prep_dog_yolo_writes_all_rects_per_file(tmp_path):
    captures = tmp_path / "captures"
    captures.mkdir()
    for name in ("a.jpg", "b.jpg"):
        (captures / name).write_bytes(b"jpg")

    labels = tmp_path / "labels.jsonl"
    rows = [
        {"file": "a.jpg", "cls": "dog", "x": 0.5, "y": 0.5, "w": 0.4, "h": 0.6},
        {"file": "a.jpg", "cls": "dog", "x": 0.2, "y": 0.2, "w": 0.1, "h": 0.1},
    ]
    labels.write_text("\n".join(json.dumps(r) for r in rows) + "\n")

    out = tmp_path / "dataset"
    result = prep_dog_yolo(captures_dir=captures, labels_path=labels, out_dir=out)

    assert result["images"] == 2
    assert result["labels_converted"] == 2
    txts = list(out.rglob("labels/a.txt"))
    assert len(txts) == 1
    lines = txts[0].read_text().strip().splitlines()
    assert len(lines) == 2
    assert lines[0].startswith("0 0.500000 0.500000")


def test_prep_dog_yolo_unlabeled_becomes_background(tmp_path):
    captures = tmp_path / "captures"
    captures.mkdir()
    (captures / "solo.jpg").write_bytes(b"jpg")
    labels = tmp_path / "labels.jsonl"
    labels.write_text("")

    out = tmp_path / "dataset"
    prep_dog_yolo(captures_dir=captures, labels_path=labels, out_dir=out)
    txts = list(out.rglob("labels/solo.txt"))
    assert len(txts) == 1 and txts[0].read_text() == ""


# ── breed extra stills ────────────────────────────────────────────────────

def test_merge_extra_stills_matches_known_and_appends_new(tmp_path):
    extra = tmp_path / "breed"
    known = extra / "n02085620-Chihuahua"
    new = extra / "MyDog mix"
    known.mkdir(parents=True)
    new.mkdir(parents=True)
    for i in range(10):
        (known / f"k{i}.jpg").write_bytes(b"jpg")
    for i in range(3):
        (new / f"n{i}.jpg").write_bytes(b"jpg")

    labels = ["Chihuahua", "Labrador retriever"]
    train: list = []
    val: list = []
    train, val, labels, stats = merge_extra_stills(extra, labels, train, val, seed=42)

    assert stats["extra_images"] == 13
    assert stats["per_class"] == {"Chihuahua": 10, "MyDog mix": 3}
    assert labels == ["Chihuahua", "Labrador retriever", "MyDog mix"]
    chis = [(p, idx) for p, idx in train + val if idx == 0]
    mixes = [(p, idx) for p, idx in train + val if idx == 2]
    assert len(chis) == 10 and len(mixes) == 3
    # >1 image per class reserves a val slice; single-digit small classes may be all-train
    assert any(idx == 0 for _, idx in val)


def test_merge_extra_stills_synset_prefix_stripped(tmp_path):
    extra = tmp_path / "breed"
    d = extra / "n02085782-English_foxhound"
    d.mkdir(parents=True)
    (d / "x.jpg").write_bytes(b"jpg")

    labels = ["English foxhound"]
    train: list = []
    val: list = []
    _, _, labels_out, stats = merge_extra_stills(extra, labels, train, val)
    assert stats["per_class"] == {"English foxhound": 1}
    assert all(idx == 0 for _, idx in train)
