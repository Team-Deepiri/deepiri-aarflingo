from app.capture import capture_frames
from app.clipper import clip_around_trigger


def test_clip_selects_window() -> None:
    frames = capture_frames(count=30, interval_ms=100)
    trigger = frames[15].ts_ms
    clip = clip_around_trigger(frames, trigger, pre_roll_ms=200, clip_ms=500)
    assert clip.frames
    assert clip.start_ms <= clip.frames[0].ts_ms
    assert clip.frames[-1].ts_ms <= clip.end_ms
