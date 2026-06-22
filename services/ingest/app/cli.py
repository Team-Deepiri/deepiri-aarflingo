"""Typer CLI for ingest service."""
from __future__ import annotations

import json
from pathlib import Path

import typer

from app.baseline import record_baseline
from app.capture import capture_frames
from app.clipper import clip_around_trigger

app = typer.Typer(help="AARFLingo ingest CLI")


@app.command()
def capture(out: Path = typer.Option(Path("data/clips/last.json"), help="Output JSON")) -> None:
    frames = capture_frames()
    trigger = frames[len(frames) // 2].ts_ms
    clip = clip_around_trigger(frames, trigger)
    payload = {
        "start_ms": clip.start_ms,
        "end_ms": clip.end_ms,
        "frame_count": len(clip.frames),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    typer.echo(f"wrote {out}")


@app.command()
def baseline(dog_id: str, hr: float = 80.0, tail: float = 35.0) -> None:
    b = record_baseline(dog_id, hr, tail)
    typer.echo(b.to_json())


if __name__ == "__main__":
    app()
