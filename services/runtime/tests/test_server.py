"""FastAPI integration tests (no camera)."""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app.gaze_zones as _zones
from app.server import app

client = TestClient(app)

# Point zone persistence at a temp file so tests never touch the repo config.
_TMP_ZONES = Path("/tmp/aarflingo_test_zones.yaml")


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


def test_infer_collar_endpoint_maps_to_physio() -> None:
    res = client.post(
        "/infer/collar",
        json={"hr_bpm": 90, "rmssd_ms": 45, "imu_rms": 0.4, "still": False, "arousal": 0.6},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["collar_modality"]["ecg_hr_norm"] == pytest.approx(0.5)
    assert "audio_arousal" not in body["collar_modality"]


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



def test_gaze_zones_get_returns_defaults() -> None:
    _zones.ZONES_PATH = _TMP_ZONES
    res = client.get("/gaze/zones")
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert set(body["zones"]) >= {"door", "toy", "bowl"}
    for _, z in body["zones"].items():
        assert {"x", "y", "w", "h"} <= set(z)


def test_gaze_zones_put_persists_and_clamps() -> None:
    _zones.ZONES_PATH = _TMP_ZONES
    zones = {
        "door": {"x": 0.6, "y": -0.2, "w": 1.5, "h": 0.3},
        "toy": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2},
    }
    res = client.put("/gaze/zones", json={"zones": zones})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    persisted = body["zones"]
    assert persisted["door"]["y"] == 0.0  # clamped
    assert persisted["door"]["w"] == 1.0  # clamped
    assert persisted["toy"]["x"] == 0.1


def test_gaze_zones_put_roundtrip() -> None:
    _zones.ZONES_PATH = _TMP_ZONES
    fresh = client.get("/gaze/zones").json()["zones"]
    res = client.put("/gaze/zones", json={"zones": fresh}).json()
    assert res["zones"] == fresh


def test_gaze_zones_restore_defaults() -> None:
    _zones.ZONES_PATH = _TMP_ZONES
    _zones.write_zones(dict(_zones.DEFAULT_ZONES))
    res = client.get("/gaze/zones").json()
    assert res["zones"] == _zones.DEFAULT_ZONES
