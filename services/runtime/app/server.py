"""FastAPI server for live AARF runtime."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pathlib import Path

from app.engine import _load_file, _load_service_module, STATE, broadcast, process_jpeg, webcam_loop


class FeedbackBody(BaseModel):
    prediction_id: str
    rating: int | None = None
    corrected_intent: str | None = None
    corrected_emotion: str | None = None
    corrected_behavior: str | None = None


class StartBody(BaseModel):
    camera: int = 0
    dog_id: str = "default"


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
    return {"ok": True, "running": STATE.running, "session_id": STATE.session_id}


@app.get("/metrics")
def metrics() -> dict:
    return STATE.store.metrics() if STATE.store else {}


@app.get("/predictions/recent")
def recent() -> list:
    return STATE.store.recent_predictions(30) if STATE.store else []


@app.post("/live/start")
async def live_start(body: StartBody) -> dict:
    if STATE.running:
        return {"status": "already_running", "session_id": STATE.session_id}
    STATE.camera_index = body.camera
    STATE.dog_id = body.dog_id
    asyncio.create_task(webcam_loop(body.camera))
    return {"status": "started", "camera": body.camera}


@app.post("/live/stop")
async def live_stop() -> dict:
    STATE.running = False
    return {"status": "stopping"}


@app.post("/infer/frame")
async def infer_frame(file: UploadFile = File(...)) -> dict:
    data = await file.read()
    result = process_jpeg(data)
    result["type"] = "prediction"
    await broadcast(result)
    return result


@app.post("/live/retrain")
def live_retrain() -> dict:
    root = Path(__file__).resolve().parents[3]
    fb = root / "artifacts" / "feedback" / "export.json"
    if STATE.store:
        n = STATE.store.export_training_json(fb)
    else:
        n = 0
    train_mod = _load_service_module("forecast", "train")
    result = train_mod.train_epochs(epochs=15, feedback_path=fb if n else None)
    _forecast_infer = _load_service_module("forecast", "infer")
    _forecast_infer._MODEL = None
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
            elif data.get("type") == "feedback":
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
