# Collar Rev-A BOM (stuffed default)

Charge current: **RPROG = 10 kΩ → 100 mA**. Schematic pad allows 2 kΩ (500 mA) — do not stuff that on a ~180 mAh pouch. See [AFE_CALCULATIONS.md](AFE_CALCULATIONS.md).

| Ref | Value / MPN | Role |
|-----|-------------|------|
| J1 | USB-C receptacle | Charge / USB-JTAG |
| D1 | USBLC6-2SC6 (or equiv. USB TVS) | USB ESD |
| F1 | 500 mA PTC | USB inrush |
| U2 | MCP73831 | LiPo charge |
| RPROG | **10 kΩ** | 100 mA charge |
| J2 | JST-PH 2 | LiPo |
| U3 | AP2112K-3.3 | 3V3 LDO |
| Rdiv | 100 kΩ / 100 kΩ | VBAT → ADC1 |
| Caa | 100 nF | VBAT anti-alias |
| U1 | ESP32-S3-MINI-1 | MCU + BLE |
| U4 | BMI270 | IMU I2C 0x68 |
| U5 | INMP441 | I2S mic |
| U6 | TI AFE4404 | Neck PPG I2C 0x58 |
| D3 | IR LED (940 nm) | PPG emitter toward ventral neck |
| R7, R8 | 4.7 kΩ | I2C pull-ups to 3V3 |
| R6 | 330 Ω | STAT LED |
| D2 | LED | Status |
| — | Passive NFC/RFID tag | Enclosure only, not a net |
| BT1 | LiPo ~180 mAh pouch | Field cell |

Footprints are unassigned until layout. Open `./kicad-launcher --run collar`.
