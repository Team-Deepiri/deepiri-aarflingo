# Collar firmware (Rev-A)

Who: firmware for the **physical puck on the dog** (`hardware/collar-reva/`). Why: stream IMU + mic summaries to aarf-pocket without putting actuation on the animal.

This document is the firmware contract. Pin numbers come from `scripts/aarf_sch/nets.py` via `hardware/collar-reva/pins.h`. Do not fork a second map.

KiCad: `./kicad-launcher --run collar`. Electrical math: [hardware/collar-reva/AFE_CALCULATIONS.md](../hardware/collar-reva/AFE_CALCULATIONS.md). Sampling math: [hardware/collar-reva/MATH.md](../hardware/collar-reva/MATH.md). Product freeze: [PHASE2_COLLAR.md](PHASE2_COLLAR.md).

## Target

| Item | Value |
|------|--------|
| Module | ESP32-S3-MINI-1 |
| Framework (Rev-A) | ESP-IDF or Arduino+NimBLE — pick one in the first firmware PR; do not mix |
| Sensors | BMI270 (I2C), INMP441 (I2S) |
| Radio | BLE notify 1 Hz; Wi-Fi only for triggered clip upload |
| Actuation | **None** |

## Pin map

Include `hardware/collar-reva/pins.h`. Live buses:

| Pin macro | GPIO | Peripheral |
|-----------|------|------------|
| `PIN_VBAT_SENSE` | 1 | ADC1_CH0 |
| `PIN_CHG_STAT` | 2 | input, pull-up |
| `PIN_SDA` | 4 | I2C |
| `PIN_SCL` | 5 | I2C |
| `PIN_LED_STAT` | 6 | output, sink LED |
| `PIN_I2S_SCK` | 7 | I2S BCLK |
| `PIN_I2S_WS` | 15 | I2S WS |
| `PIN_I2S_SD` | 16 | I2S DIN |
| `PIN_IMU_INT` | 17 | BMI270 INT1 |

USB-JTAG is GPIO19/20 (not in `pins.h` live list). GPIO0 is boot. Never drive GPIO 0/3/45/46 as a bus.

I2C pull-ups are **on the PCB** (4.7 kΩ). Do not also enable fat internal pulls.

## Bring-up order

1. USB 100 mA current limit. 3V3 in range. STAT behaves with a cell.
2. Flash via USB-JTAG. Serial 115200.
3. I2C scan — BMI270 at 0x68 (typical, SA0 low). Treat NAK as `imu_fault`.
4. IMU 100 Hz burst → RMS/peak on serial.
5. I2S clap → audio RMS on serial.
6. ADC1 VBAT vs DMM at three voltages; store a two-point cal in NVS.
7. BLE advertise; phone sees 1 Hz notify.
8. Only then: Wi-Fi clip path.

Do not enable Wi-Fi and ADC2. VBAT stays on ADC1.

## State machine

```
IDLE → SAMPLE → TRANSMIT → IDLE
                 ↘ CLIP (rare, Wi-Fi) → IDLE
```

SLEEP is a Rev-B stub (no 32 kHz crystal on Rev-A; GPIO15/16 are I2S).

| State | Work | Time budget |
|-------|------|-------------|
| SAMPLE | Drain IMU FIFO (100 Hz), I2S hop, VBAT average N=16 | < 200 ms |
| TRANSMIT | CBOR encode, NimBLE notify | < 50 ms |
| CLIP | Only if bark/trigger **and** Wi-Fi associated; then back | seconds, watchdog fed |

Arm a task watchdog **longer than the slowest legal CLIP**, and pet it on every loop path. No blocking `delay` that can exceed the WDT.

ISRs: IMU INT1 sets a flag only. I2S via DMA. Encode and BLE in the main task.

## BLE / CBOR contract (do not invent a fourth protocol)

Phase 2 already specified this. Collar firmware **extends** it; it does not replace JSON runtime frames or triad-spec JSON.

**1 Hz notify** (CBOR map, keys stable):

```
{
  "v": 1,
  "ts_ms": <u32 boot-relative or UTC if synced>,
  "intent_id": <str, optional on-puck model>,
  "emotion_id": <str, optional>,
  "behavior_id": <str, optional>,
  "confidence": <float 0..1>,
  "imu_rms": <float g>,
  "imu_peak": <float g>,
  "audio_rms": <float>,
  "bark": <bool>,
  "vbat_v": <float>,
  "fault": <str or null>   // "imu" | "mic" | "vbat" | null
}
```

If on-puck TriadNet is absent (Rev-A default), omit intent/emotion/behavior or send `"source": "sensors"` and let aarf-pocket/runtime fuse. When present, `intent_id` / `emotion_id` / `behavior_id` / `confidence` must be valid against `core/triad-spec/prediction.json` ranges (`confidence` ∈ [0,1]).

**MTU:** call `NimBLEDevice::setMTU(247)` (or IDF equivalent) after init. Serialized CBOR must fit in `(negotiated_MTU − 3)` or fragment. Default 23-byte MTU **will truncate**.

**Clip upload (Wi-Fi, on trigger):** HTTP POST of a short WAV/Opus clip to the runtime ingest URL already used by studio. Same host config as aarf-pocket. Not a new binary framing.

Baseline sync: pull `record-baseline.sh` output over BLE or Wi-Fi as already described in PHASE2 — add a command byte to this CBOR map later (`"cmd": "baseline"`), do not stand up a parallel ASCII protocol.

## Faults

| Condition | Emit | LED |
|-----------|------|-----|
| IMU NAK | `fault=imu`, keep advertising | slow blink |
| I2S timeout | `fault=mic` | slow blink |
| \(V_{BAT}<3.1\ \mathrm{V}\) (after cal) | `fault=vbat` | solid dim |
| Healthy 1 Hz | `fault=null` | 10 ms tick |

Never encode a door-open or stim command. If a future GATT char looks like actuation, it is a spec bug.

## Calibration

`vbat_v = 2 * V_adc_raw * scale + offset` with `scale, offset` from NVS, default `scale=1, offset=0`. Fit against a DMM at three points. Do not compare floats with `==`; empty/full thresholds use hysteresis (e.g. empty 3.20 V, recover 3.35 V).

IMU features in **g**, not LSB. Convert with the BMI270 full-scale setting actually programmed.

## Tests (host, no hardware)

- CBOR round-trip: encode a max-size frame, decode, keys match, `confidence` in [0,1], payload ≤ 200 bytes.
- `pins.h` GPIO numbers equal `scripts/aarf_sch/nets.py` (`aarf_sch verify` already does this).
- Denylist: firmware source must not reference SHOCK/VIBE/SOLENOID drivers.

## Out of scope (Rev-A)

OTA, deep sleep, on-puck YOLO, gate MOSFET, ECG analog front-end, 32 kHz RTC crystal.
