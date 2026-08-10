"""
Webcam bridge for WSL / Docker dev — streams Windows (or Linux) webcam as MJPEG.

Runs on the host with real camera access. WSL runtime consumes:
  http://<windows-host>:8766/video/stream

Design (single-writer / many-readers):
  A single CameraOwner thread owns the cv2.VideoCapture handle and continuously
  publishes the latest encoded JPEG to a shared slot guarded by a lock. Every
  /video/stream client just serves whatever is in the slot — clients NEVER open,
  release, or touch the camera handle. This makes concurrent connections (browser
  <img>, runtime server-mode loop, health probes) safe by construction: the old
  per-connection `_open_capture()` design released the global capture out from
  under whichever client was mid-read, wedging the camera into "Webcam
  unavailable" under any real load.

Pattern adapted from lighthouse-avionics-video-processing.
"""
from __future__ import annotations

import argparse
import logging
import threading
import time

import cv2
import numpy as np
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("aarflingo-webcam-bridge")

app = Flask(__name__)
CORS(app)

# Publisher slot: (capture_time_monotonic, jpeg_bytes). Guarded by _slot_lock.
_slot: tuple[float, bytes] | None = None
_slot_lock = threading.Lock()
_owner_started = False
_owner_start_lock = threading.Lock()

# Keep one error frame around so clients always get *some* image while the
# camera is unavailable (the <img> element shows the message instead of hanging).
_error_jpeg: bytes | None = None


def _make_error_jpeg(message: str) -> bytes:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, message[:48], (24, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    return buf.tobytes() if ok else b""


def _parse_source(source: str | int) -> str | int:
    if isinstance(source, int):
        return source
    try:
        return int(source) if str(source).isdigit() else source
    except ValueError:
        return source


def _open_capture(source: str | int) -> cv2.VideoCapture | None:
    parsed = _parse_source(source)
    logger.info("Opening video source: %s", parsed)
    try:
        cap = cv2.VideoCapture(parsed)
        if not cap.isOpened():
            logger.error("Failed to open source: %s", parsed)
            return None
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        ok, _ = cap.read()
        if not ok:
            cap.release()
            logger.error("Source opened but no frames: %s", parsed)
            return None
    except Exception as exc:  # noqa: BLE001 - OpenCV raises across backends
        logger.error("Exception opening source %s: %s", parsed, exc)
        return None
    return cap


def _camera_owner_loop(source: str | int, stop: threading.Event) -> None:
    """Single writer: owns the capture, publishes the latest frame forever."""
    global _slot, _error_jpeg
    cap: cv2.VideoCapture | None = None
    consecutive_failures = 0
    while not stop.is_set():
        if cap is None:
            cap = _open_capture(source)
            if cap is None:
                consecutive_failures += 1
                err = _make_error_jpeg(
                    "Webcam unavailable" if consecutive_failures > 2 else "Starting camera…"
                )
                with _slot_lock:
                    _slot = (time.monotonic(), err)
                    _error_jpeg = err
                # Back off a little on repeated failures, retry fast on first.
                stop.wait(min(0.5 * consecutive_failures, 3.0))
                continue
            consecutive_failures = 0
            logger.info("Camera owner streaming source %s", _parse_source(source))

        ok, frame = cap.read()
        if not ok:
            logger.warning("Camera read failed — reopening source %s", _parse_source(source))
            cap.release()
            cap = None
            err = _make_error_jpeg("Stream lost")
            with _slot_lock:
                _slot = (time.monotonic(), err)
                _error_jpeg = err
            stop.wait(0.3)
            continue

        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        if ok:
            with _slot_lock:
                _slot = (time.monotonic(), buf.tobytes())
        stop.wait(1 / 30)

    if cap is not None:
        cap.release()


_owner_thread: threading.Thread | None = None
_owner_stop: threading.Event | None = None
_owner_source: str | int = "0"


def start_owner(source: str | int) -> None:
    """(Re)start the camera owner thread for the given source. Idempotent per source."""
    global _owner_thread, _owner_stop, _owner_source
    with _owner_start_lock:
        if _owner_thread is not None and _owner_thread.is_alive() and _owner_source == source:
            return
        if _owner_stop is not None:
            _owner_stop.set()
        if _owner_thread is not None:
            _owner_thread.join(timeout=2.0)
        _owner_source = source
        _owner_stop = threading.Event()
        _owner_thread = threading.Thread(
            target=_camera_owner_loop,
            args=(source, _owner_stop),
            daemon=True,
            name="aarflingo-camera-owner",
        )
        _owner_thread.start()


def latest_frame() -> tuple[float, bytes] | None:
    """Copy of the newest published frame, or None if none yet."""
    with _slot_lock:
        return _slot


@app.route("/video/stream")
def video_stream():
    source = app.config.get("VIDEO_SOURCE", "0")
    start_owner(source)

    def generate():
        last_seq: tuple[float, bytes] | None = None
        while True:
            slot = latest_frame()
            if slot is not None and slot != last_seq:
                last_seq = slot
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + slot[1] + b"\r\n"
            time.sleep(1 / 30)

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/health")
def health():
    source = app.config.get("VIDEO_SOURCE", "0")
    slot = latest_frame()
    fresh = slot is not None and (time.monotonic() - slot[0]) < 2.0
    # If nothing has streamed yet, kick the owner once so the first probe is useful.
    if not fresh:
        start_owner(source)
    return jsonify(
        {
            "status": "ok",
            "video_available": bool(fresh),
            "source": str(_parse_source(source)),
            "service": "aarflingo-webcam-bridge",
        }
    )


@app.route("/api/source", methods=["GET", "POST"])
def api_source():
    if request.method == "GET":
        return jsonify({"source": str(_parse_source(_owner_source))})
    data = request.get_json(silent=True) or {}
    new_source = _parse_source(data.get("source", "0"))
    app.config["VIDEO_SOURCE"] = new_source
    start_owner(new_source)
    return jsonify({"status": "ok", "source": str(_parse_source(new_source))})


@app.route("/")
def index():
    port = app.config.get("PORT", 8766)
    return f"""<!doctype html>
<html><head><title>Aarflingo Webcam Bridge</title></head>
<body style="font-family:system-ui;background:#0f1419;color:#e7ecf3;padding:1.5rem">
<h1>Aarflingo webcam bridge</h1>
<p>Stream: <code>http://localhost:{port}/video/stream</code></p>
<p>WSL runtime: <code>http://&lt;windows-host&gt;:{port}/video/stream</code></p>
<img src="/video/stream" style="max-width:720px;border-radius:12px;border:1px solid #2a3441" />
</body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Aarflingo MJPEG webcam bridge")
    parser.add_argument("--source", default="0", help='Webcam index "0" or video path/URL')
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    app.config["VIDEO_SOURCE"] = _parse_source(args.source)
    app.config["PORT"] = args.port
    start_owner(_parse_source(args.source))
    print(f"Aarflingo webcam bridge http://{args.host}:{args.port}/video/stream")
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
