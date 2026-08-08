"""WSL / bridge helpers for runtime."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
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


def wsl_mode() -> str | None:
    """'mirrored' | 'nat' | None (not WSL)."""
    if not is_wsl():
        return None
    host = windows_host_ip()
    try:
        out = subprocess.run(
            ["ip", "-o", "-4", "addr", "show"], capture_output=True, text=True, timeout=3
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return "nat"
    # Mirrored mode mirrors the Windows host gateway into WSL loopback.
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[3].split("/")[0] == host:
            return "mirrored"
    return "nat"


def wsl_primary_ip() -> str:
    """First non-loopback WSL IPv4 (used for NAT portproxy connectaddress)."""
    try:
        out = subprocess.run(
            ["ip", "-o", "-4", "addr", "show"], capture_output=True, text=True, timeout=3
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return "127.0.0.1"
    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        ip = parts[3].split("/")[0]
        if ip.startswith(("127.", "169.254.")):
            continue
        return ip
    return "127.0.0.1"


def _win_powershell() -> str | None:
    return shutil.which("powershell.exe")


def _run_ps_script(script: str, args: list[str]) -> tuple[int, str]:
    """Run a PowerShell script on the Windows side (no elevation)."""
    exe = _win_powershell()
    if exe is None:
        return 2, "no powershell.exe (not WSL?)"
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False) as f:
        f.write(script)
        ps_path = f.name
    wargs = subprocess.run(
        ["wslpath", "-w", ps_path], capture_output=True, text=True, check=False
    )
    win_path = wargs.stdout.strip() if wargs.returncode == 0 else ps_path
    proc = subprocess.run(
        [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", win_path, *args],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    Path(ps_path).unlink(missing_ok=True)
    out = (proc.stdout + proc.stderr).strip()
    # A rule is only "added" when the script prints its sentinel marker.
    if proc.returncode == 0 and "FAILED:" in out:
        return 1, out
    return proc.returncode, out


def _run_ps_script_elevated(script: str) -> tuple[int, str]:
    """Run a self-contained PowerShell script elevated via a UAC prompt."""
    exe = _win_powershell()
    if exe is None:
        return 2, "no powershell.exe (not WSL?)"
    out_file = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    out_path = out_file.name
    out_file.close()
    w_out = subprocess.run(
        ["wslpath", "-w", out_path], capture_output=True, text=True, check=False
    )
    win_out = w_out.stdout.strip() if w_out.returncode == 0 else out_path
    wrapped = f'& {{ {script} }} *> "{win_out}"\n'
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False) as f:
        f.write(wrapped)
        ps_path = f.name
    wargs = subprocess.run(
        ["wslpath", "-w", ps_path], capture_output=True, text=True, check=False
    )
    win_path = wargs.stdout.strip() if wargs.returncode == 0 else ps_path
    argv = [
        exe,
        "-NoProfile",
        "-Command",
        (
            "Start-Process -FilePath 'powershell.exe' -Verb RunAs -Wait -ArgumentList "
            f"'-NoProfile -ExecutionPolicy Bypass -File {win_path}'"
        ),
    ]
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=90, check=False)
    except subprocess.TimeoutExpired:
        Path(ps_path).unlink(missing_ok=True)
        Path(out_path).unlink(missing_ok=True)
        return 1, "elevation timeout (UAC not approved)"
    Path(ps_path).unlink(missing_ok=True)
    try:
        result = Path(out_path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        result = ""
    Path(out_path).unlink(missing_ok=True)
    # The firewall script itself doesn't set a failure exit code; check sentinels.
    if "FAILED:" in result or "denied" in result.lower():
        return 1, result
    return proc.returncode, result


def _ensure_firewall_rule(port: int, elevated: bool = False) -> tuple[bool, str]:
    """Add a Windows Firewall inbound rule for the port (returns ok, message)."""
    script = rf"""
$port = {port}
$name = "AARFLingo-$port"
if (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue) {{
    Write-Output "EXISTS"
    exit 0
}}
try {{
    New-NetFirewallRule -DisplayName $name -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow -Profile Any -ErrorAction Stop | Out-Null
    Write-Output "ADDED"
    exit 0
}} catch {{
    Write-Output ("FAILED: " + $_.Exception.Message)
    exit 1
}}
"""
    if elevated:
        return _run_ps_script_elevated(script)
    return _run_ps_script(script, [str(port)])


def _ensure_portproxy(port: int) -> tuple[bool, str]:
    """Add a netsh portproxy host->WSL for NAT mode (returns ok, message)."""
    wsl_ip = wsl_primary_ip()
    script = r"""
param([int]$port, [string]$wslIp)
$existing = netsh interface portproxy show v4tov4 | Select-String "$port"
if ($existing) {
    Write-Output "EXISTS"
    exit 0
}
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=$port connectaddress=$wslIp connectport=$port
if ($LASTEXITCODE -ne 0) {
    Write-Output "FAILED: netsh portproxy add failed"
    exit 1
}
Write-Output "ADDED"
exit 0
"""
    return _run_ps_script(script, [str(port), wsl_ip])


def ensure_lan_access(port: int) -> str:
    """Open Windows Firewall (and portproxy in NAT mode) so the LAN can reach
    the runtime from the Windows side. Idempotent — no-op when not WSL.

    Prompts UAC once on first run if the firewall rule is missing."""
    mode = wsl_mode()
    if mode is None:
        return "not-wsl"
    steps: list[str] = [f"wsl-{mode}"]
    ok, msg = _ensure_firewall_rule(port)
    if ok == 0 and "FAILED:" not in msg:
        steps.append(f"firewall:{msg.splitlines()[0].lower()}")
    else:
        ok, msg = _ensure_firewall_rule(port, elevated=True)
        if ok == 0 and "FAILED:" not in msg:
            steps.append(f"firewall:{msg.splitlines()[0].lower()} (elevated)")
        else:
            steps.append("firewall:needs-admin")
    if mode == "nat":
        ok2, msg2 = _ensure_portproxy(port)
        steps.append(f"portproxy:{msg2.splitlines()[0][:30].lower() if ok2 == 0 else 'needs-admin'}")
    return " | ".join(steps)
