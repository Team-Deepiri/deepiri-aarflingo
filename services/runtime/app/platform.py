"""WSL / bridge helpers for runtime."""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEFAULT_BRIDGE_PORT = 8766

# Root of the repo (parents: app -> runtime -> services -> repo root).
_REPO_ROOT: Path = Path(__file__).resolve().parents[3]


def is_wsl() -> bool:
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def platform_name() -> str:
    """'wsl' | 'windows' | 'macos' | 'linux' | 'unknown'."""
    if is_wsl():
        return "wsl"
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    return "unknown"


def local_lan_ip() -> str:
    """Best-effort primary LAN IPv4 (e.g. 192.168.x.x) for this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        pass
    return "127.0.0.1"


def windows_host_ip() -> str:
    """IP the Windows host is reachable at from inside WSL (nameserver/gateway)."""
    try:
        for line in Path("/etc/resolv.conf").read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("nameserver"):
                return line.split()[1]
    except (OSError, IndexError):
        pass
    return "127.0.0.1"


def windows_bridge_host_ip() -> str:
    """IP WSL uses to reach a service bound on the Windows host.

    Mirrored mode shares the Windows loopback into WSL, so 127.0.0.1 is the
    reliable address (the nameserver gateway can be unroutable for host-bound
    listeners in that mode). NAT mode reaches the host at the nameserver IP."""
    if not is_wsl():
        return "127.0.0.1"
    if wsl_mode() == "mirrored":
        return "127.0.0.1"
    return windows_host_ip()


def bridge_stream_url(port: int = DEFAULT_BRIDGE_PORT) -> str:
    """URL of the MJPEG bridge stream as reachable from this process.

    On WSL the bridge runs on the Windows host, addressed by the address that
    actually routes to it (loopback in mirrored mode, nameserver in NAT mode).
    On native OSes it listens on 0.0.0.0 so localhost works from this machine."""
    if is_wsl():
        return f"http://{windows_bridge_host_ip()}:{port}/video/stream"
    return f"http://127.0.0.1:{port}/video/stream"


def client_bridge_stream_url(port: int = DEFAULT_BRIDGE_PORT) -> str:
    """URL the browser/phone on the LAN can use for the bridge MJPEG stream.

    For WSL the phone reaches the bridge at the Windows LAN IP directly
    (the bridge binds 0.0.0.0 on the Windows host), not the WSL-internal
    nameserver address."""
    if is_wsl():
        host = windows_lan_ip() or local_lan_ip()
        return f"http://{host}:{port}/video/stream"
    return f"http://{local_lan_ip()}:{port}/video/stream"


def bridge_health_url(port: int = DEFAULT_BRIDGE_PORT) -> str:
    return bridge_stream_url(port).replace("/video/stream", "/health")


def probe_bridge(port: int = DEFAULT_BRIDGE_PORT, timeout: float = 2.5) -> bool:
    """True when the MJPEG bridge health endpoint responds ok."""
    import urllib.request

    url = bridge_health_url(port)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            if r.status != 200:
                return False
            return b"\"status\": \"ok\"" in r.read(4096)
    except Exception:
        return False


def _start_bridge_windows(port: int) -> str:
    """Auto-start the webcam bridge on the Windows host from WSL.

    WSL cannot enumerate USB webcams, so the bridge (Flask + OpenCV MJPEG)
    must run on the Windows side. Launched detached via powershell.exe so the
    runtime doesn't block; the ps1 handles python + pip install itself."""
    exe = _win_powershell()
    if exe is None:
        return "auto-start-failed (no powershell.exe from WSL)"
    ps1 = _REPO_ROOT / "scripts" / "webcam" / "start_webcam_bridge.ps1"
    if not ps1.exists():
        return f"auto-start-failed (missing {ps1})"
    wpath = subprocess.run(
        ["wslpath", "-w", str(ps1)], capture_output=True, text=True, check=False
    )
    win_ps1 = wpath.stdout.strip() if wpath.returncode == 0 else str(ps1)
    cmd = (
        "Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList "
        f"'-NoProfile','-ExecutionPolicy','Bypass','-File','{win_ps1}','-Port',{port}"
    )
    try:
        proc = subprocess.run(
            [exe, "-NoProfile", "-Command", cmd], capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return "auto-start-failed (powershell launch error)"
    # The phone hits the bridge at the Windows LAN IP:<port>, so make sure
    # Windows Firewall doesn't drop that inbound traffic either.
    _ensure_firewall_rule(port)
    time.sleep(1.5)
    # Give the bridge (and its pip install) a few seconds to come up.
    seen = None
    for _ in range(6):
        if probe_bridge(port):
            seen = "ok"
            break
    return "auto-started-windows" if seen else "auto-start-sent (bridge still starting)"


def _start_bridge_native() -> str:
    """Auto-start the bridge locally on Linux/macOS/Windows using the repo script."""
    sh_path = _REPO_ROOT / "scripts" / "wsl-webcam-bridge.sh"
    py_path = _REPO_ROOT / "scripts" / "webcam" / "webcam_bridge.py"
    if sh_path.exists():
        argv = ["bash", str(sh_path)]
    else:
        argv = [sys.executable, str(py_path), "--source", "0", "--port", str(DEFAULT_BRIDGE_PORT), "--host", "0.0.0.0"]
    try:
        log = open(_REPO_ROOT / "artifacts" / "webcam-bridge.log", "a", encoding="utf-8")
    except OSError:
        log = open(os.devnull, "w", encoding="utf-8")
    try:
        subprocess.Popen(
            argv,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )
    except (OSError, subprocess.SubprocessError):
        return "auto-start-failed"
    time.sleep(2.0)
    seen = None
    for _ in range(6):
        if probe_bridge():
            seen = "ok"
            break
        time.sleep(1.0)
    return "auto-started-native" if seen else "auto-start-sent (bridge starting)"


def ensure_webcam_bridge(port: int = DEFAULT_BRIDGE_PORT) -> str:
    """Auto-detect platform/OS and make sure the webcam bridge is running.

    Returns a status string like 'bridge:ok', 'bridge:auto-started-windows',
    'bridge:not-reachable'. Idempotent — no-op when already reachable."""
    if probe_bridge(port):
        return "bridge:ok"
    platform = platform_name()
    if platform == "wsl":
        status = _start_bridge_windows(port)
    else:
        status = _start_bridge_native()
    if "sent" in status or "started" in status:
        return f"bridge:{status}"
    return f"bridge:{status}"


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


def windows_lan_ip() -> str | None:
    """Real Windows-side LAN IPv4, queried from Windows itself rather than
    inferred from WSL's interface list — mirrored mode surfaces WSL-internal
    gateway/DNS addresses alongside the real LAN IP, and naive first-match
    can pick the wrong one. Resolved as the IP bound to whichever interface
    owns the default route, so it works regardless of adapter names/count
    (VPNs, virtual adapters, etc. are excluded automatically since they
    aren't the lowest-metric default-route interface)."""
    exe = shutil.which("powershell.exe")
    if exe is None:
        return None
    cmd = (
        "$if = (Get-NetRoute -DestinationPrefix '0.0.0.0/0' -ErrorAction SilentlyContinue "
        "| Sort-Object RouteMetric | Select-Object -First 1 -ExpandProperty InterfaceIndex); "
        "Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $if -ErrorAction SilentlyContinue "
        "| Where-Object { $_.PrefixOrigin -ne 'WellKnown' } "
        "| Select-Object -First 1 -ExpandProperty IPAddress"
    )
    try:
        proc = subprocess.run(
            [exe, "-NoProfile", "-Command", cmd],
            capture_output=True, text=True, timeout=10, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    ip = proc.stdout.strip()
    return ip or None


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


def _ensure_portproxy(port: int, listen_addr: str, connect_addr: str) -> tuple[bool, str]:
    """Add a netsh portproxy listen_addr->connect_addr on Windows (returns ok, message)."""
    script = r"""
param([int]$port, [string]$listenAddr, [string]$connectAddr)
$existing = netsh interface portproxy show v4tov4 | Select-String "$listenAddr\s+$port"
if ($existing) {
    Write-Output "EXISTS"
    exit 0
}
netsh interface portproxy add v4tov4 listenaddress=$listenAddr listenport=$port connectaddress=$connectAddr connectport=$port
if ($LASTEXITCODE -ne 0) {
    Write-Output "FAILED: netsh portproxy add failed"
    exit 1
}
Write-Output "ADDED"
exit 0
"""
    return _run_ps_script(script, [str(port), listen_addr, connect_addr])


def _ensure_portproxy_elevated(port: int, listen_addr: str, connect_addr: str) -> tuple[bool, str]:
    """Elevated fallback for _ensure_portproxy (netsh portproxy needs admin)."""
    script = f"""
$port = {port}
$listenAddr = "{listen_addr}"
$connectAddr = "{connect_addr}"
$existing = netsh interface portproxy show v4tov4 | Select-String "$listenAddr\\s+$port"
if ($existing) {{
    Write-Output "EXISTS"
    exit 0
}}
netsh interface portproxy add v4tov4 listenaddress=$listenAddr listenport=$port connectaddress=$connectAddr connectport=$port
if ($LASTEXITCODE -ne 0) {{
    Write-Output "FAILED: netsh portproxy add failed"
    exit 1
}}
Write-Output "ADDED"
exit 0
"""
    return _run_ps_script_elevated(script)


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
        listen_addr, connect_addr = "0.0.0.0", wsl_primary_ip()
    else:
        # Mirrored mode: WSL's interface list includes the real Windows LAN
        # IP, but Windows' mirrored inbound forwarding to that IP can be
        # unreliable (observed broken on machines with active VPN/virtual
        # adapters). localhostForwarding still works, so proxy the LAN IP
        # to Windows' own loopback rather than trusting mirrored forwarding.
        listen_addr, connect_addr = windows_lan_ip() or wsl_primary_ip(), "127.0.0.1"
    ok2, msg2 = _ensure_portproxy(port, listen_addr, connect_addr)
    if ok2 == 0 and "FAILED:" not in msg2:
        steps.append(f"portproxy:{msg2.splitlines()[0][:30].lower()}")
    else:
        ok2, msg2 = _ensure_portproxy_elevated(port, listen_addr, connect_addr)
        if ok2 == 0 and "FAILED:" not in msg2:
            steps.append(f"portproxy:{msg2.splitlines()[0][:30].lower()} (elevated)")
        else:
            steps.append("portproxy:needs-admin")
    return " | ".join(steps)
