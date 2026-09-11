# METHODS

Aarflingo predicts a triad — intent × emotion × behavior — from vision, audio, and physiology. This file is the protocol a reviewer can run. It is not a results claim. The manuscript is [PAPER.md](PAPER.md) / [aarflingo.tex](aarflingo.tex).

## What counts as v1.0 accuracy

The only number that can satisfy the v1.0 bar is **dog-held-out** intent accuracy on a home set:

- ≥ 3 dogs
- splits by **dog id**, never by random frame
- labels from the ethogram in `ethogram/`
- rows in `data/dog/eval/dog_split.jsonl`
- scored by `python3 scripts/v1_gate.py --require-bar`

Target: accuracy ≥ 0.95 and macro-F1 reported beside it. Calibration (ECE) and coupling-corrected accuracy are required before submission; they are not in the gate yet.

## What does not count

- Triad `best_val_acc` on synthetic or mixed rows (the current manifest can read 1.0)
- Vocal acc on a mixed real/synth val set
- Breed top-1 on Stanford Dogs (public photos, not your living room)
- Collar proxies (`arousal`, `still`, `red`) — observational correlates, not intent labels

## Sensors

- Home hub: USB or MIPI camera on a Jetson Orin-class box (`infra/docker/jetson.Dockerfile`)
- Wearable: ESP32-S3 collar, BLE notify-only CBOR (`firmware/collar`). The Jetson image does not run on the puck.
- Wearable 1 Hz CBOR maps onto existing triad slots (no new FEATURE_DIM):
  `hr_bpm` → `ecg_hr_norm`, `rmssd_ms` → `ecg_rmssd_norm`, `arousal` → `ecg_stress`,
  `imu_rms` → `imu_activity`, `still` → `imu_posture_static`.
  Path: BLE notify → `scripts/collar_listen.py --runtime` → `POST /infer/collar`
  (same HTTP family as `/infer/audio`). The Jetson hub also reads
  `artifacts/eval/collar_latest.json` when the file is younger than 3 s.
- Optional eval field: `"collar": { ... }` on a `dog_split.jsonl` row. Camera-only rows stay valid.

## Ethics

Observational only. No shock, vibe, or door strike. See [ETHICS.md](../ETHICS.md).
