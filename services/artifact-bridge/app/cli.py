"""Typer CLI for artifact bridge."""
from __future__ import annotations

from pathlib import Path

import typer

from app.export_coreml import export_coreml
from app.export_onnx import export_onnx
from app.manifest import build_manifest

app = typer.Typer(help="AARFLingo artifact bridge CLI")


@app.command()
def export(
    out: Path = Path("artifacts/bundles/dev"),
    target: str = typer.Option("onnx", help="onnx or coreml"),
) -> None:
    if target == "coreml":
        path = export_coreml(out)
    else:
        path = export_onnx(out)
    manifest = build_manifest(out)
    (out / "manifest.json").write_text(manifest.to_json(), encoding="utf-8")
    typer.echo(f"exported {path}")


if __name__ == "__main__":
    app()
