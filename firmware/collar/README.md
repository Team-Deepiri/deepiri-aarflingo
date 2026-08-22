# Collar firmware (Rev-A)

Arduino app for the ESP32-S3-MINI-1 puck. Contract: [docs/FIRMWARE_COLLAR.md](../../docs/FIRMWARE_COLLAR.md). Pins are generated from `scripts/aarf_sch/nets.py` into `include/pins.h` and `hardware/collar-reva/pins.h`.

Host tests (no board):

```bash
python3 -m pytest -q firmware/collar/test
```

Advertises **`aarf-collar`**. 1 Hz frames are **CBOR** on the notify characteristic (`6e400003-…`). GATT is notify-only — no writable actuation char.

Flash (PlatformIO):

```bash
make firmware          # host tests + pio compile
cd firmware/collar && pio run -t upload
```

Phone: scan for `aarf-collar`, subscribe to notify UUID `6e400003-b5a3-f393-e0a9-e50e24dcca9e`, decode CBOR. VBAT scale/offset live in NVS namespace `collar` keys `vbat_s` / `vbat_o`.

Bring-up order stays in the firmware contract. This tree has no actuator drivers.
