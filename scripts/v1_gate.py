#!/usr/bin/env python3
"""Write the v1.0 readiness report. Exit 0 unless --require-bar."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.v1_gate import collect_report, write_outputs  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-bar",
        action="store_true",
        help="exit 1 unless dog-split ≥95% on ≥3 dogs and paper + Jetson hub are ready",
    )
    args = parser.parse_args()
    report = collect_report(ROOT)
    write_outputs(ROOT, report)
    print(json.dumps({k: report[k] for k in ("bar_met", "blockers", "bar")}, indent=2))
    if args.require_bar and not report["bar_met"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
