"""Collar Rev-A electrical contract.

Single source of truth for nets, GPIO, and the ethics denylist.
Firmware `hardware/collar-reva/pins.h` and the KiCad sheets must match this file.
"""

from __future__ import annotations

BOARD = "collar-reva"
TITLE = "Aarflingo Collar Rev-A"
MCU = "ESP32-S3-MINI-1"
# 40×32 mm: USB/charger dirty, module, optical/clean. 30×30 cannot fit MINI-1 + USB-C.
BOARD_W_MM = 40.0
BOARD_H_MM = 32.0

# Observational wearable only. These substrings must never appear as net names.
FORBIDDEN_NETS = (
    "SHOCK",
    "STIM",
    "VIBE",
    "HAPTIC",
    "SOLENOID",
    "MOTOR",
    "STRIKE",
    "PUNISH",
)

# Live buses. GPIO0 is boot-only (strapping) and is not listed here.
GPIO = {
    "SDA": 4,
    "SCL": 5,
    "I2S_SCK": 7,
    "I2S_WS": 15,
    "I2S_SD": 16,
    "IMU_INT": 17,
    "VBAT_SENSE": 1,  # ADC1_CH0 — never ADC2 (Wi-Fi conflict)
    "CHG_STAT": 2,
    "LED_STAT": 6,
    "PPG_RDY": 8,  # TI AFE4404 ADC_RDY
    "PPG_RST": 9,  # TI AFE4404 RESET (active low)
    "SKIN_SENSE": 10,  # ADC1_CH9 — 10k NTC divider, not a strap
}

BOOT_GPIO = 0
STRAPPING_DO_NOT_USE_LIVE = (0, 3, 45, 46)
USB_D_N_GPIO = 19
USB_D_P_GPIO = 20

SHEET_NETS = {
    "power": (
        "VUSB",
        "VBAT",
        "3V3",
        "GND",
        "VBAT_SENSE",
        "CHG_STAT",
        "USB_DP",
        "USB_DN",
        "CC1",
        "CC2",
    ),
    "mcu": (
        "3V3",
        "GND",
        "SDA",
        "SCL",
        "I2S_SCK",
        "I2S_WS",
        "I2S_SD",
        "IMU_INT",
        "VBAT_SENSE",
        "CHG_STAT",
        "LED_STAT",
        "PPG_RDY",
        "PPG_RST",
        "SKIN_SENSE",
        "USB_DP",
        "USB_DN",
        "EN",
        "GPIO0",
    ),
    "sensors": (
        "3V3",
        "GND",
        "SDA",
        "SCL",
        "I2S_SCK",
        "I2S_WS",
        "I2S_SD",
        "IMU_INT",
        "PPG_RDY",
        "PPG_RST",
        "PPG_TXP",
        "PPG_TX2",
        "PPG_INP",
        "SKIN_SENSE",
    ),
}

REQUIRED_PARTS = {
    "power": ("J1", "D1", "F1", "U2", "U3", "J2", "R9", "R10"),
    "mcu": ("U1",),
    "sensors": ("U4", "U5", "U6", "D3", "D4", "D5", "RT1"),
}

# MCP73831: IREG = 1 V / RPROG. Schematic 2 kΩ = 500 mA max pad.
# BOM default: 10 kΩ → 100 mA (see hardware/collar-reva/AFE_CALCULATIONS.md).
RPROG_OHMS = 2000
VBAT_DIV_TOP_OHMS = 100_000
VBAT_DIV_BOT_OHMS = 100_000
I2C_PULLUP_OHMS = 4700
LED_SERIES_OHMS = 330

NEXT_STEPS = (
    "Open the board: ./kicad-launcher --run collar",
    "Footprints are on the symbols. Layout: USB/charger dirty zone opposite I2S mic; solid GND plane",
    "Run schematic ERC in KiCad (or kicad-cli sch erc on KiCad 9+)",
    "Update gerbers after copper; stuff from hardware/collar-reva/BOM.csv",
    "Firmware: keep hardware/collar-reva/pins.h in lockstep with scripts/aarf_sch/nets.py",
)
