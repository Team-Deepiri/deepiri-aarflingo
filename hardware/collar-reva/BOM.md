# Collar Rev-A BOM (stuffed default)

Charge: **R1 = 10k → 100 mA**. Schematic pad allows 2 kΩ (500 mA) — do not stuff that on a ~180 mAh pouch. See [AFE_CALCULATIONS.md](AFE_CALCULATIONS.md).

Regenerate: `./kicad-launcher --sch bom` (writes this file and `BOM.csv`).

Footprints are assigned on the schematic (`./kicad-launcher --sch bom`). PCB copper is still outline-only.

| Qty | Ref | Value | MPN | Pkg | Footprint | Sheet | Role |
|----:|-----|-------|-----|-----|-----------|-------|------|
| 1 | U1 | ESP32-S3-MINI-1-N8 | ESP32-S3-MINI-1-N8 | module | RF_Module:ESP32-S3-MINI-1 | mcu | MCU + BLE + 8 MB flash |
| 1 | U2 | MCP73831 4.2 V | MCP73831T-2ACI/OT | SOT-23-5 | Package_TO_SOT_SMD:SOT-23-5 | power | LiPo charge |
| 1 | U3 | AP2112K-3.3 600 mA | AP2112K-3.3TRG1 | SOT-23-5 | Package_TO_SOT_SMD:SOT-23-5 | power | 3V3 LDO |
| 1 | U4 | BMI270 | BMI270 | LGA-14 2.5×3.0 | Sensor_Motion:Bosch_LGA-14_2.5x3mm_P0.5mm_ClockwisePinNumbering | sensors | IMU I2C 0x68 |
| 1 | U5 | INMP441 | INMP441 | LGA | Sensor_Audio:InvenSense_INMP441 | sensors | I2S mic |
| 1 | U6 | AFE4404 | AFE4404YZPR | DSBGA-15 | Package_BGA:Texas_DSBGA-15_1.91x1.91mm_Layout5x3_P0.4mm | sensors | Neck PPG I2C 0x58 |
| 1 | D1 | USBLC6-2SC6 | USBLC6-2SC6 | SOT-23-6 | Package_TO_SOT_SMD:SOT-23-6 | power | USB ESD on VBUS/D+/D− |
| 1 | D2 | Green LED | LTST-C190KGKT | 0402 | LED_SMD:LED_0402_1005Metric | mcu | STAT, MCU sink via R6 |
| 1 | D3 | 940 nm IR LED | SFH 4451 | SMD 0805-class | LED_SMD:LED_0805_2012Metric | sensors | PPG emitter toward ventral neck |
| 1 | D4 | 940 nm photodiode | SFH 2704 | SMD | Diode_SMD:D_0805_2012Metric | sensors | PPG detector |
| 1 | D5 | 660 nm red LED | LTST-C170KRKT | SMD 0805 | LED_SMD:LED_0805_2012Metric | sensors | AFE LED2 second wavelength |
| 1 | RT1 | 10k NTC β3950 | NCP15XH103F03RC | 0402 | Resistor_SMD:R_0402_1005Metric | sensors | Neck-contact skin temp |
| 1 | F1 | PTC 500 mA | MF-MSMF050-2 | 1812 | Fuse:Fuse_1812_4532Metric | power | USB inrush |
| 1 | J1 | USB-C receptacle | USB4105-GF-A | 16-pin SMD | Connector_USB:USB_C_Receptacle_USB4105-xx-A_16P_TopMnt_Horizontal | power | Charge + USB-JTAG D+/D− |
| 1 | J2 | JST-PH 2 | S2B-PH-SM4-TB | SMD 2.0 mm | Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal | power | LiPo |
| 1 | R1 | 10k | RC0402FR-0710KL | 0402 1% | Resistor_SMD:R_0402_1005Metric | power | PROG → 100 mA |
| 1 | R2 | 100k | RC0402FR-07100KL | 0402 1% | Resistor_SMD:R_0402_1005Metric | power | VBAT divider top |
| 1 | R3 | 100k | RC0402FR-07100KL | 0402 1% | Resistor_SMD:R_0402_1005Metric | power | VBAT divider bottom |
| 1 | R4 | 10k | RC0402FR-0710KL | 0402 1% | Resistor_SMD:R_0402_1005Metric | mcu | EN pull-up |
| 1 | R5 | 10k | RC0402FR-0710KL | 0402 1% | Resistor_SMD:R_0402_1005Metric | mcu | GPIO0 / BOOT pull-up |
| 1 | R6 | 330 | RC0402FR-07330RL | 0402 1% | Resistor_SMD:R_0402_1005Metric | mcu | STAT LED series |
| 1 | R7 | 4.7k | RC0402FR-074K7L | 0402 1% | Resistor_SMD:R_0402_1005Metric | sensors | I2C SDA pull-up |
| 1 | R8 | 4.7k | RC0402FR-074K7L | 0402 1% | Resistor_SMD:R_0402_1005Metric | sensors | I2C SCL pull-up |
| 1 | R9 | 5.1k | RC0402FR-075K1L | 0402 1% | Resistor_SMD:R_0402_1005Metric | power | USB-C CC1 pulldown |
| 1 | R10 | 5.1k | RC0402FR-075K1L | 0402 1% | Resistor_SMD:R_0402_1005Metric | power | USB-C CC2 pulldown |
| 1 | R11 | 10k | RC0402FR-0710KL | 0402 1% | Resistor_SMD:R_0402_1005Metric | sensors | NTC divider to 3V3 |
| 1 | C1 | 10uF 16V | CL21A106KOQNNNE | 0805 X5R | Capacitor_SMD:C_0805_2012Metric | power | LDO VIN |
| 1 | C2 | 10uF 16V | CL21A106KOQNNNE | 0805 X5R | Capacitor_SMD:C_0805_2012Metric | power | LDO VOUT |
| 1 | C3 | 100nF 16V | CC0402KRX7R7BB104 | 0402 X7R | Capacitor_SMD:C_0402_1005Metric | power | VBAT anti-alias |
| 1 | C4 | 100nF 16V | CC0402KRX7R7BB104 | 0402 X7R | Capacitor_SMD:C_0402_1005Metric | mcu | 3V3 HF at module |
| 1 | C5 | 10uF 16V | CL21A106KOQNNNE | 0805 X5R | Capacitor_SMD:C_0805_2012Metric | mcu | 3V3 bulk at module |
| 1 | C6 | 100nF 16V | CC0402KRX7R7BB104 | 0402 X7R | Capacitor_SMD:C_0402_1005Metric | sensors | BMI270 VDD |
| 1 | C7 | 100nF 16V | CC0402KRX7R7BB104 | 0402 X7R | Capacitor_SMD:C_0402_1005Metric | sensors | INMP441 VDD |
| 1 | C8 | 100nF 16V | CC0402KRX7R7BB104 | 0402 X7R | Capacitor_SMD:C_0402_1005Metric | sensors | AFE4404 VDD |
| 1 | BT1 | LiPo 3.7 V 180 mAh | pouch + PCM + PH | wired | — | mech | Field cell |
| 1 | TAG1 | NTAG213 disc | NTAG213 25 mm | sticker | — | mech | Pet-door identity |

## Notes

- D4 (photodiode), D5 (660 nm), RT1/R11 (neck NTC), and R9/R10 (USB-C CC) are on the sheets.
- Passives are 0402 / 0805 16 V ceramics. 10 µF on LDO and module per AFE §6.
- Observational only. If a line looks like actuation, it is a spec bug.
- Enclosure / collar strap / epoxy over the optical window are not in this PCB BOM.

## Line notes

- **U5:** TDK EOL — ICS-43434 is the I2S drop-in if INMP441 is N/A
- **U6:** Reflow; not a hand-solder first proto
- **D3:** U6 TXP. Keep If at the AFE 4 mA bring-up current
- **D4:** U6 INP, cathode to GND
- **D5:** Already programmed at 4 mA in LEDCNTRL. Not SpO2 until both paths are calibrated
- **RT1:** Divider with R11. Package β is ~3380 — firmware uses 3950 until NVS cal
- **J1:** CC1/CC2 pulldowns R9/R10 are on the power sheet
- **R1:** Do not stuff 2 kΩ on a ~180 mAh pouch (≈2.8 C)
- **R6:** 330 Ω → ~3.9 mA
- **BT1:** ≤1 C charge. Matches 100 mA PROG
- **TAG1:** Enclosure only — not a PCB net
