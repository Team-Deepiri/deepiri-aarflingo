from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from bom import LINES, RPROG_STUFFED, all_refs, emit_markdown  # noqa: E402
from cli import (  # noqa: E402
    LAYOUT_ONLY_REFS,
    cmd_bom,
    cmd_next,
    cmd_status,
    cmd_verify,
    instance_refs,
    labels_in,
    parse_pins_h,
    read_sheet,
)
from nets import BOARD_H_MM, BOARD_W_MM, FORBIDDEN_NETS, GPIO, I2C_PULLUP_OHMS, SHEET_NETS, VBAT_DIV_BOT_OHMS, VBAT_DIV_TOP_OHMS  # noqa: E402


def test_pcb_places_every_stuffed_ref():
    pcb = (HERE.parents[1] / "hardware" / "collar-reva" / "collar-reva.kicad_pcb").read_text(
        encoding="utf-8"
    )
    skip = {"BT1", "TAG1"}
    missing = [
        ref
        for ref in all_refs()
        if ref not in skip and f'(property "Reference" "{ref}"' not in pcb
    ]
    assert not missing, missing
    assert "Edge.Cuts" in pcb
    assert "RF_KEEP" in pcb
    assert f"{100 + BOARD_W_MM:.1f}" in pcb or f"{100 + BOARD_W_MM:.0f}" in pcb
    assert BOARD_H_MM >= 32.0


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


def test_bom_passives_match_nets():
    assert VBAT_DIV_TOP_OHMS == VBAT_DIV_BOT_OHMS == 100_000
    assert I2C_PULLUP_OHMS == 4700
    assert next(line for line in LINES if "R2" in line.refs).value == "100k"
    assert next(line for line in LINES if "R7" in line.refs).value == "4.7k"


def test_bom_rprog_is_100_ma_not_500():
    assert RPROG_STUFFED == "10k"
    r1 = next(line for line in LINES if "R1" in line.refs)
    assert r1.value == "10k"
    assert "2k" not in r1.value


def test_bom_covers_every_sheet_instance_ref():
    covered = all_refs()
    for sheet in SHEET_NETS:
        missing = instance_refs(read_sheet(sheet)) - covered
        assert not missing, f"{sheet} refs not in BOM: {missing}"


def test_bom_has_photodiode_and_usb_cc():
    refs = all_refs()
    assert "D4" in refs
    assert "R9" in refs and "R10" in refs
    assert LAYOUT_ONLY_REFS <= refs
    assert "SFH 2704" in emit_markdown()


def test_optics_and_usb_cc_are_on_the_sheets():
    assert not LAYOUT_ONLY_REFS
    power = read_sheet("power")
    sensors = read_sheet("sensors")
    assert {"R9", "R10"} <= instance_refs(power)
    assert {"CC1", "CC2"} <= labels_in(power)
    assert "D4" in instance_refs(sensors)
    assert {"PPG_TXP", "PPG_INP"} <= labels_in(sensors)


def test_sheet_instances_have_bom_footprints():
    from bom import footprint_for

    for sheet in SHEET_NETS:
        text = read_sheet(sheet)
        for ref in instance_refs(text):
            fp = footprint_for(ref)
            assert fp, f"{ref} has no BOM footprint"
            assert fp in text, f"{sheet} {ref} missing footprint {fp}"


def test_bom_has_no_actuators():
    text = emit_markdown().upper()
    for bad in FORBIDDEN_NETS:
        assert bad not in text


def test_cmd_bom_writes_files(tmp_path, monkeypatch):
    import cli as cli_mod

    monkeypatch.setattr(cli_mod, "HARDWARE", tmp_path)
    assert cmd_bom() == 0
    assert (tmp_path / "BOM.md").is_file()
    assert (tmp_path / "BOM.csv").is_file()
    md = (tmp_path / "BOM.md").read_text(encoding="utf-8")
    assert "MCP73831T-2ACI/OT" in md
    assert "AFE4404YZPR" in md


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
