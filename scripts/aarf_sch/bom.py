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
    sheet: str
    role: str
    notes: str = ""


# Stuffed default. Schematic R1 value text may still say 2k (max pad).
RPROG_STUFFED = "10k"
RPROG_STUFFED_MA = 100

LINES: tuple[Line, ...] = (
    Line(("U1",), 1, "ESP32-S3-MINI-1-N8", "ESP32-S3-MINI-1-N8", "module", "mcu", "MCU + BLE + 8 MB flash"),
    Line(("U2",), 1, "MCP73831 4.2 V", "MCP73831T-2ACI/OT", "SOT-23-5", "power", "LiPo charge"),
    Line(("U3",), 1, "AP2112K-3.3 600 mA", "AP2112K-3.3TRG1", "SOT-23-5", "power", "3V3 LDO"),
    Line(("U4",), 1, "BMI270", "BMI270", "LGA-14 2.5×3.0", "sensors", "IMU I2C 0x68"),
    Line(("U5",), 1, "INMP441", "INMP441", "LGA", "sensors", "I2S mic", "TDK EOL — ICS-43434 is the I2S drop-in if INMP441 is N/A"),
    Line(("U6",), 1, "AFE4404", "AFE4404YZPR", "DSBGA-15", "sensors", "Neck PPG I2C 0x58", "Reflow; not a hand-solder first proto"),
    Line(("D1",), 1, "USBLC6-2SC6", "USBLC6-2SC6", "SOT-23-6", "power", "USB ESD on VBUS/D+/D−"),
    Line(("D2",), 1, "Green LED", "LTST-C190KGKT", "0402", "mcu", "STAT, MCU sink via R6"),
    Line(("D3",), 1, "940 nm IR LED", "SFH 4451", "SMD 0805-class", "sensors", "PPG emitter toward ventral neck", "U6 TXP. Keep If at the AFE 4 mA bring-up current"),
    Line(("D4",), 1, "940 nm photodiode", "SFH 2704", "SMD", "sensors", "PPG detector", "U6 INP. Not yet a sheet symbol — place at layout"),
    Line(("F1",), 1, "PTC 500 mA", "MF-MSMF050-2", "1812", "power", "USB inrush"),
    Line(("J1",), 1, "USB-C receptacle", "USB4105-GF-A", "16-pin SMD", "power", "Charge + USB-JTAG D+/D−", "Needs CC pulldowns R9/R10 for C-to-C VBUS"),
    Line(("J2",), 1, "JST-PH 2", "S2B-PH-SM4-TB", "SMD 2.0 mm", "power", "LiPo"),
    Line(("R1",), 1, RPROG_STUFFED, "RC0402FR-0710KL", "0402 1%", "power", f"PROG → {RPROG_STUFFED_MA} mA", "Do not stuff 2 kΩ on a ~180 mAh pouch (≈2.8 C)"),
    Line(("R2",), 1, "100k", "RC0402FR-07100KL", "0402 1%", "power", "VBAT divider top"),
    Line(("R3",), 1, "100k", "RC0402FR-07100KL", "0402 1%", "power", "VBAT divider bottom"),
    Line(("R4",), 1, "10k", "RC0402FR-0710KL", "0402 1%", "mcu", "EN pull-up"),
    Line(("R5",), 1, "10k", "RC0402FR-0710KL", "0402 1%", "mcu", "GPIO0 / BOOT pull-up"),
    Line(("R6",), 1, "330", "RC0402FR-07330RL", "0402 1%", "mcu", "STAT LED series", f"{LED_SERIES_OHMS} Ω → ~3.9 mA"),
    Line(("R7",), 1, "4.7k", "RC0402FR-074K7L", "0402 1%", "sensors", "I2C SDA pull-up"),
    Line(("R8",), 1, "4.7k", "RC0402FR-074K7L", "0402 1%", "sensors", "I2C SCL pull-up"),
    Line(("R9",), 1, "5.1k", "RC0402FR-075K1L", "0402 1%", "power", "USB-C CC1 pulldown", "Not on the 4-pin USB symbol — add at layout or VBUS never appears on C-to-C"),
    Line(("R10",), 1, "5.1k", "RC0402FR-075K1L", "0402 1%", "power", "USB-C CC2 pulldown"),
    Line(("C1",), 1, "10uF 16V", "CL21A106KOQNNNE", "0805 X5R", "power", "LDO VIN"),
    Line(("C2",), 1, "10uF 16V", "CL21A106KOQNNNE", "0805 X5R", "power", "LDO VOUT"),
    Line(("C3",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", "power", "VBAT anti-alias"),
    Line(("C4",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", "mcu", "3V3 HF at module"),
    Line(("C5",), 1, "10uF 16V", "CL21A106KOQNNNE", "0805 X5R", "mcu", "3V3 bulk at module"),
    Line(("C6",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", "sensors", "BMI270 VDD"),
    Line(("C7",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", "sensors", "INMP441 VDD"),
    Line(("C8",), 1, "100nF 16V", "CC0402KRX7R7BB104", "0402 X7R", "sensors", "AFE4404 VDD"),
    Line(("BT1",), 1, "LiPo 3.7 V 180 mAh", "pouch + PCM + PH", "wired", "mech", "Field cell", "≤1 C charge. Matches 100 mA PROG"),
    Line(("TAG1",), 1, "NTAG213 disc", "NTAG213 25 mm", "sticker", "mech", "Pet-door identity", "Enclosure only — not a PCB net"),
)


def all_refs() -> set[str]:
    return {ref for line in LINES for ref in line.refs}


def emit_markdown() -> str:
    rows = [
        "# Collar Rev-A BOM (stuffed default)",
        "",
        f"Charge: **R1 = {RPROG_STUFFED} → {RPROG_STUFFED_MA} mA**. Schematic pad allows 2 kΩ (500 mA) — do not stuff that on a ~180 mAh pouch. See [AFE_CALCULATIONS.md](AFE_CALCULATIONS.md).",
        "",
        "Regenerate: `./kicad-launcher --sch bom` (writes this file and `BOM.csv`).",
        "",
        "Footprints below are the intended packages. They are **not assigned in KiCad yet**.",
        "",
        "| Qty | Ref | Value | MPN | Pkg | Sheet | Role |",
        "|----:|-----|-------|-----|-----|-------|------|",
    ]
    for line in LINES:
        refs = ", ".join(line.refs)
        rows.append(
            f"| {line.qty} | {refs} | {line.value} | {line.mpn} | {line.pkg} | {line.sheet} | {line.role} |"
        )
    rows.extend(
        [
            "",
            "## Notes",
            "",
            "- D4, R9, R10 are required to function and are **not** on the current sheets. Place them at layout.",
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
    lines = ["Qty,Refs,Value,MPN,Package,Sheet,Role,Notes"]
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
                    line.sheet,
                    f'"{line.role}"',
                    f'"{note}"',
                ]
            )
        )
    return "\n".join(lines) + "\n"
