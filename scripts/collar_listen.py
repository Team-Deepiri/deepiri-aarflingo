#!/usr/bin/env python3
"""Subscribe to aarf-collar 1 Hz CBOR notifies. Observational only.

Optional --runtime POSTs each frame to the existing /infer/collar HTTP
(same studio family as /infer/audio — not a fourth protocol).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "firmware" / "collar" / "host"))

from decode import decode_collar_cbor  # noqa: E402

from core.collar_features import write_collar_latest  # noqa: E402

ADV_NAME = "aarf-collar"
NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


def post_collar_frame(runtime: str, frame: dict, timeout: float = 2.0) -> None:
    url = runtime.rstrip("/") + "/infer/collar"
    data = json.dumps(frame).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req, timeout=timeout).read()


def handle_frame(data: bytearray, runtime: str | None) -> dict:
    frame = decode_collar_cbor(bytes(data))
    write_collar_latest(ROOT, frame)
    print(json.dumps(frame, sort_keys=True), flush=True)
    if runtime:
        try:
            post_collar_frame(runtime, frame)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"runtime post failed: {exc}", file=sys.stderr)
    return frame


async def _listen(timeout: float, runtime: str | None) -> int:
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
        await client.start_notify(NOTIFY_UUID, lambda _h, data: handle_frame(data, runtime))
        print("subscribed; Ctrl-C to stop", file=sys.stderr)
        while True:
            await asyncio.sleep(1)


def main() -> int:
    p = argparse.ArgumentParser(description="Decode aarf-collar BLE notifies")
    p.add_argument("--timeout", type=float, default=12.0)
    p.add_argument(
        "--runtime",
        default=None,
        help="POST each 1 Hz frame to {url}/infer/collar (e.g. http://127.0.0.1:8000)",
    )
    args = p.parse_args()
    try:
        return asyncio.run(_listen(args.timeout, args.runtime))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
