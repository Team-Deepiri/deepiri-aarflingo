"""Edge CLI."""
from __future__ import annotations

import typer

from app.loop import run_edge

app = typer.Typer(help="AARFLingo edge / Jetson runtime")


@app.command()
def run(camera: str = "0", onnx: bool = True) -> None:
    cam: str | int = int(camera) if camera.isdigit() else camera
    run_edge(cam, use_onnx=onnx)


if __name__ == "__main__":
    app()
