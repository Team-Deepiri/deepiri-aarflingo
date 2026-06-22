"""WSL / bridge helpers for runtime."""
from __future__ import annotations

from pathlib import Path

DEFAULT_BRIDGE_PORT = 8766


def is_wsl() -> bool:
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def windows_host_ip() -> str:
    try:
        for line in Path("/etc/resolv.conf").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("nameserver"):
                return line.split()[1]
    except (OSError, IndexError):
        pass
    return "127.0.0.1"


def default_bridge_stream_url(port: int = DEFAULT_BRIDGE_PORT) -> str:
    host = windows_host_ip() if is_wsl() else "127.0.0.1"
    return f"http://{host}:{port}/video/stream"
