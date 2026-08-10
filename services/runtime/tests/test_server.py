"""FastAPI integration tests (no camera)."""
from __future__ import annotations

import io

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.server import app

client = TestClient(app)


def _jpeg_bytes() -> bytes:
    arr = np.full((64, 64, 3), 120, dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True


def test_metrics_empty() -> None:
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "predictions" in res.json()


def test_infer_frame_jpeg() -> None:
    res = client.post(
        "/infer/frame",
        files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["intent"]
    assert "confidence" in body


def test_feedback_roundtrip() -> None:
    infer = client.post(
        "/infer/frame",
        files={"file": ("frame.jpg", _jpeg_bytes(), "image/jpeg")},
    ).json()
    pid = infer.get("prediction_id")
    assert pid
    fb = client.post(
        "/feedback",
        json={"prediction_id": pid, "rating": 1, "corrected_intent": "play"},
    )
    assert fb.status_code == 200
    assert fb.json()["feedback_id"]


def test_infer_audio_endpoint() -> None:
    res = client.post(
        "/infer/audio",
        json={"audio_arousal": 0.8, "audio_valence": 0.5, "audio_bark_prob": 0.95},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["audio_modality"]["audio_arousal"] == 0.8
    assert body["audio_modality"]["audio_bark_prob"] == 0.95


def test_cameras_endpoint_shape() -> None:
    res = client.get("/cameras")
    assert res.status_code == 200
    body = res.json()
    assert "cameras" in body
    assert isinstance(body["cameras"], list)
    assert "current" in body
    assert "running" in body


def test_live_camera_switch_rejects_while_stopped_safely() -> None:
    # Live-switch should not crash and reports a resolved source string.
    res = client.post(
        "/live/camera",
        json={"camera": 0, "mode": "server"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "switched"
    assert body["camera"]
    client.post("/live/stop")


def test_live_camera_accepts_string_index() -> None:
    res = client.post("/live/camera", json={"camera": "0", "mode": "server"})
    assert res.status_code == 200
    assert res.json()["status"] == "switched"
    client.post("/live/stop")

