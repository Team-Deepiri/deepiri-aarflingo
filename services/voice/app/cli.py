"""Typer CLI for the voice interface (deepiri-speech engine)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

import typer

from .dog_voice import DogVoice
from .loader import load_service
from .speech_client import SpeechClient, speech_base_url

app = typer.Typer(help="AARFLingo voice — talk to and listen to your dog")


def _client() -> SpeechClient:
    return SpeechClient(base_url=speech_base_url())


def _save(audio: bytes, out: str | None) -> Path | None:
    if not audio:
        return None
    path = Path(out) if out else Path.cwd() / "aarflingo-speech.wav"
    path.write_bytes(audio)
    return path


def _play_file(path: Path) -> None:
    """Play via aplay (Linux) — best effort, no-op when unavailable."""
    for player in ("aplay", "paplay"):
        if subprocess.run([player, "-q", str(path)], capture_output=True).returncode == 0:
            return
    typer.echo(f"audio written to {path} (no player available)")


def _bark_classify(audio_path: Path) -> tuple[str, str]:
    """Classify a bark wav into (arousal, valence) using the vocal encoder."""
    import torch

    audio = load_service("audio", "train")
    synth = load_service("audio", "synth")
    from .wav import read_wav

    waveform = read_wav(audio_path)
    model = audio.VocalEncoder()
    ckpt = audio.default_checkpoint()
    if ckpt.exists():
        model.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=True))
    model.eval()
    with torch.no_grad():
        a_logits, v_logits = model(audio._feature_tensor(waveform).unsqueeze(0))
        ai = int(a_logits.argmax())
        vi = int(v_logits.argmax())
    return synth.AROUSAL_LEVELS[ai], synth.VALENCE_LEVELS[vi]


@app.command("status")
def status() -> None:
    health = _client().health()
    typer.echo(
        json.dumps(
            {
                "speech_url": speech_base_url(),
                "ok": health.ok,
                "latency_ms": health.latency_ms,
                "detail": health.detail,
            },
            indent=2,
        )
    )


@app.command("speak")
def speak(
    text: str = typer.Option(..., help="Text for the speech engine to say"),
    voice: Optional[str] = typer.Option(None, help="Optional voice id"),
    out: Optional[str] = typer.Option(None, help="Save audio to this path"),
    play: bool = typer.Option(False, help="Play the audio after synthesis"),
) -> None:
    audio = _client().synthesize(text, voice=voice)
    path = _save(audio, out)
    typer.echo(json.dumps({"chars": len(text), "audio_bytes": len(audio), "saved": str(path) if path else None}))
    if play and path:
        _play_file(path)


@app.command("listen")
def listen(
    audio: str = typer.Option(..., help="Path to a bark wav"),
    voice: Optional[str] = typer.Option(None, help="Optional voice id"),
    speak_back: bool = typer.Option(True, help="Speak a response to the bark"),
    out: Optional[str] = typer.Option(None, help="Save the spoken response"),
) -> None:
    arousal, valence = _bark_classify(Path(audio))
    typer.echo(json.dumps({"arousal": arousal, "valence": valence}, indent=2))
    if not speak_back:
        return
    dv = DogVoice(_client())
    response = dv.respond_to_bark(arousal, valence, voice=voice, force=True)
    path = _save(response, out)
    typer.echo(json.dumps({"phrase": dv.last_phrase, "audio_bytes": len(response or b""), "saved": str(path) if path else None}))


@app.command("respond")
def respond(
    frames: int = typer.Option(120, help="Frames to watch before giving up"),
    camera: int = typer.Option(0, help="Camera index"),
    voice: Optional[str] = typer.Option(None, help="Optional voice id"),
) -> None:
    """Watch the camera; speak whenever the dog's predicted intent changes."""
    import cv2

    perception = load_service("perception", "pipeline")
    forecast = load_service("forecast", "triad_model")

    cap = cv2.VideoCapture(camera)
    if not cap.isOpened():
        raise typer.Exit("cannot open camera")
    dv = DogVoice(_client(), cooldown_s=8.0)
    last_key: tuple[str, str, str] | None = None
    try:
        for _ in range(frames):
            ok, frame = cap.read()
            if not ok:
                break
            features = perception.run_pipeline_frame(frame)
            if float(features.get("dog_present", 0)) < 0.5:
                continue
            pred = forecast.heuristic_predict(features)
            key = (pred.intent_id, pred.emotion_id, pred.behavior_id)
            if key != last_key:
                audio = dv.respond_to_prediction(pred, voice=voice, force=True)
                typer.echo(
                    json.dumps(
                        {
                            "intent": pred.intent_id,
                            "emotion": pred.emotion_id,
                            "behavior": pred.behavior_id,
                            "phrase": dv.last_phrase,
                            "audio_bytes": len(audio or b""),
                        }
                    )
                )
                last_key = key
    finally:
        cap.release()


@app.command("play")
def play(file: str = typer.Option(..., help="Audio file to play")) -> None:
    _play_file(Path(file))


if __name__ == "__main__":
    app()
