"""Exercise real MCP imports, tool calls and persistence in temporary data only."""
import asyncio
import json
import os
from pathlib import Path
import sys
import subprocess
import tempfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def connect(data, create=False):
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-I", str(Path(__file__).with_name("serve.py")), "--worker"],
        env={**os.environ, "PLUGIN_DATA": data},
    )
    async with stdio_client(parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert {"query_schedule", "create_event", "update_event", "delete_event", "create_task", "update_task", "delete_task", "complete_task", "create_contact", "query_contacts", "update_contact", "delete_contact"} == {tool.name for tool in tools.tools}
            if create:
                result = await session.call_tool("create_contact", {"name": "Plugin smoke fixture", "email": "fixture@example.com"})
                assert json.loads(result.content[0].text)["success"], result
                result = await session.call_tool("create_task", {"title": "Smoke task"})
                task = json.loads(result.content[0].text)
                assert task["success"], task
                result = await session.call_tool("complete_task", {"id": task["task_id"]})
                assert json.loads(result.content[0].text)["task"]["state"] == "DONE"
            agenda = await session.call_tool("query_schedule", {"view": "occurrences", "date": "2030-01-07"})
            agenda_payload = json.loads(agenda.content[0].text)
            assert agenda_payload["success"], agenda_payload
            assert agenda_payload["count"] == 1, agenda_payload
            assert agenda_payload["tasks"] == []
            assert agenda_payload["events"][0]["kind"] == "all_day"
            result = await session.call_tool("query_contacts", {"name": "Plugin smoke fixture"})
            payload = json.loads(result.content[0].text)
            assert payload["success"], payload
            assert len(payload["contacts"]) == 1, payload
            result = await session.call_tool("query_schedule", {"resource": "tasks", "state": "DONE"})
            tasks = json.loads(result.content[0].text)
            assert tasks["count"] == 1, tasks


async def main():
    with tempfile.TemporaryDirectory(prefix="hermes-schedule-agent-smoke-") as data:
        Path(data, "config.json").write_text('{"log_level":"ERROR"}')
        subprocess.run(
            [sys.executable, "-m", "schedule_cli", "--data-dir", data, "--json", "init"],
            check=True, capture_output=True, text=True, timeout=30,
        )
        subprocess.run(
            [sys.executable, "-m", "schedule_cli", "--data-dir", data, "--json",
             "events", "create", "--data",
             '{"kind":"all_day","title":"Smoke day","start":"2030-01-07"}'],
            check=True, capture_output=True, text=True, timeout=30,
        )
        await asyncio.wait_for(connect(data, create=True), timeout=30)
        await asyncio.wait_for(connect(data), timeout=30)
        assert Path(data, "schedule-agent.db").is_file()
    print("PASS: twelve-tool MCP discovery, agenda read, local contact write/query, persistence across child restarts")


if __name__ == "__main__":
    asyncio.run(main())
