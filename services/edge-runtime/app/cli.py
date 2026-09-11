"""Edge CLI."""
from __future__ import annotations

import json

import typer

from app.loop import repo_root, run_edge

app = typer.Typer(help="AARFLingo Jetson home-hub runtime (not the collar)")


@app.command()
def status() -> None:
    """Print hub readiness. No camera required."""
    root = repo_root()
    onnx = root / "artifacts" / "bundles" / "default" / "studio" / "triad.onnx"
    print(
        json.dumps(
            {
                "status": "edge_ready",
                "role": "jetson-hub",
                "wearable": False,
                "root": str(root),
                "onnx": onnx.is_file(),
            }
        )
    )


@app.command()
def run(
    camera: str = "0",
    onnx: bool = True,
    frames: int = typer.Option(0, help="Stop after N frames (0 = forever)"),
) -> None:
    cam: str | int = int(camera) if camera.isdigit() else camera
    run_edge(cam, use_onnx=onnx, max_frames=frames or None)


if __name__ == "__main__":
    app()
