"""SpeechClient tests against a throwaway local HTTP server + offline fallback."""
from __future__ import annotations

import json
import sys
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.speech_client import SpeechClient


def _wav_bytes() -> bytes:
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 160)
    return buf.getvalue()


class _FakeSpeechHandler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # silence
        pass

    def do_GET(self):
        if self.path.startswith("/health"):
            body = json.dumps({"status": "healthy", "pipecat": True, "livekit": {"worker": True}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith("/v1/tts"):
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            audio = _wav_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Content-Length", str(len(audio)))
            self.end_headers()
            self.wfile.write(audio)
        elif self.path.startswith("/v1/stt"):
            length = int(self.headers.get("Content-Length", 0))
            self.rfile.read(length)
            body = json.dumps(
                {"text": "good dog", "is_final": True, "provider": "fake", "model": "test", "confidence": 0.9}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture(scope="module")
def fake_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeSpeechHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


def test_health_reports_ok(fake_server: str) -> None:
    client = SpeechClient(base_url=fake_server, offline_ok=False)
    health = client.health()
    assert health.ok
    assert health.detail["pipecat"] is True
    assert health.latency_ms >= 0
    client.close()


def test_synthesize_returns_audio(fake_server: str) -> None:
    client = SpeechClient(base_url=fake_server, offline_ok=False)
    audio = client.synthesize("come here buddy")
    assert len(audio) > 0
    with wave.open(BytesIO(audio), "rb") as wf:
        assert wf.getframerate() == 16000
    client.close()


def test_transcribe_returns_text(fake_server: str) -> None:
    client = SpeechClient(base_url=fake_server, offline_ok=False)
    result = client.transcribe(_wav_bytes(), mime_type="audio/wav")
    assert result["text"] == "good dog"
    assert result["confidence"] == 0.9
    client.close()


def test_offline_fallback_synthesize_silent_wav() -> None:
    client = SpeechClient(base_url="http://127.0.0.1:1", timeout=0.5)
    audio = client.synthesize("hello")
    assert len(audio) > 0
    with wave.open(BytesIO(audio), "rb") as wf:
        assert wf.getframerate() == 16000
    client.close()


def test_offline_fallback_transcribe_empty() -> None:
    client = SpeechClient(base_url="http://127.0.0.1:1", timeout=0.5)
    result = client.transcribe(_wav_bytes())
    assert result["text"] == ""
    assert result["provider"] == "offline"
    client.close()


def test_offline_raises_when_not_ok() -> None:
    client = SpeechClient(base_url="http://127.0.0.1:1", timeout=0.5, offline_ok=False)
    with pytest.raises(Exception):
        client.synthesize("hello")
    client.close()
