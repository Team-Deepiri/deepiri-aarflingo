#!/usr/bin/env python3
"""Emit collar-reva KiCad 7 schematic sheets from nets.py."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nets import BOARD, GPIO, TITLE

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "hardware" / BOARD

ROOT_UUID = "7fffe17a-9ffb-4f1f-b4b6-a4342b258eee"
POWER_SHEET_UUID = "722922c5-f112-4de2-9d1d-7f370e5d2a8b"
MCU_SHEET_UUID = "8715d69a-16d2-4496-965b-af55d3488b33"
SENSORS_SHEET_UUID = "72e61ef2-c28b-4186-b83a-fe973384e252"
POWER_FILE_UUID = "13884035-74b8-41a2-a20c-0d53cc2ab2d2"
MCU_FILE_UUID = "da3e4e7b-7bca-484f-bbf7-d4da3f5e0e67"
SENSORS_FILE_UUID = "35636077-3356-4ba6-9e80-adfe634ca69a"


def uid() -> str:
    return str(uuid.uuid4())


LIB_SYMBOLS = r'''
  (lib_symbols
    (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "R" (at 0 0 90)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at -1.778 0 90)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54)
          (stroke (width 0.254) (type default))
          (fill (type none))
        )
      )
      (symbol "R_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at 0 -3.81 90) (length 1.27)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0.635 2.54 0)
        (effects (font (size 1.27 1.27)) (justify left))
      )
      (property "Value" "C" (at 0.635 -2.54 0)
        (effects (font (size 1.27 1.27)) (justify left))
      )
      (property "Footprint" "" (at 0.9652 -3.81 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "C_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762))
          (stroke (width 0.508) (type default)) (fill (type none))
        )
        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762))
          (stroke (width 0.508) (type default)) (fill (type none))
        )
      )
      (symbol "C_1_1"
        (pin passive line (at 0 3.81 270) (length 2.794)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at 0 -3.81 90) (length 2.794)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "Device:LED" (pin_numbers hide) (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "LED" (at 0 -2.54 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "LED_0_1"
        (polyline (pts (xy -1.27 -1.27) (xy -1.27 1.27))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy -1.27 0) (xy 1.27 0))
          (stroke (width 0) (type default)) (fill (type none))
        )
        (polyline (pts (xy 1.27 -1.27) (xy 1.27 1.27) (xy -1.27 0) (xy 1.27 -1.27))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
      )
      (symbol "LED_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54)
          (name "K" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at 3.81 0 180) (length 2.54)
          (name "A" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "power:GND" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -6.35 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Value" "GND" (at 0 -3.81 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "GND_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27))
          (stroke (width 0) (type default)) (fill (type none))
        )
      )
      (symbol "GND_1_1"
        (pin power_in line (at 0 0 270) (length 0) hide
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "power:+3V3" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Value" "+3V3" (at 0 3.556 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "+3V3_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27))
          (stroke (width 0) (type default)) (fill (type none))
        )
        (polyline (pts (xy 0 0) (xy 0 2.54))
          (stroke (width 0) (type default)) (fill (type none))
        )
      )
      (symbol "+3V3_1_1"
        (pin power_in line (at 0 0 90) (length 0) hide
          (name "+3V3" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "Connector:Conn_01x04" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 5.08 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "Conn_01x04" (at 0 -7.62 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "Conn_01x04_1_1"
        (rectangle (start -1.27 -5.08) (end 1.27 5.08)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
        (pin passive line (at -5.08 3.81 0) (length 3.81)
          (name "Pin_1" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at -5.08 1.27 0) (length 3.81)
          (name "Pin_2" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at -5.08 -1.27 0) (length 3.81)
          (name "Pin_3" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at -5.08 -3.81 0) (length 3.81)
          (name "Pin_4" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "Connector:Conn_01x02" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 2.54 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "Conn_01x02" (at 0 -5.08 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "Conn_01x02_1_1"
        (rectangle (start -1.27 -2.54) (end 1.27 2.54)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
        (pin passive line (at -5.08 1.27 0) (length 3.81)
          (name "Pin_1" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at -5.08 -1.27 0) (length 3.81)
          (name "Pin_2" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "Device:Fuse" (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "F" (at 2.032 0 90)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "Fuse" (at 0 0 90)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "Fuse_0_1"
        (rectangle (start -0.762 -2.54) (end 0.762 2.54)
          (stroke (width 0.254) (type default)) (fill (type none))
        )
      )
      (symbol "Fuse_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at 0 -3.81 90) (length 1.27)
          (name "~" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "Device:D_TVS" (pin_numbers hide) (pin_names (offset 1.0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "D" (at 0 2.54 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "D_TVS" (at 0 -2.54 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "D_TVS_0_1"
        (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
        (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27) (xy -1.27 0) (xy 1.27 1.27))
          (stroke (width 0.254) (type default)) (fill (type none))
        )
      )
      (symbol "D_TVS_1_1"
        (pin passive line (at -3.81 0 0) (length 2.54)
          (name "A" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin passive line (at 3.81 0 180) (length 2.54)
          (name "K" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "aarf:IC5" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 8.89 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "IC5" (at 0 -8.89 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "IC5_0_1"
        (rectangle (start -7.62 -7.62) (end 7.62 7.62)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
      )
      (symbol "IC5_1_1"
        (pin unspecified line (at -10.16 5.08 0) (length 2.54)
          (name "1" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin unspecified line (at -10.16 2.54 0) (length 2.54)
          (name "2" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
        (pin unspecified line (at -10.16 0 0) (length 2.54)
          (name "3" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27))))
        )
        (pin unspecified line (at -10.16 -2.54 0) (length 2.54)
          (name "4" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27))))
        )
        (pin unspecified line (at -10.16 -5.08 0) (length 2.54)
          (name "5" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "aarf:MCU" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 22.86 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "ESP32-S3-MINI-1" (at 0 -22.86 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "https://www.espressif.com/" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "MCU_0_1"
        (rectangle (start -17.78 -20.32) (end 17.78 20.32)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
      )
      (symbol "MCU_1_1"
        (pin power_in line (at -20.32 17.78 0) (length 2.54)
          (name "3V3" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin power_in line (at -20.32 12.7 0) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at -20.32 7.62 0) (length 2.54)
          (name "EN" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27))))
        )
        (pin bidirectional line (at -20.32 2.54 0) (length 2.54)
          (name "GPIO0" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27))))
        )
        (pin bidirectional line (at -20.32 -2.54 0) (length 2.54)
          (name "USB_DN" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27))))
        )
        (pin bidirectional line (at -20.32 -7.62 0) (length 2.54)
          (name "USB_DP" (effects (font (size 1.27 1.27))))
          (number "6" (effects (font (size 1.27 1.27))))
        )
        (pin bidirectional line (at 20.32 17.78 180) (length 2.54)
          (name "SDA" (effects (font (size 1.27 1.27))))
          (number "7" (effects (font (size 1.27 1.27))))
        )
        (pin bidirectional line (at 20.32 12.7 180) (length 2.54)
          (name "SCL" (effects (font (size 1.27 1.27))))
          (number "8" (effects (font (size 1.27 1.27))))
        )
        (pin output line (at 20.32 7.62 180) (length 2.54)
          (name "I2S_SCK" (effects (font (size 1.27 1.27))))
          (number "9" (effects (font (size 1.27 1.27))))
        )
        (pin output line (at 20.32 2.54 180) (length 2.54)
          (name "I2S_WS" (effects (font (size 1.27 1.27))))
          (number "10" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at 20.32 -2.54 180) (length 2.54)
          (name "I2S_SD" (effects (font (size 1.27 1.27))))
          (number "11" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at 20.32 -7.62 180) (length 2.54)
          (name "IMU_INT" (effects (font (size 1.27 1.27))))
          (number "12" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at 20.32 -12.7 180) (length 2.54)
          (name "VBAT_SENSE" (effects (font (size 1.27 1.27))))
          (number "13" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at 20.32 -17.78 180) (length 2.54)
          (name "CHG_STAT" (effects (font (size 1.27 1.27))))
          (number "14" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "aarf:IMU" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 10.16 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "BMI270" (at 0 -10.16 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "IMU_0_1"
        (rectangle (start -10.16 -8.89) (end 10.16 8.89)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
      )
      (symbol "IMU_1_1"
        (pin power_in line (at -12.7 6.35 0) (length 2.54)
          (name "VDD" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin power_in line (at -12.7 3.81 0) (length 2.54)
          (name "VDDIO" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
        (pin power_in line (at -12.7 0 0) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27))))
        )
        (pin bidirectional line (at 12.7 6.35 180) (length 2.54)
          (name "SDA" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27))))
        )
        (pin bidirectional line (at 12.7 3.81 180) (length 2.54)
          (name "SCL" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27))))
        )
        (pin output line (at 12.7 0 180) (length 2.54)
          (name "INT1" (effects (font (size 1.27 1.27))))
          (number "6" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "aarf:MIC" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 8.89 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "INMP441" (at 0 -8.89 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "~" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "MIC_0_1"
        (rectangle (start -10.16 -7.62) (end 10.16 7.62)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
      )
      (symbol "MIC_1_1"
        (pin power_in line (at -12.7 5.08 0) (length 2.54)
          (name "VDD" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin power_in line (at -12.7 2.54 0) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at 12.7 5.08 180) (length 2.54)
          (name "SCK" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at 12.7 2.54 180) (length 2.54)
          (name "WS" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27))))
        )
        (pin output line (at 12.7 0 180) (length 2.54)
          (name "SD" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at 12.7 -2.54 180) (length 2.54)
          (name "LR" (effects (font (size 1.27 1.27))))
          (number "6" (effects (font (size 1.27 1.27))))
        )
      )
    )
    (symbol "aarf:PPG" (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 0 10.16 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Value" "AFE4404" (at 0 -10.16 0)
        (effects (font (size 1.27 1.27)))
      )
      (property "Footprint" "" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (property "Datasheet" "https://www.ti.com/product/AFE4404" (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide)
      )
      (symbol "PPG_0_1"
        (rectangle (start -12.7 -10.16) (end 12.7 10.16)
          (stroke (width 0.254) (type default)) (fill (type background))
        )
      )
      (symbol "PPG_1_1"
        (pin power_in line (at -15.24 7.62 0) (length 2.54)
          (name "VDD" (effects (font (size 1.27 1.27))))
          (number "1" (effects (font (size 1.27 1.27))))
        )
        (pin power_in line (at -15.24 5.08 0) (length 2.54)
          (name "GND" (effects (font (size 1.27 1.27))))
          (number "2" (effects (font (size 1.27 1.27))))
        )
        (pin bidirectional line (at -15.24 2.54 0) (length 2.54)
          (name "SDA" (effects (font (size 1.27 1.27))))
          (number "3" (effects (font (size 1.27 1.27))))
        )
        (pin bidirectional line (at -15.24 0 0) (length 2.54)
          (name "SCL" (effects (font (size 1.27 1.27))))
          (number "4" (effects (font (size 1.27 1.27))))
        )
        (pin output line (at 15.24 7.62 180) (length 2.54)
          (name "ADC_RDY" (effects (font (size 1.27 1.27))))
          (number "5" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at 15.24 5.08 180) (length 2.54)
          (name "RESET" (effects (font (size 1.27 1.27))))
          (number "6" (effects (font (size 1.27 1.27))))
        )
        (pin output line (at 15.24 2.54 180) (length 2.54)
          (name "TXP" (effects (font (size 1.27 1.27))))
          (number "7" (effects (font (size 1.27 1.27))))
        )
        (pin input line (at 15.24 0 180) (length 2.54)
          (name "INP" (effects (font (size 1.27 1.27))))
          (number "8" (effects (font (size 1.27 1.27))))
        )
      )
    )
  )
'''


def header(file_uuid: str, title: str, comment: str) -> str:
    return f'''(kicad_sch (version 20230121) (generator eeschema)

  (uuid {file_uuid})

  (paper "A4")

  (title_block
    (title "{title}")
    (date "2026-08-21")
    (rev "A")
    (comment 1 "{comment}")
    (comment 2 "Observational wearable — no actuators on this board")
  )
{LIB_SYMBOLS}
'''


def footer() -> str:
    return ")\n"


def glabel(name: str, x: float, y: float, shape: str = "input") -> str:
    return f'''  (global_label "{name}" (shape {shape}) (at {x} {y} 0) (fields_autoplaced)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid {uid()})
  )
'''


def wire(x1: float, y1: float, x2: float, y2: float) -> str:
    return f'''  (wire (pts (xy {x1} {y1}) (xy {x2} {y2}))
    (stroke (width 0) (type default))
    (uuid {uid()})
  )
'''


def text(msg: str, x: float, y: float) -> str:
    return f'''  (text "{msg}" (at {x} {y} 0)
    (effects (font (size 1.27 1.27)) (justify left bottom))
    (uuid {uid()})
  )
'''


def symbol(
    lib_id: str,
    ref: str,
    value: str,
    x: float,
    y: float,
    pins: list[str],
    path: str,
    rotation: int = 0,
) -> str:
    pin_block = "\n".join(f'    (pin "{p}" (uuid {uid()}))' for p in pins)
    return f'''  (symbol (lib_id "{lib_id}") (at {x} {y} {rotation}) (unit 1)
    (in_bom yes) (on_board yes)
    (uuid {uid()})
    (property "Reference" "{ref}" (at {x} {y - 12.7} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "{value}" (at {x} {y + 12.7} 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (property "Datasheet" "~" (at {x} {y} 0)
      (effects (font (size 1.27 1.27)) hide)
    )
{pin_block}
    (instances
      (project "{BOARD}"
        (path "{path}"
          (reference "{ref}") (unit 1)
        )
      )
    )
  )
'''


def emit_root() -> str:
    body = header(ROOT_UUID, TITLE, "Dog-worn IMU + mic puck. Hierarchical: power / mcu / sensors.")
    body += text("Aarflingo Collar Rev-A — physical device ON THE DOG (collar / harness puck)", 25.4, 25.4)
    body += text("No actuation. Identity tag is a passive RFID disc in the enclosure (not on-PCB).", 25.4, 30.48)
    body += f'''
  (sheet (at 38.1 50.8) (size 50.8 38.1)
    (stroke (width 0.1524) (type solid))
    (fill (color 0 0 0 0.0000))
    (uuid {POWER_SHEET_UUID})
    (property "Sheetname" "Power" (id 0) (at 38.1 50.0384 0)
      (effects (font (size 1.27 1.27)) (justify left bottom))
    )
    (property "Sheetfile" "power.kicad_sch" (id 1) (at 38.1 89.535 0)
      (effects (font (size 1.27 1.27)) (justify left top))
    )
    (pin "3V3" output (at 88.9 63.5 0)
      (effects (font (size 1.27 1.27)) (justify right))
      (uuid {uid()})
    )
    (pin "GND" output (at 88.9 71.12 0)
      (effects (font (size 1.27 1.27)) (justify right))
      (uuid {uid()})
    )
  )

  (sheet (at 114.3 50.8) (size 50.8 38.1)
    (stroke (width 0.1524) (type solid))
    (fill (color 0 0 0 0.0000))
    (uuid {MCU_SHEET_UUID})
    (property "Sheetname" "MCU" (id 0) (at 114.3 50.0384 0)
      (effects (font (size 1.27 1.27)) (justify left bottom))
    )
    (property "Sheetfile" "mcu.kicad_sch" (id 1) (at 114.3 89.535 0)
      (effects (font (size 1.27 1.27)) (justify left top))
    )
    (pin "3V3" input (at 114.3 63.5 180)
      (effects (font (size 1.27 1.27)) (justify left))
      (uuid {uid()})
    )
    (pin "GND" input (at 114.3 71.12 180)
      (effects (font (size 1.27 1.27)) (justify left))
      (uuid {uid()})
    )
  )

  (sheet (at 76.2 114.3) (size 50.8 38.1)
    (stroke (width 0.1524) (type solid))
    (fill (color 0 0 0 0.0000))
    (uuid {SENSORS_SHEET_UUID})
    (property "Sheetname" "Sensors" (id 0) (at 76.2 113.5384 0)
      (effects (font (size 1.27 1.27)) (justify left bottom))
    )
    (property "Sheetfile" "sensors.kicad_sch" (id 1) (at 76.2 153.035 0)
      (effects (font (size 1.27 1.27)) (justify left top))
    )
  )

  (sheet_instances
    (path "/" (page "1"))
    (path "/{POWER_SHEET_UUID}" (page "2"))
    (path "/{MCU_SHEET_UUID}" (page "3"))
    (path "/{SENSORS_SHEET_UUID}" (page "4"))
  )
'''
    body += footer()
    return body


def emit_power() -> str:
    path = f"/{ROOT_UUID}/{POWER_SHEET_UUID}"
    b = header(POWER_FILE_UUID, f"{TITLE} — Power", "USB-C → TVS → PTC → MCP73831 → LiPo → AP2112K-3.3")
    b += text("Dirty zone: USB / charger. Keep away from I2S mic.", 20, 20)
    b += symbol("Connector:Conn_01x04", "J1", "USB-C", 40, 70, ["1", "2", "3", "4"], path)
    b += symbol("Device:D_TVS", "D1", "USBLC6", 65, 55, ["1", "2"], path)
    b += symbol("Device:Fuse", "F1", "PTC 500mA", 90, 50, ["1", "2"], path)
    b += symbol("aarf:IC5", "U2", "MCP73831", 120, 55, ["1", "2", "3", "4", "5"], path)
    b += symbol("Connector:Conn_01x02", "J2", "JST-PH LiPo", 155, 55, ["1", "2"], path)
    b += symbol("aarf:IC5", "U3", "AP2112K-3.3", 190, 55, ["1", "2", "3", "4", "5"], path)
    b += symbol("Device:R", "R1", "2k PROG", 120, 80, ["1", "2"], path)
    b += symbol("Device:R", "R2", "100k", 175, 90, ["1", "2"], path)
    b += symbol("Device:R", "R3", "100k", 175, 105, ["1", "2"], path)
    b += symbol("Device:C", "C1", "10uF", 190, 80, ["1", "2"], path)
    b += symbol("Device:C", "C2", "10uF", 205, 80, ["1", "2"], path)
    b += symbol("Device:C", "C3", "100nF", 175, 120, ["1", "2"], path)
    b += symbol("power:GND", "#PWR01", "GND", 40, 95, ["1"], path)
    b += symbol("power:+3V3", "#PWR02", "+3V3", 215, 40, ["1"], path)
    for name, x, y in (
        ("VUSB", 28, 66.19),
        ("USB_DP", 28, 71.27),
        ("USB_DN", 28, 68.73),
        ("GND", 28, 73.81),
        ("VBAT", 148, 53.73),
        ("CHG_STAT", 109, 55),
        ("VBAT_SENSE", 175, 97.54),
        ("3V3", 215, 55),
    ):
        b += glabel(name, x, y)
    b += footer()
    return b


def emit_mcu() -> str:
    path = f"/{ROOT_UUID}/{MCU_SHEET_UUID}"
    b = header(MCU_FILE_UUID, f"{TITLE} — MCU", "ESP32-S3-MINI-1 used pins only. Remaining module pins NC.")
    gpio_txt = "  ".join(f"{n}=GPIO{g}" for n, g in GPIO.items())
    b += text(gpio_txt, 20, 18)
    b += text("GPIO0 = boot only (10k to 3V3). No live bus on 0/3/45/46.", 20, 22)
    b += symbol("aarf:MCU", "U1", "ESP32-S3-MINI-1", 110, 80, [str(i) for i in range(1, 15)], path)
    b += symbol("Device:R", "R4", "10k EN", 70, 55, ["1", "2"], path)
    b += symbol("Device:R", "R5", "10k BOOT", 70, 80, ["1", "2"], path)
    b += symbol("Device:R", "R6", "330 LED", 160, 110, ["1", "2"], path)
    b += symbol("Device:LED", "D2", "STAT", 175, 110, ["1", "2"], path)
    b += symbol("Device:C", "C4", "0.1uF", 80, 45, ["1", "2"], path)
    b += symbol("Device:C", "C5", "10uF", 95, 45, ["1", "2"], path)
    b += symbol("power:GND", "#PWR03", "GND", 90, 110, ["1"], path)
    b += symbol("power:+3V3", "#PWR04", "+3V3", 90, 50, ["1"], path)
    for name, x, y in (
        ("3V3", 85, 62.22),
        ("GND", 85, 67.3),
        ("EN", 85, 72.38),
        ("GPIO0", 85, 77.46),
        ("USB_DN", 85, 82.54),
        ("USB_DP", 85, 87.62),
        ("SDA", 135, 62.22),
        ("SCL", 135, 67.3),
        ("I2S_SCK", 135, 72.38),
        ("I2S_WS", 135, 77.46),
        ("I2S_SD", 135, 82.54),
        ("IMU_INT", 135, 87.62),
        ("VBAT_SENSE", 135, 92.7),
        ("CHG_STAT", 135, 97.78),
        ("LED_STAT", 155, 110),
        ("PPG_RDY", 155, 120),
        ("PPG_RST", 155, 125),
    ):
        b += glabel(name, x, y)
    b += footer()
    return b


def emit_sensors() -> str:
    path = f"/{ROOT_UUID}/{SENSORS_SHEET_UUID}"
    b = header(SENSORS_FILE_UUID, f"{TITLE} — Sensors", "BMI270 + INMP441 + TI AFE4404 neck PPG.")
    b += text("I2C pull-ups 4.7k. AFE4404 optical AFE faces the ventral neck (carotid).", 20, 20)
    b += symbol("aarf:IMU", "U4", "BMI270", 80, 70, ["1", "2", "3", "4", "5", "6"], path)
    b += symbol("aarf:MIC", "U5", "INMP441", 160, 70, ["1", "2", "3", "4", "5", "6"], path)
    b += symbol("aarf:PPG", "U6", "AFE4404", 80, 140, ["1", "2", "3", "4", "5", "6", "7", "8"], path)
    b += symbol("Device:LED", "D3", "IR neck", 130, 140, ["1", "2"], path)
    b += symbol("Device:C", "C8", "0.1uF PPG", 55, 140, ["1", "2"], path)
    b += symbol("Device:R", "R7", "4.7k", 110, 45, ["1", "2"], path)
    b += symbol("Device:R", "R8", "4.7k", 125, 45, ["1", "2"], path)
    b += symbol("Device:C", "C6", "0.1uF IMU", 80, 95, ["1", "2"], path)
    b += symbol("Device:C", "C7", "0.1uF MIC", 160, 95, ["1", "2"], path)
    b += symbol("power:GND", "#PWR05", "GND", 80, 110, ["1"], path)
    b += symbol("power:+3V3", "#PWR06", "+3V3", 80, 45, ["1"], path)
    for name, x, y in (
        ("3V3", 63, 63.65),
        ("GND", 63, 70),
        ("SDA", 97, 63.65),
        ("SCL", 97, 66.19),
        ("IMU_INT", 97, 70),
        ("I2S_SCK", 177, 64.92),
        ("I2S_WS", 177, 67.46),
        ("I2S_SD", 177, 70),
        ("PPG_RDY", 100, 132.38),
        ("PPG_RST", 100, 134.92),
        ("SDA", 60, 142.54),
        ("SCL", 60, 140),
    ):
        b += glabel(name, x, y)
    b += footer()
    return b


def emit_pins_h() -> str:
    lines = [
        "#pragma once",
        "/* Generated from scripts/aarf_sch/nets.py — do not edit by hand. */",
        "",
    ]
    for net, gpio in GPIO.items():
        lines.append(f"#define PIN_{net} {gpio}")
    lines.append("")
    return "\n".join(lines)


def emit_pcb() -> str:
    return '''(kicad_pcb (version 20221018) (generator pcbnew)

  (general
    (thickness 1.6)
  )

  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )

  (setup
    (pad_to_mask_clearance 0)
  )

  (gr_rect (start 100 80) (end 130 110)
    (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (tstamp ''' + uid() + ''')
  )
)
'''


def emit_pro() -> str:
    return f'''{{
  "board": {{
    "design_settings": {{
      "defaults": {{}},
      "diff_pair_dimensions": [],
      "drc_exclusions": [],
      "meta": {{
        "version": 1
      }},
      "rule_severities": {{}},
      "rules": {{
        "max_error": 0.005,
        "min_clearance": 0.0,
        "min_connection": 0.0,
        "min_copper_edge_clearance": 0.0
      }},
      "teardrop_options": [],
      "teardrop_parameters": [],
      "track_widths": [],
      "via_dimensions": [],
      "zones": []
    }}
  }},
  "boards": [],
  "cvpcb": {{
    "equivalence_files": []
  }},
  "libraries": {{
    "pinned_footprint_libs": [],
    "pinned_symbol_libs": []
  }},
  "meta": {{
    "filename": "{BOARD}.kicad_pro",
    "version": 1
  }},
  "net_settings": {{
    "classes": [
      {{
        "bus_width": 12,
        "clearance": 0.2,
        "diff_pair_gap": 0.25,
        "diff_pair_via_gap": 0.25,
        "diff_pair_width": 0.2,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "Default",
        "pcb_color": "rgba(0, 0, 0, 0.000)",
        "schematic_color": "rgba(0, 0, 0, 0.000)",
        "track_width": 0.25,
        "via_diameter": 0.8,
        "via_drill": 0.4,
        "wire_width": 6
      }}
    ],
    "meta": {{
      "version": 3
    }}
  }},
  "pcbnew": {{
    "last_paths": {{
      "gencad": "",
      "idf": "",
      "netlist": "",
      "specctra_dsn": "",
      "step": "",
      "vrml": ""
    }},
    "page_layout_descr_file": ""
  }},
  "schematic": {{
    "annotate_start_num": 0,
    "drawing": {{
      "dashed_lines_dash_length_ratio": 12.0,
      "dashed_lines_gap_length_ratio": 3.0,
      "default_line_thickness": 6.0,
      "default_text_size": 50.0,
      "field_names": [],
      "intersheets_ref_own_page": false,
      "intersheets_ref_prefix": "",
      "intersheets_ref_short": false,
      "intersheets_ref_show": false,
      "intersheets_ref_suffix": "",
      "junction_size_choice": 3,
      "label_size_ratio": 0.375,
      "pin_symbol_size": 25.0,
      "text_offset_ratio": 0.15
    }},
    "legacy_lib_dir": "",
    "legacy_lib_list": [],
    "meta": {{
      "version": 1
    }},
    "net_format_name": "",
    "page_layout_descr_file": "",
    "plot_directory": "",
    "spice_current_sheet_as_root": false,
    "spice_external_command": "spice \\"%I\\"",
    "spice_model_current_sheet_as_root": true,
    "spice_save_all_currents": false,
    "spice_save_all_displacements": false,
    "spice_save_all_voltages": false,
    "subpart_first_id": 65,
    "subpart_id_separator": 0
  }},
  "sheets": [
    [
      "{ROOT_UUID}",
      "Root"
    ]
  ],
  "text_variables": {{}}
}}
'''


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "collar-reva.kicad_sch").write_text(emit_root(), encoding="utf-8")
    (OUT / "power.kicad_sch").write_text(emit_power(), encoding="utf-8")
    (OUT / "mcu.kicad_sch").write_text(emit_mcu(), encoding="utf-8")
    (OUT / "sensors.kicad_sch").write_text(emit_sensors(), encoding="utf-8")
    (OUT / "collar-reva.kicad_pro").write_text(emit_pro(), encoding="utf-8")
    (OUT / "collar-reva.kicad_pcb").write_text(emit_pcb(), encoding="utf-8")
    pins = emit_pins_h()
    (OUT / "pins.h").write_text(pins, encoding="utf-8")
    fw_pins = REPO_ROOT / "firmware" / "collar" / "include" / "pins.h"
    fw_pins.parent.mkdir(parents=True, exist_ok=True)
    fw_pins.write_text(pins, encoding="utf-8")
    print(f"wrote {OUT} and {fw_pins}")


if __name__ == "__main__":
    main()
