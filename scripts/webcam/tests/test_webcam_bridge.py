"""Slot-semantics tests for the webcam bridge (single-writer / many-readers).

Requires the bridge's own runtime deps (cv2 + flask). Run from repo root with
the bridge venv active:

    python3 -m venv /tmp/wcb-venv
    /tmp/wcb-venv/bin/pip install -r scripts/webcam/requirements.txt
    PYTHONPATH=scripts/webcam /tmp/wcb-venv/bin/python -m pytest scripts/webcam/tests -q
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pytest
import cv2

import webcam_bridge as w


@pytest.fixture(scope="module")
def clip(tmp_path_factory) -> str:
    path = str(tmp_path_factory.mktemp("wcb") / "clip.mp4")
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 10, (320, 240))
    for i in range(20):
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        frame[:, :, 0] = i * 10
        vw.write(frame)
    vw.release()
    return path


def test_start_owner_is_idempotent(clip):
    w.start_owner(clip)
    thread = w._owner_thread
    w.start_owner(clip)  # same source → no-op
    assert w._owner_thread is thread, "start_owner must not spawn a second thread"

    w.start_owner(clip)  # restarts are safe
    assert w._owner_thread.is_alive()


def test_latest_frame_is_published(clip):
    w.start_owner(clip)
    deadline = time.monotonic() + 5.0
    while w.latest_frame() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    slot = w.latest_frame()
    assert slot is not None, "owner must publish at least one frame"
    stamp, jpeg = slot
    assert jpeg.startswith(b"\xff\xd8"), "slot holds a JPEG"
    assert time.monotonic() - stamp < 5.0


def test_latest_wins(clip):
    w.start_owner(clip)
    deadline = time.monotonic() + 5.0
    while w.latest_frame() is None and time.monotonic() < deadline:
        time.sleep(0.05)
    first = w.latest_frame()
    time.sleep(0.15)
    second = w.latest_frame()
    assert second is not None
    # Slot advances (new capture timestamps) — latest-wins, not first-wins.
    assert second[0] > first[0]


def test_owner_recovers_after_source_loop(clip):
    # The clip is short; the owner must reopen it when reads start failing and
    # keep publishing frames instead of wedging.
    w.start_owner(clip)
    deadline = time.monotonic() + 6.0
    stamps: set[float] = set()
    while time.monotonic() < deadline:
        slot = w.latest_frame()
        if slot:
            stamps.add(round(slot[0], 2))
        time.sleep(0.05)
    assert len(stamps) >= 2, "owner must keep publishing across reopens"
