"""Ensure monorepo imports resolve."""
from __future__ import annotations

import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def setup_paths() -> Path:
    root = repo_root()
    for p in (
        root,
        root / "services" / "perception",
        root / "services" / "forecast",
        root / "services" / "feedback",
    ):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    return root
