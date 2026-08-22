# Aarflingo hardware

KiCad lives **in this repo**. There is no sibling launcher, no Exovra clone, and `./setup.sh` stays the software installer.

```bash
./kicad-launcher                 # tool status + next steps
./kicad-launcher --run collar    # open the dog-worn puck
./kicad-launcher --sch verify    # GPIO + ethics + required parts
```

Rev-A is a **collar / harness puck on the dog**: ESP32-S3, BMI270, INMP441, LiPo. No shock, vibe, or door solenoid on this board.

- Product (flash + pair): [docs/COLLAR_PRODUCT.md](../docs/COLLAR_PRODUCT.md)
- Stuffing BOM: [collar-reva/BOM.md](collar-reva/BOM.md)
- Hardware spec: [collar-reva/DESIGN_SPEC.md](collar-reva/DESIGN_SPEC.md)
- Derived EE math: [collar-reva/AFE_CALCULATIONS.md](collar-reva/AFE_CALCULATIONS.md)
- Sampling / energy model: [collar-reva/MATH.md](collar-reva/MATH.md)
- Firmware contract: [docs/FIRMWARE_COLLAR.md](../docs/FIRMWARE_COLLAR.md)
