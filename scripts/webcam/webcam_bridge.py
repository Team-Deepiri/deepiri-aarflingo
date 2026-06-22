"""
Webcam bridge for WSL / Docker dev — streams Windows (or Linux) webcam as MJPEG.

Runs on the host with real camera access. WSL runtime consumes:
  http://<windows-host>:8766/video/stream

Pattern adapted from lighthouse-avionics-video-processing.
"""
from __future__ import annotations

import argparse
import logging
import time

import cv2
import numpy as np
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("aarflingo-webcam-bridge")

app = Flask(__name__)
CORS(app)

_video_capture: cv2.VideoCapture | None = None
_current_source: str | int = "0"


def _open_capture(source: str | int) -> cv2.VideoCapture | None:
    global _video_capture, _current_source
    if _video_capture is not None:
        _video_capture.release()
        _video_capture = None
    try:
        parsed: str | int = int(source) if str(source).isdigit() else source
    except ValueError:
        parsed = source
    logger.info("Opening video source: %s", parsed)
    cap = cv2.VideoCapture(parsed)
    if not cap.isOpened():
        logger.error("Failed to open source: %s", parsed)
        return None
    ok, _ = cap.read()
    if not ok:
        cap.release()
        logger.error("Source opened but no frames: %s", parsed)
        return None
    if isinstance(parsed, str) and not str(parsed).startswith("http"):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    _video_capture = cap
    _current_source = source
    return cap


def _error_frame(message: str) -> bytes:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(frame, message[:48], (24, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    return buf.tobytes() if ok else b""


def _generate_frames(source: str | int):
    cap = _open_capture(source)
    if cap is None:
        err = _error_frame("Webcam unavailable")
        while True:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + err + b"\r\n"
            time.sleep(0.5)
        return

    while True:
        ok, frame = cap.read()
        if not ok:
            cap.release()
            global _video_capture
            _video_capture = None
            cap = _open_capture(source)
            if cap is None:
                err = _error_frame("Stream lost")
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + err + b"\r\n"
                time.sleep(0.5)
                continue
            continue
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        if ok:
            data = buf.tobytes()
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + data + b"\r\n"


@app.route("/video/stream")
def video_stream():
    source = app.config.get("VIDEO_SOURCE", "0")
    return Response(_generate_frames(source), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/health")
def health():
    cap = _open_capture(app.config.get("VIDEO_SOURCE", "0")) if _video_capture is None else _video_capture
    return jsonify(
        {
            "status": "ok",
            "video_available": cap is not None and cap.isOpened(),
            "source": str(app.config.get("VIDEO_SOURCE", "0")),
            "service": "aarflingo-webcam-bridge",
        }
    )


@app.route("/api/source", methods=["GET", "POST"])
def api_source():
    if request.method == "GET":
        return jsonify({"source": str(app.config.get("VIDEO_SOURCE", "0"))})
    data = request.get_json(silent=True) or {}
    new_source = data.get("source", "0")
    app.config["VIDEO_SOURCE"] = new_source
    _open_capture(new_source)
    return jsonify({"status": "ok", "source": str(new_source)})


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
    app.config["VIDEO_SOURCE"] = args.source
    app.config["PORT"] = args.port
    print(f"Aarflingo webcam bridge http://{args.host}:{args.port}/video/stream")
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
