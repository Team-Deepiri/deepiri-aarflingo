# Aarflingo Collar Rev-A — product

Observational puck on the dog. Streams IMU, mic, neck PPG, and battery to aarf-pocket over BLE. **No shock, vibe, motor, or door strike.**

Firmware `0.2.0`. Advertises `aarf-collar`.

## What you get

| Piece | Status |
|-------|--------|
| Schematic + GPIO contract | Done — D4 PD, D5 660 nm, RT1 neck NTC, USB-C CC |
| Firmware (ESP32-S3) | Done — BLE 1 Hz CBOR, I2S, I2C, CLIP to `/infer/audio` |
| Pocket iOS / Android | Done — Settings → Listen to collar |
| Laptop listener | Done — `python3 scripts/collar_listen.py` |
| Footprints / BOM | Done — `./kicad-launcher --sch bom` |
| PCB layout / fab | 40×32 mm outline, parts placed, copper unrouted |
| Enclosure / strap | Not designed. NFC tag + 180 mAh cell are in the BOM. |

## Flash

```bash
./scripts/flash_collar.sh          # tests + PlatformIO upload
# or
cd firmware/collar && pio run -t upload
```

Serial 115200 should print `aarf-collar rev-A fw 0.2.0` and any I2C hits (`0x68` IMU, `0x58` PPG).

## Pair

1. Charge via USB-C (100 mA default PROG).
2. Phone: Settings → **Listen to collar**. Allow Bluetooth.
3. Or laptop: `pip install bleak && python3 scripts/collar_listen.py`
4. You should see 1 Hz JSON with `hr_bpm`, `rr_bpm`, `still`, `pant`, `arousal`, `skin_c`, `puck_c`, `gyro`, `vbat_v`, `fault`.

Dog-state (ethogram + autonomic proxies, not blood work): [DOG_STATE.md](DOG_STATE.md).

Optional Wi-Fi CLIP (bark → existing runtime): NVS `collar` keys `wifi_ssid`, `wifi_pass`, `runtime` (e.g. `http://192.168.1.10:8000`).

## Build (after layout + fab)

1. Buy [hardware/collar-reva/BOM.csv](../hardware/collar-reva/BOM.csv). Stuff R1 = 10 kΩ.
2. Optical window toward the ventral neck: D3 IR + D5 red out, D4 PD in. RT1 on the skin face.
3. `./scripts/flash_collar.sh` then pair as above.
4. First USB-C from a C-to-C cable needs R9/R10 stuffed or VBUS will not appear.

## Ethics

The GATT map is notify-only. Pocket clients do not write actuation characteristics. `aarf_sch` and firmware tests fail if SHOCK/VIBE/SOLENOID appear.

## Not this Rev

OTA, deep sleep, on-puck YOLO, wet ECG, Bosch BMI270 config blob, auto-open gate.
