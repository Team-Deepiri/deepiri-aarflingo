#!/usr/bin/env python3
"""Collar schematic craftsmanship: status / verify / next / bom."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bom import LINES, all_refs, emit_csv, emit_markdown
from nets import (
    BOARD,
    FORBIDDEN_NETS,
    GPIO,
    NEXT_STEPS,
    REQUIRED_PARTS,
    SHEET_NETS,
    STRAPPING_DO_NOT_USE_LIVE,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HARDWARE = REPO_ROOT / "hardware" / BOARD
PINS_H = HARDWARE / "pins.h"

LABEL_RE = re.compile(r'\((?:global_)?label\s+"([^"]+)"')
REF_RE = re.compile(r'\(property\s+"Reference"\s+"([^"]+)"')
INSTANCE_REF_RE = re.compile(r"^[A-Z]+\d+$")
PIN_DEFINE_RE = re.compile(r"#define\s+PIN_([A-Z0-9_]+)\s+(\d+)")
LAYOUT_ONLY_REFS: set[str] = set()
MECH_REFS = {"BT1", "TAG1"}


def sheet_path(name: str) -> Path:
    return HARDWARE / f"{name}.kicad_sch"


def read_sheet(name: str) -> str:
    path = sheet_path(name)
    if not path.is_file():
        raise FileNotFoundError(f"missing sheet {path}")
    return path.read_text(encoding="utf-8")


def labels_in(text: str) -> set[str]:
    return set(LABEL_RE.findall(text))


def refs_in(text: str) -> set[str]:
    return {r for r in REF_RE.findall(text) if not r.startswith("#")}


def instance_refs(text: str) -> set[str]:
    return {r for r in refs_in(text) if INSTANCE_REF_RE.match(r)}


def cmd_status() -> int:
    print(f"board: {BOARD}")
    print(f"path:  {HARDWARE}")
    if not HARDWARE.is_dir():
        print("missing hardware/collar-reva/", file=sys.stderr)
        return 1
    root = HARDWARE / "collar-reva.kicad_sch"
    print(f"  [{'x' if root.is_file() else ' '}] {root.name}")
    for name in SHEET_NETS:
        path = sheet_path(name)
        ok = path.is_file()
        extra = ""
        if ok:
            text = path.read_text(encoding="utf-8")
            extra = f"  labels={len(labels_in(text))}  refs={len(refs_in(text))}"
        print(f"  [{'x' if ok else ' '}] {path.name}{extra}")
    print("gpio:")
    for net, gpio in GPIO.items():
        print(f"  GPIO{gpio:<3} {net}")
    return 0


def parse_pins_h() -> dict[str, int]:
    if not PINS_H.is_file():
        raise FileNotFoundError(f"missing {PINS_H}")
    found: dict[str, int] = {}
    for match in PIN_DEFINE_RE.finditer(PINS_H.read_text(encoding="utf-8")):
        found[match.group(1)] = int(match.group(2))
    return found


def cmd_verify() -> int:
    errors: list[str] = []

    for net, gpio in GPIO.items():
        if gpio in STRAPPING_DO_NOT_USE_LIVE:
            errors.append(f"{net} on strapping GPIO{gpio}")

    try:
        pins = parse_pins_h()
    except FileNotFoundError as exc:
        errors.append(str(exc))
        pins = {}
    for net, gpio in GPIO.items():
        header = pins.get(net)
        if header != gpio:
            errors.append(f"pins.h PIN_{net}={header!r} != nets.py {gpio}")

    for sheet, required in SHEET_NETS.items():
        try:
            text = read_sheet(sheet)
        except FileNotFoundError as exc:
            errors.append(str(exc))
            continue
        present = labels_in(text)
        missing = [n for n in required if n not in present]
        if missing:
            errors.append(f"{sheet}: missing labels {missing}")
        for label in present:
            upper = label.upper()
            for bad in FORBIDDEN_NETS:
                if bad in upper:
                    errors.append(f"{sheet}: forbidden net {label}")

        refs = refs_in(text)
        for ref in REQUIRED_PARTS.get(sheet, ()):
            if ref not in refs:
                errors.append(f"{sheet}: missing required part {ref}")
        bom_refs = all_refs()
        for ref in instance_refs(text):
            if ref not in bom_refs:
                errors.append(f"{sheet}: {ref} missing from BOM")

    for line in LINES:
        for ref in line.refs:
            if ref in LAYOUT_ONLY_REFS or ref in MECH_REFS:
                continue
            if line.sheet not in SHEET_NETS:
                continue
            try:
                present = instance_refs(read_sheet(line.sheet))
            except FileNotFoundError as exc:
                errors.append(str(exc))
                break
            if ref not in present:
                errors.append(f"BOM {ref} not on {line.sheet} sheet")

    if errors:
        print("FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("OK  collar nets, GPIO, pins.h, ethics denylist")
    return 0


def cmd_next() -> int:
    print("Next (collar Rev-A):")
    for i, step in enumerate(NEXT_STEPS, 1):
        print(f"  {i}. {step}")
    return 0


def cmd_bom() -> int:
    md = HARDWARE / "BOM.md"
    csv_path = HARDWARE / "BOM.csv"
    md.write_text(emit_markdown(), encoding="utf-8")
    csv_path.write_text(emit_csv(), encoding="utf-8")
    print(f"wrote {md}")
    print(f"wrote {csv_path}")
    print(f"lines: {len(LINES)}  refs: {len(all_refs())}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="aarf_sch", description=__doc__)
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=("status", "verify", "next", "bom"),
    )
    args = parser.parse_args(argv)
    if args.command == "status":
        return cmd_status()
    if args.command == "verify":
        return cmd_verify()
    if args.command == "bom":
        return cmd_bom()
    return cmd_next()


if __name__ == "__main__":
    sys.exit(main())
