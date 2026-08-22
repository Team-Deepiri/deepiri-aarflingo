# Phase 2 Collar Integration

## Goal

Stream low-rate triad predictions from a **physical device on the dog** (collar / harness puck: IMU + mic) to aarf-pocket via BLE.

KiCad for that puck lives in this repo: `hardware/collar-reva/`. Open it with `./kicad-launcher --run collar`. Schematic contract: `./kicad-launcher --sch verify`. Spec: [hardware/collar-reva/DESIGN_SPEC.md](../hardware/collar-reva/DESIGN_SPEC.md).

## Contract

- 1 Hz intent/emotion summary frames (CBOR)
- Clip upload on trigger (Wi-Fi)
- Baseline sync from `record-baseline.sh` output
- GPIO source of truth: `scripts/aarf_sch/nets.py` ↔ `hardware/collar-reva/pins.h`

## Safety

- No shock/vibrate actuation in v0
- Human-in-the-loop for any welfare alert
- Collar board has no solenoid / motor / haptic nets (`aarf_sch` denylist)
