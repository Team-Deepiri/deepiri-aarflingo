# Collar dog-state layer (Rev-A)

A neck puck cannot assay blood. It **can** read the same autonomic and kinematic correlates veterinary behavior papers use as the chemistry of arousal: heart rate, RMSSD, panting, freeze vs motion, shake-off, and (when still) a respiratory estimate from IR baseline wander.

Firmware: `firmware/collar/src/dog_state.c`. Same 1 Hz CBOR map — new keys, not a new protocol.

## What the neck can see

| Signal | Sensor | Ethogram / physiology | Honest limit |
|--------|--------|------------------------|--------------|
| `still` | IMU dyn + peak | Freeze / rest. HR is only trustworthy when still. | Not “lying vs sitting” |
| `shake` | IMU peak > 2.6 g | Wet-dog / stress shake-off | Threshold, not a classifier |
| `pitch` | Mean accel tilt | Head/neck inclination | Uncalibrated until mount NVS |
| `pant` | Mic ZCR + RMS, not bark | Stress or heat pant (PetMD / ethogram) | Cannot tell heat from fear |
| `hr_bpm` / `rmssd_ms` | Neck PPG | Arousal ↑ HR, ↓ RMSSD (Katayama et al.; Frontiers 2022) | Fur kills optical SNR; `ppg_ok` gates it |
| `rr_bpm` | IR wander while `still` | Resting respiratory rate (collar SCG/PPG literature) | 0 when moving |
| `pi` | IR AC/DC | Perfusion / contact quality | Not SpO2 (need a second LED) |
| `arousal` | Fusion 0..1 | High HR + low RMSSD + pant/bark + motion | **Not valence.** Play and fear both raise it. |
| `gyro` | BMI270 °/s RMS | Shake-off / roll / head snap | Needs the Bosch config blob for full noise floor |
| `puck_c` | BMI270 die | Package self-heat | Not ambient, not skin |
| `skin_c` | Neck 10 kΩ NTC | Contact temperature | Not core / cortisol. Fur and air gap dominate |

## What this is not

Cortisol, glucose, “happy vs sad,” tail set, ear set, whale eye. Those need blood, a camera, or a human. Do not print them on the dash.

## Sources (read, not copied)

- Katayama et al. / related short-term canine HRV vs behavior (rest vs play vs pant vs sniff).
- Frontiers in Veterinary Science (2022): handler–dog cardiac + ethogram (freeze, pant, shake, vocal).
- Sci Rep (2024): HR and RMSSD track arousal more than valence.
- Neck IMU respiratory/HR reconstruction at rest (ACM / AI-COLLAR-style SCG) — we only emit RR when `still`.

## Firmware contract

Keys live on the existing notify map (`docs/FIRMWARE_COLLAR.md`). Pocket decodes `still`, `pant`, `rr_bpm`, `arousal`, `skin_c`, `puck_c`, `gyro`. No writable GATT.
