"""Collar CBOR → triad modality. Written first."""

from __future__ import annotations

import pytest


def test_collar_frame_fills_existing_physio_slots() -> None:
    from core.collar_features import collar_to_modality
    from core.modality_spec import MODALITY_NAMES

    mod = collar_to_modality(
        {
            "hr_bpm": 90,
            "rmssd_ms": 45,
            "imu_rms": 0.4,
            "still": False,
            "arousal": 0.6,
            "bark": False,
        }
    )
    assert set(mod) <= set(MODALITY_NAMES)
    assert "audio_arousal" not in mod
    assert mod["ecg_hr_norm"] == pytest.approx(90 / 180.0)
    assert mod["ecg_rmssd_norm"] == pytest.approx(45 / 150.0)
    assert mod["ecg_stress"] == pytest.approx(0.6)
    assert mod["imu_activity"] == pytest.approx(0.4)
    assert mod["imu_posture_static"] == 0.0


def test_collar_still_sets_posture_and_clamps() -> None:
    from core.collar_features import collar_to_modality

    mod = collar_to_modality({"hr_bpm": 400, "still": True, "imu_rms": 3.0, "arousal": 2.0})
    assert mod["ecg_hr_norm"] == 1.0
    assert mod["imu_activity"] == 1.0
    assert mod["ecg_stress"] == 1.0
    assert mod["imu_posture_static"] == 1.0


def test_empty_collar_is_zeros() -> None:
    from core.collar_features import collar_to_modality

    mod = collar_to_modality({})
    assert mod["ecg_hr_norm"] == 0.0
    assert mod["imu_posture_static"] == 0.0


def test_fresh_collar_file_merges_physio(tmp_path) -> None:
    from core.collar_features import merge_live_collar, write_collar_latest

    write_collar_latest(tmp_path, {"hr_bpm": 90, "still": True, "imu_rms": 0.2}, recv_ts=100.0)
    feats = merge_live_collar(tmp_path, {"audio_arousal": 0.4}, now=101.0)
    assert feats["ecg_hr_norm"] == pytest.approx(0.5)
    assert feats["imu_posture_static"] == 1.0
    assert feats["audio_arousal"] == 0.4


def test_stale_collar_file_is_ignored(tmp_path) -> None:
    from core.collar_features import merge_live_collar, write_collar_latest

    write_collar_latest(tmp_path, {"hr_bpm": 90}, recv_ts=100.0)
    feats = merge_live_collar(tmp_path, {}, now=110.0)
    assert "ecg_hr_norm" not in feats
