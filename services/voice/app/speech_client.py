"""Thin client for the deepiri-speech engine (Team-Deepiri/deepiri-platform).

Deepiri-platform PR #302 ships `deepiri-speech` (FastAPI + Pipecat + LiveKit)
with HTTP batch endpoints:

    POST /v1/tts            text -> audio (audio/mpeg)
    POST /v1/stt            audio -> text (multipart)
    POST /v1/sessions       create a duplex session
    GET  /health            health incl. pipecat + livekit worker

AARFLingo talks to the engine so the system can *speak to* the dog and
*listen to* it. When the engine is unreachable the client degrades to a
local offline mode (silent WAV from `synthesize`, empty transcript) so the
product still runs in dev without the platform stack.
"""
from __future__ import annotations

import os
import time
import wave
from dataclasses import dataclass
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:5020"
DEFAULT_TIMEOUT = 8.0
SILENT_WAV_RATE = 16000
SILENT_WAV_SECONDS = 0.3


def speech_base_url() -> str:
    return os.environ.get("SPEECH_URL", DEFAULT_BASE_URL).rstrip("/")


@dataclass
class HealthResult:
    ok: bool
    detail: dict[str, Any] | None = None
    latency_ms: float = 0.0


def _silent_wav(seconds: float = SILENT_WAV_SECONDS, rate: int = SILENT_WAV_RATE) -> bytes:
    import io

    n_frames = int(rate * seconds)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b"\x00\x00" * n_frames)
    return buf.getvalue()


class SpeechClient:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        offline_ok: bool = True,
    ) -> None:
        self.base_url = (base_url or speech_base_url()).rstrip("/")
        self.timeout = timeout
        self.offline_ok = offline_ok
        self._http = httpx.Client(base_url=self.base_url, timeout=timeout)

    # ------------------------------------------------------------------ #
    # engine state
    # ------------------------------------------------------------------ #
    def health(self) -> HealthResult:
        started = time.monotonic()
        try:
            resp = self._http.get("/health")
            latency_ms = (time.monotonic() - started) * 1000.0
            ok = resp.status_code == 200
            detail = resp.json() if ok else {"http_status": resp.status_code}
            return HealthResult(ok=ok, detail=detail, latency_ms=round(latency_ms, 1))
        except httpx.HTTPError as exc:
            return HealthResult(ok=False, detail={"error": str(exc)})

    def create_session(self, user_id: str | None = None, room_name: str | None = None) -> dict:
        body: dict[str, str] = {}
        if user_id:
            body["user_id"] = user_id
        if room_name:
            body["room_name"] = room_name
        resp = self._http.post("/v1/sessions", json=body)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------ #
    # speak / listen
    # ------------------------------------------------------------------ #
    def synthesize(self, text: str, voice: str | None = None) -> bytes:
        """Text -> audio bytes. Returns a silent WAV when offline."""
        if not text.strip():
            return b""
        payload: dict[str, str] = {"text": text}
        if voice:
            payload["voice"] = voice
        try:
            resp = self._http.post("/v1/tts", json=payload)
            resp.raise_for_status()
            return resp.content
        except httpx.HTTPError:
            if self.offline_ok:
                return _silent_wav()
            raise

    def transcribe(self, audio: bytes, mime_type: str = "audio/wav") -> dict[str, Any]:
        """Audio -> transcript. Empty text when offline."""
        try:
            resp = self._http.post(
                "/v1/stt",
                files={"file": ("audio", audio, mime_type)},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError:
            if self.offline_ok:
                return {
                    "text": "",
                    "is_final": True,
                    "provider": "offline",
                    "model": "none",
                    "confidence": 0.0,
                }
            raise

    def close(self) -> None:
        self._http.close()
