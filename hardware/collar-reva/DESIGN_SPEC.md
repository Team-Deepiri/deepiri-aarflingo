# Collar Rev-A design spec

Dog-worn observational puck (collar or harness). Not a human bracelet. Not a gate actuator.

| Doc | Role |
|-----|------|
| This file | Topology, GPIO, floorplan, bring-up |
| [AFE_CALCULATIONS.md](AFE_CALCULATIONS.md) | Derived passives, ADC, PDN, ESD |
| [MATH.md](MATH.md) | Sampling / energy model (invariants, Π groups, state) |
| [docs/FIRMWARE_COLLAR.md](../../docs/FIRMWARE_COLLAR.md) | State machine, BLE/CBOR, faults |
| `scripts/aarf_sch/nets.py` | Net/GPIO source of truth |

## Topology

```
USB-C  → TVS (USBLC6) → PTC 500 mA → MCP73831 → LiPo (JST-PH)
                                           │
                                         VBAT ── 100k/100k divider + 100 nF → GPIO1 (ADC1)
                                           │
                                      AP2112K-3.3 → 3V3 → ESP32-S3-MINI-1
                                                      ├─ I2C  BMI270 (SDA/SCL + INT1)
                                                      └─ I2S  INMP441 (SCK/WS/SD)
```

Passive 125 kHz / NFC tag rides in the enclosure for pet-door identity. It is not a PCB net.

## GPIO (source: `scripts/aarf_sch/nets.py`)

| Net | GPIO | Notes |
|-----|------|--------|
| VBAT_SENSE | 1 | ADC1_CH0. Divider 100k/100k: 4.2 V bat → 2.1 V at pin. Anti-alias 100 nF. |
| CHG_STAT | 2 | MCP73831 STAT, open-drain, MCU pull-up |
| SDA | 4 | I2C, 4.7 kΩ to 3V3 |
| SCL | 5 | I2C, 4.7 kΩ to 3V3 |
| LED_STAT | 6 | 330 Ω series LED, MCU sink |
| I2S_SCK | 7 | INMP441 BCLK |
| I2S_WS | 15 | INMP441 WS. Blocks 32.768 kHz crystal (Rev-B move). |
| I2S_SD | 16 | INMP441 SD |
| IMU_INT | 17 | BMI270 INT1 |
| USB_DN / USB_DP | 19 / 20 | USB-JTAG |
| GPIO0 | 0 | Boot button only. 10 kΩ to 3V3. Not a live bus. |

Do not put live buses on GPIO 0, 3, 45, 46.

## Power budget (order-of-magnitude)

| Mode | Draw | 180 mAh life |
|------|------|----------------|
| Deep idle (Rev-B) | ~50 µA | weeks |
| IMU 100 Hz + mic + BLE advertise | ~8–15 mA avg | ~12–20 h |
| BLE TX peak | ~150 mA | pulse; 10 µF + 0.1 µF at module |

LDO: AP2112K-3.3, 600 mA, 10 µF in / 10 µF out. Dropout is fine from 3.5–4.2 V LiPo.

Charger: MCP73831. Schematic pad allows 2 kΩ (500 mA). **BOM default RPROG = 10 kΩ → 100 mA** so a 180 mAh pouch is not charged at ~2.8 C. USB-C is charge + bring-up, not a field cable. Derivation: [AFE_CALCULATIONS.md](AFE_CALCULATIONS.md) §1.

## Floorplan

| Zone | Contents |
|------|----------|
| Dirty | USB-C, TVS, PTC, MCP73831, JST |
| Brain | ESP32-S3, 0.1 µF + 10 µF on 3V3, crystal is on-module |
| Clean | BMI270, INMP441, I2C pull-ups. Far from charger loop. |

## Ethics / safety

No motor, solenoid, haptic, or stimulator on this board. `aarf_sch verify` fails if those net names appear. Door hardware is a separate node and is not Rev-A.

## Bring-up

1. Continuity 3V3–GND > 1 kΩ before applying USB.
2. Current-limit USB to 100 mA. Charger STAT should toggle with battery present.
3. 3V3 within 3.2–3.4 V. Program via USB-JTAG.
4. I2C scan: BMI270 typically 0x68. INMP441 is I2S, not I2C.
