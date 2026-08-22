#!/usr/bin/env python3
"""Subscribe to aarf-collar 1 Hz CBOR notifies. Observational only."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "firmware" / "collar" / "host"))

from decode import decode_collar_cbor  # noqa: E402

ADV_NAME = "aarf-collar"
NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


def _print_frame(data: bytearray) -> None:
    frame = decode_collar_cbor(bytes(data))
    print(json.dumps(frame, sort_keys=True), flush=True)


async def _listen(timeout: float) -> int:
    try:
        from bleak import BleakClient, BleakScanner
    except ImportError:
        print("install bleak to scan: pip install bleak", file=sys.stderr)
        return 2

    print(f"scanning for {ADV_NAME}…", file=sys.stderr)
    dev = await BleakScanner.find_device_by_name(ADV_NAME, timeout=timeout)
    if dev is None:
        print("no aarf-collar found", file=sys.stderr)
        return 1

    async with BleakClient(dev) as client:
        await client.start_notify(NOTIFY_UUID, lambda _h, data: _print_frame(data))
        print("subscribed; Ctrl-C to stop", file=sys.stderr)
        while True:
            await asyncio.sleep(1)


def main() -> int:
    p = argparse.ArgumentParser(description="Decode aarf-collar BLE notifies")
    p.add_argument("--timeout", type=float, default=12.0)
    args = p.parse_args()
    try:
        return asyncio.run(_listen(args.timeout))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
