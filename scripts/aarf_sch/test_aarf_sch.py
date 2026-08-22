from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from cli import cmd_next, cmd_status, cmd_verify, labels_in, parse_pins_h, read_sheet  # noqa: E402
from nets import FORBIDDEN_NETS, GPIO, SHEET_NETS  # noqa: E402


def test_verify_passes_on_emitted_board():
    assert cmd_verify() == 0


def test_status_passes():
    assert cmd_status() == 0


def test_next_prints_checklist(capsys):
    assert cmd_next() == 0
    out = capsys.readouterr().out
    assert "kicad-launcher --run collar" in out


def test_pins_h_matches_gpio_map():
    assert parse_pins_h() == GPIO


def test_every_sheet_has_required_labels():
    for sheet, required in SHEET_NETS.items():
        present = labels_in(read_sheet(sheet))
        missing = set(required) - present
        assert not missing, f"{sheet} missing {missing}"


def test_ethics_denylist_absent_from_labels():
    for sheet in SHEET_NETS:
        present = {label.upper() for label in labels_in(read_sheet(sheet))}
        for bad in FORBIDDEN_NETS:
            assert all(bad not in label for label in present), f"{sheet} net matches {bad}"


def test_no_live_net_on_strapping_pins():
    from nets import STRAPPING_DO_NOT_USE_LIVE

    for net, gpio in GPIO.items():
        assert gpio not in STRAPPING_DO_NOT_USE_LIVE, net


def test_vbat_sense_is_adc1_not_adc2():
    # ESP32-S3 ADC2 conflicts with Wi-Fi. GPIO1 is ADC1_CH0.
    assert GPIO["VBAT_SENSE"] == 1


def test_kicad_cli_loads_sheets(tmp_path):
    import shutil
    import subprocess

    if not shutil.which("kicad-cli"):
        pytest.skip("kicad-cli not installed")
    sch = HERE.parents[1] / "hardware" / "collar-reva" / "collar-reva.kicad_sch"
    out = tmp_path / "collar.net"
    result = subprocess.run(
        ["kicad-cli", "sch", "export", "netlist", "-o", str(out), str(sch)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert out.is_file()
