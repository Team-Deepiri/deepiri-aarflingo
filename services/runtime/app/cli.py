"""Runtime CLI."""
from __future__ import annotations

import typer
import uvicorn

app = typer.Typer(help="AARFLingo live runtime")


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    uvicorn.run("app.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    app()
