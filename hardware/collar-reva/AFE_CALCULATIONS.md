# Collar Rev-A analog / power calculations

Every passive on the power and sensor sheets is derived here. Firmware must not invent a different `RPROG`, divider, or anti-alias corner. Values match `scripts/aarf_sch/nets.py`.

## 1. Charge current (MCP73831)

Datasheet: \(I_{REG} = 1000 / R_{PROG}\) with \(R_{PROG}\) in kΩ and \(I_{REG}\) in mA… equivalently

\[
I_{REG}\ (\mathrm{A}) = \frac{1.0\ \mathrm{V}}{R_{PROG}}
\]

\(R_{PROG} = 2.00\ \mathrm{k}\Omega\) → \(I_{REG} = 0.50\ \mathrm{A}\).

USB-C bring-up is current-limited in the lab to 100 mA first; 500 mA is the *designed* charge rate once STAT is proven. Do not raise \(I_{REG}\) without checking the 180 mAh cell’s C-rate (0.5 A / 0.18 Ah ≈ 2.8 C — too hot for field use). **Rev-A lab:** keep a 10 kΩ PROG option (100 mA ≈ 0.56 C) as the default stuffed value if the cell is a small pouch.

Recommended stuffed default: **RPROG = 10 kΩ → 100 mA**. Schematic value 2 kΩ is the absolute max pad; BOM default is 10 kΩ.

## 2. VBAT divider → ADC1

Equal divider \(R_T = R_B = 100\ \mathrm{k}\Omega\):

\[
V_{ADC} = V_{BAT}\cdot\frac{R_B}{R_T + R_B} = \tfrac{1}{2} V_{BAT}
\]

| \(V_{BAT}\) | \(V_{ADC}\) | Notes |
|-------------|-------------|--------|
| 4.20 V (full) | 2.10 V | ESP32-S3 ADC1 11 dB atten ≈ 0–3.1 V; 1.0 V headroom |
| 3.70 V (nominal) | 1.85 V | mid-band |
| 3.30 V (LDO dropout region) | 1.65 V | still valid |
| 3.00 V (empty) | 1.50 V | cutoff in firmware, not at the pin |

Always-on divider current at 4.2 V: \(I_{div} = 4.2 / 200\mathrm{k} = 21\ \mu\mathrm{A}\). Over 24 h that is 0.50 mAh — 0.3 % of a 180 mAh cell. Acceptable; do not MOSFET-switch the divider on Rev-A.

**ADC2 is forbidden** (Wi-Fi). GPIO1 = ADC1_CH0.

ESP32-S3 ADC is nonlinear. Theoretical mapping \(V_{BAT} = 2 V_{ADC}\) is a starting point; **bench-calibrate against a DMM** at 3.5 V, 3.7 V, 4.1 V.

## 3. Anti-alias on VBAT_SENSE

Thevenin of the divider as seen by the cap: \(R_{th} = R_T \parallel R_B = 50\ \mathrm{k}\Omega\). \(C_f = 100\ \mathrm{nF}\):

\[
f_c = \frac{1}{2\pi R_{th} C_f} = \frac{1}{2\pi \cdot 5\cdot 10^{4} \cdot 10^{-7}} \approx 31.8\ \mathrm{Hz}
\]

Battery voltage is a slow state. Nyquist for a 10 Hz firmware sample is 5 Hz; 31.8 Hz still knocks down charger ripple and BLE TX droop before they alias. Oversample in firmware (N=16) and average.

12-bit ADC, 11 dB atten ≈ 3.1 V FS → LSB ≈ \(3.1 / 4095 \approx 0.76\ \mathrm{mV}\) at the pin → **1.5 mV at the cell**. That is finer than cell chemistry; noise, not LSB, sets the floor. Treat ±50 mV at the cell as the honest resolution until calibrated.

## 4. I2C pull-ups (BMI270)

\(R_p = 4.7\ \mathrm{k}\Omega\) to 3V3. Low-level current \(I_{OL} = 3.3 / 4.7\mathrm{k} \approx 0.70\ \mathrm{mA}\) (within BMI270 sink).

Rise time with 50 pF bus: \(\tau = R_p C \approx 235\ \mathrm{ns}\). Fast-mode 400 kHz allows ~300 ns to 0.7 VDD. 4.7 kΩ is the stiff-enough / quiet-enough middle. Do not go below 2.2 kΩ (wastes 1.5 mA) or above 10 kΩ (fails 400 kHz).

## 5. Status LED

MCU sink, \(R = 330\ \Omega\), green \(V_F \approx 2.0\ \mathrm{V}\):

\[
I_{LED} = \frac{3.3 - 2.0}{330} \approx 3.9\ \mathrm{mA}
\]

Duty-cycle in firmware if battery is the limit. GPIO6 is not a strapping pin on ESP32-S3.

## 6. LDO (AP2112K-3.3)

VIN = VBAT (3.0–4.2 V). Dropout of AP2112 at 200 mA is typically < 400 mV, so 3.3 V stays in regulation down to ~3.5 V VIN; below that the rail follows VIN and the MCU brownout detector is the authority.

Datasheet caps: **10 µF ceramic on VIN and VOUT**, plus **0.1 µF at the ESP32-S3 3V3 pin** (high-frequency, ≤ 2 mm).

BLE TX peak ~150 mA for ~1 ms. Charge from the 10 µF:

\[
\Delta V \approx \frac{I \Delta t}{C} = \frac{0.15 \times 10^{-3}}{10\times 10^{-6}} = 15\ \mathrm{mV}
\]

Plus the 10 µF at the module. Combined ~7 mV if they share the pulse. Fine. Keep the module cap’s loop tiny.

## 7. USB / ESD / fuse

Entry order (dirty zone, threat first):

`USB-C VBUS → USBLC6 (or SMBJ5.0A on VBUS) → PTC 500 mA → MCP73831 VDD`

CC1 and CC2 each have **5.1 kΩ to GND** (R9, R10) so a C-to-C cable presents VBUS. D+/D− go through the same USBLC6 to GPIO19/20 (USB-JTAG). Series 22–27 Ω on D+/D− if layout is long; skip if the TVS sits on the connector pads.

## 8. I2S mic (INMP441)

Digital PDM/I2S — **no analog AFE**. L/R pin tied to GND (left). VDD = 3V3 with 0.1 µF on the mic pads.

Rev-A sample rate: 16 kHz. Bit clock \(64 f_s = 1.024\ \mathrm{MHz}\). That is a digital edge rate, not an analog Nyquist problem. Keep I2S traces short and away from the charger.

## 9. IMU (BMI270) @ 100 Hz

Roadmap alignment: 100 Hz 6-DoF. Dog kinematics of interest (gait, shake, jump) sit below ~20 Hz. 100 Hz ODR → Nyquist 50 Hz, two-and-a-half times the band. INT1 → GPIO17, edge, not polled if we can avoid it.

I2C address typically 0x68 (SDO/SA0 low). Confirm on the first scan.

## 10. GPIO / strapping (ESP32-S3, not classic ESP32)

Live nets **must not** use GPIO 0, 3, 45, 46. GPIO0 is boot-only (10 kΩ to 3V3, button to GND).

Classic-ESP32 rules (GPIO2/5/12/15 strapping, GPIO6–11 flash) **do not apply** to ESP32-S3-MINI-1. I2S_WS on GPIO15 is legal here.

USB-JTAG is GPIO19 (D−) / GPIO20 (D+). Do not reuse.

## 11. Neck PPG (TI AFE4404)

Ventral-neck photoplethysmography. IR LED + photodiode look at carotid-adjacent tissue. Observational only — no stim, no current into the animal except the optical pulse.

AFE4404 I2C address `0x58`. Shares SDA/SCL with BMI270. `ADC_RDY` → GPIO8, `RESET` (active low) → GPIO9. Neither is an S3 strap.

LED current is programmed in the AFE, not a series resistor on the schematic. Average extra drain:

\[
I_{LED,avg} = I_{pulse}\cdot D
\]

Rev-A bring-up: \(I_{pulse} = 4\ \mathrm{mA}\), \(D = 0.25\) → \(1\ \mathrm{mA}\) average. At 180 mAh that is ~5 % of the IMU+mic budget. Do not stuff 50 mA pulses on a small pouch without measuring skin heating.

Photodiode current is nanoamps; the AFE integrates it. No extra ADC pin — do not put PPG on ADC2.

Firmware: 50 Hz IR FIFO → peak detect → `hr_bpm` and `rmssd_ms` (`firmware/collar/src/ppg_hr.c`).

## 12. What this board deliberately omits

| Omitted | Why | Cost of omission |
|---------|-----|------------------|
| 32.768 kHz crystal | GPIO15/16 are I2S on Rev-A | Deep-sleep RTC accuracy; Rev-B moves I2S |
| Fuel-gauge IC | Divider + ADC is enough | ~1 % SoC vs 5–10 % |
| Haptic / motor / solenoid | Ethics freeze | Cannot open a door from this PCB |
| MOSFET-gated divider | 21 µA is cheap | Extra FET + GPIO |

## Review checklist

- [x] Passives derived (this file)
- [x] Bias/ADC range with margin (2.10 V < 3.1 V FS)
- [x] Anti-alias \(f_c\) stated (31.8 Hz)
- [x] No S3 strapping on live nets; ADC1 only
- [x] I2C pull-ups specified
- [x] TVS + PTC at USB
- [x] Power budget: see [DESIGN_SPEC.md](DESIGN_SPEC.md) + [MATH.md](MATH.md)
- [x] Pin map = `nets.py` = `pins.h`
- [x] Calibration: DMM vs ADC at three cell voltages
- [x] Neck PPG AFE4404: I_LED,avg = 1 mA at 4 mA × 25 % duty
