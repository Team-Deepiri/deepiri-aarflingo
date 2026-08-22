# METHODS

Aarflingo predicts a triad — intent × emotion × behavior — from vision, audio, and physiology. This file is the protocol a reviewer can run. It is not a results claim.

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
- Optional: neck PPG / IMU / mic features fused in runtime when the collar is paired

## Ethics

Observational only. No shock, vibe, or door strike. See [ETHICS.md](../ETHICS.md).
