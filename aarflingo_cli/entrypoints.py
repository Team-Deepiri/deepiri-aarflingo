"""Console-script shims — each service uses a top-level `app` package on PYTHONPATH."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_app_cli(*path_parts: str) -> None:
    service_dir = ROOT.joinpath(*path_parts)
    sys.path[:0] = [str(ROOT), str(service_dir)]
    from app.cli import app

    app()


def _run_physio_cli() -> None:
    physio_dir = ROOT / "lib" / "aarf-physio"
    sys.path[:0] = [str(physio_dir)]
    from aarf_physio.cli import app

    app()


def runtime() -> None:
    _run_app_cli("services", "runtime")


def perception() -> None:
    _run_app_cli("services", "perception")


def ingest() -> None:
    _run_app_cli("services", "ingest")


def labeler() -> None:
    _run_app_cli("services", "labeler")


def forecast() -> None:
    _run_app_cli("services", "forecast")


def artifact_bridge() -> None:
    _run_app_cli("services", "artifact-bridge")


def feedback() -> None:
    _run_app_cli("services", "feedback")


def edge() -> None:
    _run_app_cli("services", "edge-runtime")


def audio() -> None:
    _run_app_cli("services", "audio")


def physio() -> None:
    _run_physio_cli()
