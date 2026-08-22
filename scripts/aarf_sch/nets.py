"""Collar Rev-A electrical contract.

Single source of truth for nets, GPIO, and the ethics denylist.
Firmware `hardware/collar-reva/pins.h` and the KiCad sheets must match this file.
"""

from __future__ import annotations

BOARD = "collar-reva"
TITLE = "Aarflingo Collar Rev-A"
MCU = "ESP32-S3-MINI-1"

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
    ),
}

REQUIRED_PARTS = {
    "power": ("J1", "D1", "F1", "U2", "U3", "J2"),
    "mcu": ("U1",),
    "sensors": ("U4", "U5"),
}

# MCP73831: IREG ≈ 1000 / RPROG_kΩ → 2 kΩ ≈ 500 mA.
RPROG_OHMS = 2000
VBAT_DIV_TOP_OHMS = 100_000
VBAT_DIV_BOT_OHMS = 100_000
I2C_PULLUP_OHMS = 4700
LED_SERIES_OHMS = 330

NEXT_STEPS = (
    "Open the board: ./kicad-launcher --run collar",
    "Assign footprints (USB-C, JST-PH, ESP32-S3-MINI-1, SOT-23-5 charger/LDO)",
    "Run schematic ERC in KiCad (or kicad-cli sch erc on KiCad 9+)",
    "Layout: USB/charger dirty zone opposite I2S mic; solid GND plane",
    "Firmware: keep hardware/collar-reva/pins.h in lockstep with scripts/aarf_sch/nets.py",
)
