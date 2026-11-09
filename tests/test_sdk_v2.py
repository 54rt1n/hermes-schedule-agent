"""SDK-v2 stdio uses the ordinary launcher, typed contracts and profile-owned disk."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from mcp import StdioServerParameters
from mcp.client import Client

ROOT = Path(__file__).resolve().parents[1]


def cli(data, *args):
    result = subprocess.run(
        [
            str(ROOT / ".venv/bin/python"),
            "-m",
            "schedule_cli",
            "--data-dir",
            str(data),
            "--json",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize("mode", ["legacy", "auto"])
def test_real_launcher_crud_readback_restart_and_profile_isolation(tmp_path, mode):
    data = tmp_path / "profile-a"
    other = tmp_path / "profile-b"
    cli(data, "init", "--timezone", "America/Chicago")
    cli(other, "init", "--timezone", "UTC")
    for directory in [data, other]:
        (directory / "config.json").write_text(
            json.dumps({"default_timezone": "America/Chicago", "log_level": "ERROR"})
        )

    async def phase(directory, write=False):
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-I", str(ROOT / "scripts/serve.py")],
            env={
                k: v
                for k, v in dict(os.environ, PLUGIN_DATA=str(directory)).items()
                if k != "PYTHONPATH"
            },
            cwd=str(tmp_path),
        )
        async with Client(parameters, mode=mode) as client:
            tools = {tool.name: tool for tool in (await client.list_tools()).tools}
            assert {
                "create_event",
                "query_schedule",
                "create_task",
                "complete_task",
                "create_contact",
                "query_contacts",
            } <= tools.keys()
            assert tools["create_contact"].input_schema["additionalProperties"] is False
            assert (
                tools["update_event"].input_schema["$defs"]["EventPatch"]["additionalProperties"]
                is False
            )

            async def call(name, values):
                result = await client.call_tool(name, values)
                assert not result.is_error, result
                parsed = json.loads(result.content[0].text)
                assert parsed["success"], parsed
                assert result.structured_content == {"result": parsed}
                return parsed

            if write:
                contact = await call(
                    "create_contact", {"name": "V2 contact", "email": "sdk@example.com"}
                )
                changed = await call(
                    "update_contact", {"id": contact["contact_id"], "patch": {"phone": "555-0100"}}
                )
                assert changed["contact"]["phone"] == "555-0100"
                task = await call("create_task", {"title": "V2 task"})
                assert (await call("complete_task", {"id": task["task_id"]}))["task"][
                    "state"
                ] == "DONE"
                event = await call(
                    "create_event",
                    {
                        "event": {
                            "kind": "timed",
                            "title": "V2 meeting",
                            "start_time": "2030-01-07T10:00:00",
                            "end_time": "2030-01-07T11:00:00",
                        }
                    },
                )
                assert event["event"]["time_zone"] == "America/Chicago"
                assert event["event"]["start_time"] == "2030-01-07T16:00:00+00:00"
                assert (await call("delete_event", {"id": event["event_id"]}))["success"]
                malformed = await client.call_tool(
                    "create_contact", {"name": "Rejected", "unknown": True}
                )
                assert malformed.is_error
                nested = await client.call_tool(
                    "update_event", {"id": event["event_id"], "patch": {"titel": "Rejected"}}
                )
                assert nested.is_error
            contacts = await call("query_contacts", {"name": "V2 contact"})
            tasks = await call("query_schedule", {"resource": "tasks", "state": "DONE"})
            return contacts, tasks

    created = asyncio.run(phase(data, write=True))
    assert created[0]["count"] == created[1]["count"] == 1
    assert (
        cli(data, "contacts", "get", created[0]["contacts"][0]["id"])["contact"]["phone"]
        == "555-0100"
    )
    assert asyncio.run(phase(data)) == created
    absent = asyncio.run(phase(other))
    assert absent[0]["count"] == absent[1]["count"] == 0
    assert (data / "schedule-agent.db").is_file() and (other / "schedule-agent.db").is_file()


def test_launcher_refuses_missing_data_without_installing_or_creating_state(tmp_path):
    result = subprocess.run(
        [sys.executable, "-I", str(ROOT / "scripts/serve.py")],
        env={k: v for k, v in os.environ.items() if k not in {"PLUGIN_DATA", "PYTHONPATH"}},
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode != 0
    assert "absolute, profile-scoped PLUGIN_DATA" in result.stderr
    assert list(tmp_path.iterdir()) == []


HOST_PROBE = r"""
import asyncio,json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import hermes_bootstrap
from hermes_cli import plugins
from hermes_cli.plugins import PluginManager
from tools.mcp_tool_discovery import _connect_server
from tools.mcp_tool_handlers import _call_tool_racing_stdio_death
from hermes_constants import get_hermes_home

async def run():
    home=Path(os.environ['HERMES_HOME'])
    plugins.get_bundled_plugins_dir=lambda: home/'empty-bundled'
    from hermes_cli.plugin_validate import validate_plugin_dir
    report=validate_plugin_dir(home/'plugins/hermes-schedule-agent')
    assert report.ok,report.to_dict()
    manager=PluginManager(scope_key=str(home))
    plugins.get_plugin_manager=lambda: manager
    manager.discover_and_load()
    loaded=manager._plugins['hermes-schedule-agent']
    assert loaded.enabled and not loaded.error,loaded.error
    expected_skills={'schedule-agent','schedule-events','schedule-tasks','schedule-contacts'}
    assert {entry['bare_name'] for entry in manager._plugin_skills.values()} >= expected_skills
    server_name,config=next(iter(manager.get_portable_mcp_servers().items()))
    data=Path(config['env']['PLUGIN_DATA'])
    assert data.is_relative_to(home/'plugin-data')
    data.mkdir(parents=True,exist_ok=True)
    (data/'config.json').write_text('{"log_level":"ERROR"}')
    server=await _connect_server(server_name,config)
    try:
        catalog=await server.session.list_tools()
        expected_tools={'create_task','query_schedule','create_contact'}
        assert expected_tools <= {tool.name for tool in catalog.tools}
        async def call(name,args):
            result=await _call_tool_racing_stdio_death(server,server_name,name,args)
            assert not result.is_error,result
            value=json.loads(result.content[0].text)
            assert value['success'],value
            return value
        made=await call('create_task',{'title':'Disposable host task'})
        queried=await call('query_schedule',{'id':made['task_id'],'resource':'tasks'})
        assert queried['count']==1 and queried['tasks'][0]['title']=='Disposable host task'
        print(json.dumps({'profile':str(home),'data':str(data),'task_id':made['task_id'],'sdk':__import__('importlib.metadata').metadata.version('mcp')}))
    finally:
        await server.shutdown()
        manager.unload()
        assert manager.get_portable_mcp_servers()=={}
asyncio.run(run())
"""


def test_disposable_hermes_discovers_skill_mcp_and_executes_profile_scoped_tool(tmp_path):
    host_python = os.environ.get("SCHEDULE_HOST_TEST_PYTHON")
    if not host_python:
        pytest.skip("Set SCHEDULE_HOST_TEST_PYTHON to a PM-built Hermes test interpreter")
    home = tmp_path / "hermes-profile"
    home.mkdir()
    (home / "plugins").mkdir()
    (home / "plugins/hermes-schedule-agent").symlink_to(ROOT, target_is_directory=True)
    (home / "config.yaml").write_text(
        json.dumps({"plugins": {"enabled": ["hermes-schedule-agent"]}})
    )
    script = tmp_path / "host_probe.py"
    script.write_text(HOST_PROBE)
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"VIRTUAL_ENV", "PYTHONPATH", "HERMES_TRANSCRIPTION_DEPENDENCY_PATH"}
    }
    env.update(
        HOME=str(tmp_path / "os-home"),
        HERMES_HOME=str(home),
        HERMES_RUNTIME_DIR=str(tmp_path / "runtime"),
        HERMES_DISABLE_LAZY_INSTALLS="1",
    )
    result = subprocess.run(
        [host_python, str(script), str(ROOT.parent / "metroscale-hermes")],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = json.loads(result.stdout.strip().splitlines()[-1])
    assert evidence["sdk"] == "2.3.0"
    assert Path(evidence["data"]).is_relative_to(home)
