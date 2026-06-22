"""Runtime CLI."""
from __future__ import annotations

import typer
import uvicorn

app = typer.Typer(help="AARFLingo live runtime")


@app.command()
def serve(
    host: str = typer.Option(default="127.0.0.1", help="Bind host"),
    port: int = typer.Option(default=8765, help="Bind port"),
) -> None:
    uvicorn.run("app.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
