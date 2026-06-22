from app.dog_detect import BBox
from app.gaze import gaze_aversion
from app.pose import estimate_pose


def test_gaze_aversion_in_range() -> None:
    bbox = BBox(x=0.2, y=0.1, w=0.5, h=0.6, confidence=0.9)
    pose = estimate_pose(bbox)
    score = gaze_aversion(pose)
    assert 0.0 <= score <= 1.0
