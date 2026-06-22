"""Flatten perception dict to model input vector."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.feature_spec import FEATURE_NAMES, vectorize  # noqa: E402

__all__ = ["FEATURE_NAMES", "vectorize"]
