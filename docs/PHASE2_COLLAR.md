# Phase 2 Collar Integration

## Goal

Stream low-rate triad predictions from a wearable IMU + mic puck to aarf-pocket via BLE.

## Contract

- 1 Hz intent/emotion summary frames (CBOR)
- Clip upload on trigger (Wi-Fi)
- Baseline sync from `record-baseline.sh` output

## Safety

- No shock/vibrate actuation in v0
- Human-in-the-loop for any welfare alert
