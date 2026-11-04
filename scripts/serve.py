"""Launch upstream Schedule Agent in an external runtime with profile-owned data."""

import asyncio
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path


def load_config(data):
    from schedule_core.storage import read_config

    return read_config(data).model_dump()


async def worker(data):
    # Upstream setup_logging writes to stdout, which belongs to MCP framing.
    # Construct its handlers under redirection; they retain stderr afterwards.
    with redirect_stdout(sys.stderr):
        from schedule_core.core.logging_config import setup_logging
        from schedule_core.core.settings import Settings
        from schedule_mcp.server import setup_mcp_server

        settings = Settings(
            _env_file=None,
            database_url="sqlite+aiosqlite:///"
            + (data / "schedule-agent.db").as_posix(),
            **load_config(data),
        )
        setup_logging(settings)
        server = await setup_mcp_server(settings)
    await server.run_stdio_async()


def main():
    data_value = os.environ.get("PLUGIN_DATA")
    if not data_value or not Path(data_value).is_absolute():
        raise SystemExit("Hermes must supply an absolute, profile-scoped PLUGIN_DATA")
    data = Path(data_value)
    data.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:] == ["--worker"]:
        asyncio.run(worker(data))
        return
    root = Path(__file__).resolve().parents[1]
    python = (
        root
        / ".venv"
        / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    )
    if not python.is_file():
        raise SystemExit(
            "Schedule Agent runtime missing; run python3.12 scripts/setup_runtime.py in the plugin directory"
        )
    os.execv(
        str(python), [str(python), "-I", str(Path(__file__).resolve()), "--worker"]
    )


if __name__ == "__main__":
    main()
