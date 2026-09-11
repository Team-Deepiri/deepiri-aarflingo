"""Map aarf-collar CBOR onto the existing triad modality slots.

Does not add FEATURE_DIM. Does not invent a new wire protocol.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

COLLAR_LATEST = Path("artifacts/eval/collar_latest.json")
MAX_AGE_S = 3.0


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def collar_to_modality(frame: dict[str, Any]) -> dict[str, float]:
    hr = float(frame.get("hr_bpm") or 0)
    rmssd = float(frame.get("rmssd_ms") or 0)
    imu = float(frame.get("imu_rms") or 0)
    arousal = float(frame.get("arousal") or 0)
    still = bool(frame.get("still"))
    return {
        "ecg_hr_norm": _clamp01(hr / 180.0),
        "ecg_rmssd_norm": _clamp01(rmssd / 150.0),
        "ecg_stress": _clamp01(arousal),
        "imu_activity": _clamp01(imu),
        "imu_posture_static": 1.0 if still else 0.0,
    }


def write_collar_latest(root: Path, frame: dict[str, Any], recv_ts: float | None = None) -> Path:
    path = root / COLLAR_LATEST
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"recv_ts": recv_ts if recv_ts is not None else time.time(), "frame": frame}
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return path


def read_fresh_collar_modality(
    root: Path,
    now: float | None = None,
    max_age_s: float = MAX_AGE_S,
) -> dict[str, float]:
    path = root / COLLAR_LATEST
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    ts = float(data.get("recv_ts") or 0)
    if (now if now is not None else time.time()) - ts > max_age_s:
        return {}
    frame = data.get("frame") if isinstance(data.get("frame"), dict) else data
    return collar_to_modality(frame)


def merge_live_collar(root: Path, features: dict[str, Any], now: float | None = None) -> dict[str, Any]:
    mod = read_fresh_collar_modality(root, now)
    if mod:
        features.update(mod)
    return features
