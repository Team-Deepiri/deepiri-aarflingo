"""Runtime CLI."""
from __future__ import annotations

import typer
import uvicorn

from app.platform import ensure_lan_access, is_wsl, wsl_mode
from app.server import lan_ip

app = typer.Typer(help="AARFLingo live runtime")


@app.command()
def serve(
    host: str = typer.Option(default="0.0.0.0", help="Bind host (0.0.0.0 = LAN)"),
    port: int = typer.Option(default=8765, help="Bind port"),
) -> None:
    """Serve the live API + built studio UI. Binds all interfaces so any
    device on the same Wi-Fi can open http://<lan-ip>:<port> (rohomieo-style)."""
    if is_wsl():
        status = ensure_lan_access(port)
        typer.echo(f"  WSL LAN setup ({status})")
        if "needs-admin" in status:
            typer.echo(
                f"  \u26a0 Windows Firewall blocked inbound. Open an elevated PowerShell"
                f" and run once:\n"
                f"      New-NetFirewallRule -DisplayName AARFLingo-{port} -Direction"
                f" Inbound -Protocol TCP -LocalPort {port} -Action Allow\n"
            )
    if host in ("0.0.0.0", "::"):
        typer.echo(f"  Hosting on Wi-Fi:  http://{lan_ip()}:{port}   (LAN)")
        typer.echo(f"  Local:             http://127.0.0.1:{port}")
    else:
        typer.echo(f"  Serving on:        http://{host}:{port}")
    uvicorn.run("app.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
