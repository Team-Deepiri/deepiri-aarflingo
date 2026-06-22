"""Feature vector helper for forecast service."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.feature_spec import FEATURE_DIM, SEQUENCE_LEN, vectorize  # noqa: E402

__all__ = ["FEATURE_DIM", "SEQUENCE_LEN", "vectorize"]
