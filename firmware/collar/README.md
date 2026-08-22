# Collar firmware (Rev-A)

Arduino app for the ESP32-S3-MINI-1 puck. Contract: [docs/FIRMWARE_COLLAR.md](../../docs/FIRMWARE_COLLAR.md). Pins are generated from `scripts/aarf_sch/nets.py` into `include/pins.h` and `hardware/collar-reva/pins.h`.

Host tests (no board):

```bash
python3 -m pytest -q firmware/collar/test
```

1 Hz frames are **CBOR** (Phase 2 keys), printed on Serial for bring-up. Decode with any CBOR tool; do not expect JSON.

Flash (PlatformIO):

```bash
cd firmware/collar && pio run -t upload
```

Bring-up order stays in the firmware contract. This tree has no actuator drivers.
