from app.dog_detect import BBox
from app.gaze import gaze_aversion


def test_gaze_aversion_in_range() -> None:
    bbox = BBox(x=0.2, y=0.1, w=0.5, h=0.6, confidence=0.9)
    score = gaze_aversion(bbox)
    assert 0.0 <= score <= 1.0
