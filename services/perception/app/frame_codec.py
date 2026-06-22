"""BGR frame utilities."""
from __future__ import annotations

import numpy as np


def bytes_to_bgr(data: bytes, width: int, height: int) -> np.ndarray | None:
    expected = width * height * 3
    if len(data) < expected:
        return None
    arr = np.frombuffer(data[:expected], dtype=np.uint8).reshape((height, width, 3))
    return arr.copy()


def bgr_from_jpeg(jpeg_bytes: bytes) -> np.ndarray | None:
    try:
        import cv2
    except ImportError:
        return None
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


def resize_for_model(frame: np.ndarray, size: int = 224) -> np.ndarray:
    import cv2

    return cv2.resize(frame, (size, size), interpolation=cv2.INTER_AREA)
