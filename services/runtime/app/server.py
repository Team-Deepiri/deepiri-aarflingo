"""FastAPI server for live AARF runtime."""
from __future__ import annotations

import asyncio
import socket
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.engine import STATE, _load_service_package, broadcast, list_cameras, live_status, process_jpeg, reset_sync, switch_camera, update_audio_modality, update_collar_modality, webcam_loop
from app.dog_profile import PERSONALITIES, TRAIT_KEYS, DogProfile, load_profile, save_profile
from app.gaze_zones import _zones_path, read_zones, reload_zones, write_zones
from app.platform import (
    bridge_stream_url,
    client_bridge_stream_url,
    ensure_webcam_bridge,
    is_wsl,
    local_lan_ip,
    platform_name,
    windows_host_ip,
)


def lan_ip() -> str:
    """Best-effort primary LAN IPv4 address (e.g. 192.168.x.x)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        pass
    return "127.0.0.1"


def web_root() -> Path:
    """Built studio UI (`apps/aarf-studio/dist`); falls back to repo root if absent."""
    root = Path(__file__).resolve().parents[3]
    dist = root / "apps" / "aarf-studio" / "dist"
    return dist if dist.exists() else root


class AudioBody(BaseModel):
    audio_arousal: float = 0.0
    audio_valence: float = 0.0
    audio_bark_prob: float = 0.0


class FeedbackBody(BaseModel):
    prediction_id: str
    rating: int | None = None
    corrected_intent: str | None = None
    corrected_emotion: str | None = None
    corrected_behavior: str | None = None


class StartBody(BaseModel):
    camera: int | str = 0
    dog_id: str = "default"
    mode: str | None = None  # browser | server | bridge


class CameraBody(BaseModel):
    camera: int | str = 0
    mode: str | None = None  # browser | server | bridge


class ZonesBody(BaseModel):
    zones: dict[str, dict[str, float]]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


app = FastAPI(title="AARFLingo Runtime", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "running": STATE.running,
        "session_id": STATE.session_id,
        "wsl": is_wsl(),
        "bridge_url": bridge_stream_url(),
        "voice": live_status().get("voice", {}),
    }


@app.get("/bridge/info")
def bridge_info() -> dict:
    return {
        "platform": platform_name(),
        "wsl": is_wsl(),
        "windows_host": windows_host_ip(),
        "lan_ip": local_lan_ip(),
        "stream_url": client_bridge_stream_url(),
        "health_url": client_bridge_stream_url().replace("/video/stream", "/health"),
        "internal_stream_url": bridge_stream_url(),
        "start_windows": "powershell -File scripts/webcam/start_webcam_bridge.ps1",
    }


@app.post("/bridge/start")
def bridge_start() -> dict:
    """Auto-detect the platform/OS and ensure the webcam bridge is running."""
    status = ensure_webcam_bridge()
    return {
        "status": status,
        "health_url": client_bridge_stream_url().replace("/video/stream", "/health"),
        "ok": status == "bridge:ok" or "auto-started" in status or "auto-start-sent" in status,
    }


@app.get("/metrics")
def metrics() -> dict:
    return STATE.store.metrics() if STATE.store else {}


@app.get("/live/status")
def live_status_endpoint() -> dict:
    """Streaming telemetry: fps, avg inference latency, sequence window, uptime."""
    return live_status()


class DogProfileBody(BaseModel):
    name: str | None = None
    breed: str | None = None
    age_years: float | None = None
    weight_kg: float | None = None
    traits: dict[str, int] | None = None
    personality: str | None = None
    baseline_hr_bpm: float | None = None
    baseline_tail_deg: float | None = None
    notes: str | None = None


@app.get("/dog/profile")
def dog_profile_get() -> dict:
    """Current dog profile (traits + personality) for STATE.dog_id."""
    profile = load_profile(STATE.dog_id)
    return {
        **{
            k: getattr(profile, k)
            for k in ("dog_id", "name", "breed", "age_years", "weight_kg", "personality", "baseline_hr_bpm", "baseline_tail_deg", "notes", "updated_ms")
        },
        "traits": profile.traits,
        "trait_keys": TRAIT_KEYS,
        "personalities": PERSONALITIES,
    }


@app.post("/dog/profile")
def dog_profile_post(body: DogProfileBody) -> dict:
    profile = load_profile(STATE.dog_id)
    for k in ("name", "breed", "age_years", "weight_kg", "personality", "baseline_hr_bpm", "baseline_tail_deg", "notes"):
        v = getattr(body, k)
        if v is not None:
            setattr(profile, k, v)
    if body.traits is not None:
        for k, v in body.traits.items():
            if k in TRAIT_KEYS:
                profile.traits[k] = max(1, min(10, int(v)))
    save_profile(profile)
    return {"ok": True, "profile": dog_profile_get()}


@app.get("/gaze/zones")
def gaze_zones_get() -> dict:
    """Current gaze zones (normalized 0–1 rects) + where they persist."""
    zones = read_zones()
    return {
        "ok": True,
        "zones": zones,
        "path": str(_zones_path(None)),
        "reloaded": False,
    }


@app.put("/gaze/zones")
def gaze_zones_put(body: ZonesBody) -> dict:
    """Persist gaze zones. Applied live when the perception pipeline is loaded."""
    zones = {name: dict(vals) for name, vals in body.zones.items()}
    path = write_zones(zones)
    reloaded = reload_zones()
    return {
        "ok": True,
        "zones": read_zones(path),
        "path": str(path),
        "reloaded": reloaded,
    }


@app.get("/predictions/recent")
def recent() -> list:
    return STATE.store.recent_predictions(30) if STATE.store else []


@app.get("/voice/outcomes")
def voice_outcomes() -> list:
    """Recent voice utterances + dog bark responses."""
    return STATE.store.recent_voice_outcomes(50) if STATE.store else []


@app.get("/voice/weights")
def voice_weights() -> dict:
    """Current learned phrase weights for this dog."""
    if STATE.conversation is not None:
        return STATE.conversation.phrase_weights()
    return {}


@app.get("/cameras")
def cameras_endpoint() -> dict:
    """List local OpenCV-visible camera indices for the camera input switch."""
    return {
        "cameras": list_cameras(),
        "current": str(STATE.camera_index),
        "running": STATE.running,
        "bridge_available": bridge_info()["wsl"] or True,
        "mode_hint": "On WSL use bridge mode; the Windows host camera streams via MJPEG.",
    }


@app.post("/live/camera")
async def live_camera(body: CameraBody) -> dict:
    """Live-switch the capture source without restarting the server."""
    camera: int | str = body.camera
    if isinstance(camera, str) and camera.isdigit():
        camera = int(camera)
    resolved = switch_camera(camera, body.mode)
    return {"status": "switched", "camera": resolved, "running": STATE.running}


@app.post("/live/start")
async def live_start(body: StartBody) -> dict:
    if STATE.running:
        return {"status": "already_running", "session_id": STATE.session_id}
    camera: int | str = body.camera
    if isinstance(camera, str) and camera.isdigit():
        camera = int(camera)
    # Server mode reads a local OpenCV camera directly; only bridge mode (or
    # WSL with no native webcam) should route through the MJPEG bridge URL.
    if body.mode == "bridge" or (is_wsl() and isinstance(camera, int) and body.mode != "server"):
        camera = bridge_stream_url()
    STATE.camera_index = camera
    STATE.dog_id = body.dog_id
    STATE.started_at = None
    STATE.frame_count = 0
    STATE.infer_count = 0
    STATE.infer_total_ms = 0.0
    STATE.sequence.clear()
    reset_sync()
    STATE.camera_task = asyncio.create_task(webcam_loop(camera))
    return {"status": "started", "camera": camera, "mode": body.mode or "server", "wsl": is_wsl()}


@app.post("/live/stop")
async def live_stop() -> dict:
    STATE.running = False
    task = STATE.camera_task
    if task is not None:
        try:
            task.cancel()
        except Exception:
            pass
        STATE.camera_task = None
    return {"status": "stopping"}


@app.post("/infer/frame")
async def infer_frame(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    result = process_jpeg(data)
    result["type"] = "prediction"
    await broadcast(result)
    return result


@app.post("/infer/audio")
def infer_audio(body: AudioBody) -> dict:
    mod = update_audio_modality(body.audio_arousal, body.audio_valence, body.audio_bark_prob)
    return {"status": "ok", "audio_modality": mod}


@app.post("/infer/collar")
def infer_collar(body: dict) -> dict:
    mod = update_collar_modality(body)
    return {"status": "ok", "collar_modality": mod}


@app.post("/live/retrain")
def live_retrain() -> dict:
    root = Path(__file__).resolve().parents[3]
    fb = root / "artifacts" / "feedback" / "export.json"
    if STATE.store:
        n = STATE.store.export_training_json(fb)
    else:
        n = 0
    train_mod = _load_service_package("forecast", "train")
    result = train_mod.train_epochs(epochs=15, feedback_path=fb if n else None)
    _forecast_infer = _load_service_package("forecast", "infer")
    _forecast_infer.reset_model_cache()
    return {"status": "ok", "feedback_samples": n, "train": result}


@app.post("/feedback")
def post_feedback(body: FeedbackBody) -> dict:
    fid = STATE.store.add_feedback(
        body.prediction_id,
        rating=body.rating,
        corrected_intent=body.corrected_intent,
        corrected_emotion=body.corrected_emotion,
        corrected_behavior=body.corrected_behavior,
    )
    return {"feedback_id": fid}


@app.websocket("/ws/live")
async def ws_live(ws: WebSocket) -> None:
    await ws.accept()
    q: asyncio.Queue = asyncio.Queue(maxsize=32)
    STATE.subscribers.append(q)
    try:
        while True:
            if not q.empty():
                msg = await q.get()
                await ws.send_json(msg)
            try:
                data = await asyncio.wait_for(ws.receive_json(), timeout=0.05)
            except asyncio.TimeoutError:
                continue
            if data.get("type") == "ping":
                await ws.send_json({"type": "pong"})
            elif data.get("type") == "audio":
                update_audio_modality(
                    audio_arousal=float(data.get("audio_arousal", 0.0)),
                    audio_valence=float(data.get("audio_valence", 0.0)),
                    audio_bark_prob=float(data.get("audio_bark_prob", 0.0)),
                )
            elif data.get("type") == "feedback":
                if STATE.store:
                    STATE.store.add_feedback(
                        data["prediction_id"],
                        rating=data.get("rating"),
                        corrected_intent=data.get("corrected_intent"),
                    )
    except WebSocketDisconnect:
        pass
    finally:
        if q in STATE.subscribers:
            STATE.subscribers.remove(q)


_root = web_root()
if (_root / "index.html").exists():
    app.mount("/", StaticFiles(directory=_root, html=True), name="studio")
