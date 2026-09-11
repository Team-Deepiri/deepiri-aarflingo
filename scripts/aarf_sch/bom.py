"""Collar Rev-A stuffing BOM.

Source of truth for what to buy. Schematic refs must appear here.
R1 stuffed value is 10 kΩ (100 mA), not the 2 kΩ max pad on the sheet.
"""

from __future__ import annotations

from dataclasses import dataclass

from nets import LED_SERIES_OHMS


@dataclass(frozen=True)
class Line:
    refs: tuple[str, ...]
    qty: int
    value: str
    mpn: str
    pkg: str
    fp: str
    sheet: str
    role: str
    notes: str = ""


FP_R0402 = "Resistor_SMD:R_0402_1005Metric"
FP_C0402 = "Capacitor_SMD:C_0402_1005Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_LED0402 = "LED_SMD:LED_0402_1005Metric"
FP_LED0805 = "LED_SMD:LED_0805_2012Metric"
FP_D0805 = "Diode_SMD:D_0805_2012Metric"
FP_SOT235 = "Package_TO_SOT_SMD:SOT-23-5"
FP_SOT236 = "Package_TO_SOT_SMD:SOT-23-6"
FP_ESP = "RF_Module:ESP32-S3-MINI-1"
FP_USB = "Connector_USB:USB_C_Receptacle_USB4105-xx-A_16P_TopMnt_Horizontal"
FP_JST = "Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal"
FP_FUSE = "Fuse:Fuse_1812_4532Metric"
FP_BMI = "Sensor_Motion:Bosch_LGA-14_2.5x3mm_P0.5mm_ClockwisePinNumbering"
FP_MIC = "Sensor_Audio:InvenSense_INMP441"
FP_AFE = "Package_BGA:Texas_DSBGA-15_1.91x1.91mm_Layout5x3_P0.4mm"


# Stuffed default. Schematic R1 value text may still say 2k (max pad).
RPROG_STUFFED = "10k"
RPROG_STUFFED_MA = 100

LINES: tuple[Line, ...] = (
    Line(("U1",), 1, "ESP32-S3-MINI-1-N8", "ESP32-S3-MINI-1-N8", "module", FP_ESP, "mcu", "MCU + BLE + 8 MB flash"),
    Line(("U2",), 1, "MCP73831 4.2 V", "MCP73831T-2ACI/OT", "SOT-23-5", FP_SOT235, "power", "LiPo charge"),
    Line(("U3",), 1, "AP2112K-3.3 600 mA", "AP2112K-3.3TRG1", "SOT-23-5", FP_SOT235, "power", "3V3 LDO"),
    Line(("U4",), 1, "BMI270", "BMI270", "LGA-14 2.5×3.0", FP_BMI, "sensors", "IMU I2C 0x68"),
    Line(("U5",), 1, "INMP441", "INMP441", "LGA", FP_MIC, "sensors", "I2S mic", "TDK EOL — ICS-43434 is the I2S drop-in if INMP441 is N/A"),
    Line(("U6",), 1, "AFE4404", "AFE4404YZPR", "DSBGA-15", FP_AFE, "sensors", "Neck PPG I2C 0x58", "Reflow; not a hand-solder first proto"),
    Line(("D1",), 1, "USBLC6-2SC6", "USBLC6-2SC6", "SOT-23-6", FP_SOT236, "power", "USB ESD on VBUS/D+/D−"),
    Line(("D2",), 1, "Green LED", "LTST-C190KGKT", "0402", FP_LED0402, "mcu", "STAT, MCU sink via R6"),
    Line(("D3",), 1, "940 nm IR LED", "SFH 4451", "SMD 0805-class", FP_LED0805, "sensors", "PPG emitter toward ventral neck", "U6 TXP. Keep If at the AFE 4 mA bring-up current"),
    Line(("D4",), 1, "940 nm photodiode", "SFH 2704", "SMD", FP_D0805, "sensors", "PPG detector", "U6 INP, cathode to GND"),
    Line(("D5",), 1, "660 nm red LED", "LTST-C170KRKT", "SMD 0805", FP_LED0805, "sensors", "AFE LED2 second wavelength", "Already programmed at 4 mA in LEDCNTRL. Not SpO2 until both paths are calibrated"),
    Line(("RT1",), 1, "10k NTC β3950", "NCP15XH103F03RC", "0402", FP_R0402, "sensors", "Neck-contact skin temp", "Divider with R11. Package β is ~3380 — firmware uses 3950 until NVS cal"),
    Line(("F1",), 1, "PTC 500 mA", "MF-MSMF050-2", "1812", FP_FUSE, "power", "USB inrush"),
    Line(("J1",), 1, "USB-C receptacle", "USB4105-GF-A", "16-pin SMD", FP_USB, "power", "Charge + USB-JTAG D+/D−", "CC1/CC2 pulldowns R9/R10 are on the power sheet"),
    Line(("J2",), 1, "JST-PH 2", "S2B-PH-SM4-TB", "SMD 2.0 mm", FP_JST, "power", "LiPo"),
    Line(("R1",), 1, RPROG_STUFFED, "RC0402FR-0710KL", "0402 1%", FP_R0402, "power", f"PROG → {RPROG_STUFFED_MA} mA", "Do not stuff 2 kΩ on a ~180 mAh pouch (≈2.8 C)"),
    Line(("R2",), 1, "100k", "RC0402FR-07100KL", "0402 1%", FP_R0402, "power", "VBAT divider top"),
    Line(("R3",), 1, "100k", "RC0402FR-07100KL", "0402 1%", FP_R0402, "power", "VBAT divider bottom"),
    Line(("R4",), 1, "10k", "RC0402FR-0710KL", "0402 1%", FP_R0402, "mcu", "EN pull-up"),
    Line(("R5",), 1, "10k", "RC0402FR-0710KL", "0402 1%", FP_R0402, "mcu", "GPIO0 / BOOT pull-up"),
    Line(("R6",), 1, "330", "RC0402FR-07330RL", "0402 1%", FP_R0402, "mcu", "STAT LED series", f"{LED_SERIES_OHMS} Ω → ~3.9 mA"),
    Line(("R7",), 1, "4.7k", "RC0402FR-074K7L", "0402 1%", FP_R0402, "sensors", "I2C SDA pull-up"),
    Line(("R8",), 1, "4.7k", "RC0402FR-074K7L", "0402 1%", FP_R0402, "sensors", "I2C SCL pull-up"),
    Line(("R9",), 1, "5.1k", "RC0402FR-075K1L", "0402 1%", FP_R0402, "power", "USB-C CC1 pulldown"),
    Line(("R10",), 1, "5.1k", "RC0402FR-075K1L", "0402 1%", FP_R0402, "power", "USB-C CC2 pulldown"),
    Line(("R11",), 1, "10k", "RC0402FR-0710KL", "0402 1%", FP_R0402, "sensors", "NTC divider to 3V3"),
    Line(("C1",), 1, "10uF 16V", "CL21A106KOQNNNE", "0805 X5R", FP_C0805, "power", "LDO VIN"),
    Line(("C2",), 1, "10uF 16V", "CL21A106KOQNNNE", "0805 X5R", FP_C0805, "power", "LDO VOUT"),
    Line(("C3",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", FP_C0402, "power", "VBAT anti-alias"),
    Line(("C4",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", FP_C0402, "mcu", "3V3 HF at module"),
    Line(("C5",), 1, "10uF 16V", "CL21A106KOQNNNE", "0805 X5R", FP_C0805, "mcu", "3V3 bulk at module"),
    Line(("C6",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", FP_C0402, "sensors", "BMI270 VDD"),
    Line(("C7",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", FP_C0402, "sensors", "INMP441 VDD"),
    Line(("C8",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", FP_C0402, "sensors", "AFE4404 VDD"),
    Line(("BT1",), 1, "LiPo 3.7 V 180 mAh", "pouch + PCM + PH", "wired", "", "mech", "Field cell", "≤1 C charge. Matches 100 mA PROG"),
    Line(("TAG1",), 1, "NTAG213 disc", "NTAG213 25 mm", "sticker", "", "mech", "Pet-door identity", "Enclosure only — not a PCB net"),
)


def all_refs() -> set[str]:
    return {ref for line in LINES for ref in line.refs}


def footprint_for(ref: str) -> str:
    for line in LINES:
        if ref in line.refs:
            return line.fp
    return ""


def emit_markdown() -> str:
    rows = [
        "# Collar Rev-A BOM (stuffed default)",
        "",
        f"Charge: **R1 = {RPROG_STUFFED} → {RPROG_STUFFED_MA} mA**. Schematic pad allows 2 kΩ (500 mA) — do not stuff that on a ~180 mAh pouch. See [AFE_CALCULATIONS.md](AFE_CALCULATIONS.md).",
        "",
        "Regenerate: `./kicad-launcher --sch bom` (writes this file and `BOM.csv`).",
        "",
        "Footprints are assigned on the schematic (`./kicad-launcher --sch bom`). PCB has GND pours; signal traces are still unrouted.",
        "",
        "| Qty | Ref | Value | MPN | Pkg | Footprint | Sheet | Role |",
        "|----:|-----|-------|-----|-----|-----------|-------|------|",
    ]
    for line in LINES:
        refs = ", ".join(line.refs)
        rows.append(
            f"| {line.qty} | {refs} | {line.value} | {line.mpn} | {line.pkg} | {line.fp or '—'} | {line.sheet} | {line.role} |"
        )
    rows.extend(
        [
            "",
            "## Notes",
            "",
            "- D4 (photodiode), D5 (660 nm), RT1/R11 (neck NTC), and R9/R10 (USB-C CC) are on the sheets.",
            "- Passives are 0402 / 0805 16 V ceramics. 10 µF on LDO and module per AFE §6.",
            "- Observational only. If a line looks like actuation, it is a spec bug.",
            "- Enclosure / collar strap / epoxy over the optical window are not in this PCB BOM.",
            "",
        ]
    )
    extras = [line for line in LINES if line.notes]
    if extras:
        rows.append("## Line notes")
        rows.append("")
        for line in extras:
            rows.append(f"- **{', '.join(line.refs)}:** {line.notes}")
        rows.append("")
    return "\n".join(rows)


def emit_csv() -> str:
    lines = ["Qty,Refs,Value,MPN,Package,Footprint,Sheet,Role,Notes"]
    for line in LINES:
        note = line.notes.replace('"', "'")
        lines.append(
            ",".join(
                [
                    str(line.qty),
                    " ".join(line.refs),
                    f'"{line.value}"',
                    f'"{line.mpn}"',
                    f'"{line.pkg}"',
                    f'"{line.fp}"',
                    line.sheet,
                    f'"{line.role}"',
                    f'"{note}"',
                ]
            )
        )
    return "\n".join(lines) + "\n"
