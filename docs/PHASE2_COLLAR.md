# Phase 2 Collar Integration

## Goal

Stream low-rate triad predictions from a **physical device on the dog** (collar / harness puck: IMU + mic + neck PPG) to aarf-pocket via BLE.

KiCad: `./kicad-launcher --run collar`. Verify: `./kicad-launcher --sch verify`.

| Doc | Role |
|-----|------|
| [hardware/collar-reva/DESIGN_SPEC.md](../hardware/collar-reva/DESIGN_SPEC.md) | Topology, GPIO, floorplan |
| [hardware/collar-reva/AFE_CALCULATIONS.md](../hardware/collar-reva/AFE_CALCULATIONS.md) | Derived passives / ADC / PDN |
| [hardware/collar-reva/MATH.md](../hardware/collar-reva/MATH.md) | Energy and sampling model |
| [FIRMWARE_COLLAR.md](FIRMWARE_COLLAR.md) | State machine, BLE/CBOR, bring-up |

## Contract

- 1 Hz intent/emotion summary frames (CBOR)
- Clip upload on trigger (Wi-Fi)
- Baseline sync from `record-baseline.sh` output
- GPIO source of truth: `scripts/aarf_sch/nets.py` ↔ `hardware/collar-reva/pins.h`

## Safety

- No shock/vibrate actuation in v0
- Human-in-the-loop for any welfare alert
- Collar board has no solenoid / motor / haptic nets (`aarf_sch` denylist)
