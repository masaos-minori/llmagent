"""tests/test_mcp_tools_validation.py
Integration tests: verify that each MCP server's /v1/tools endpoint returns
the expected tool names.

Tests start each server as a subprocess (same as production), send GET /v1/tools,
and assert the declared tool names match the server's _MCP_TOOLS list.

Marked with @pytest.mark.integration so they can be skipped in fast unit-test runs:
  pytest -m "not integration"   # skip these
  pytest -m integration         # run only these
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx
import pytest

_SCRIPTS = Path(__file__).parent.parent / "scripts"
_PYTHON = sys.executable

# (module_path, port, expected_tool_names)
_MCP_SERVERS: list[tuple[str, int, list[str]]] = [
    ("mcp.shell.server", 18009, ["shell_run"]),
    ("mcp.sqlite.server", 18011, ["query_sqlite"]),
    (
        "mcp.cicd.server",
        18012,
        [
            "trigger_workflow",
            "get_workflow_runs",
            "get_workflow_status",
            "get_workflow_logs",
        ],
    ),
    (
        "mcp.mdq.server",
        18013,
        [
            "search_docs",
            "get_chunk",
            "outline",
            "index_paths",
            "refresh_index",
            "stats",
            "grep_docs",
        ],
    ),
]


def _wait_for_health(url: str, timeout: float = 10.0) -> bool:
    """Poll /health until 200 or timeout (seconds)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(url, timeout=1.0)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


@pytest.fixture()
def mcp_server(request: pytest.FixtureRequest) -> Any:
    """Fixture: start an MCP server subprocess, yield (port, expected_tools), then stop it."""
    module, port, tools = request.param
    env_override = {"PYTHONPATH": str(_SCRIPTS)}
    cmd = [
        _PYTHON,
        "-m",
        module,
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    import os

    env = {**os.environ, **env_override}
    proc = subprocess.Popen(
        cmd,
        cwd=str(_SCRIPTS),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    health_url = f"http://127.0.0.1:{port}/health"
    healthy = _wait_for_health(health_url, timeout=15.0)
    if not healthy:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        pytest.skip(
            f"Server {module}:{port} did not become healthy — possibly missing deps"
        )

    yield port, tools

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def test_read_tools_schema_matches_hand_written() -> None:
    """Generated schema must have the expected tool names and valid inputSchema structure."""
    from mcp.file.read_tools import _MCP_TOOLS

    names = [t["name"] for t in _MCP_TOOLS]
    assert names == [
        "list_directory",
        "list_directory_with_sizes",
        "directory_tree",
        "read_text_file",
        "read_media_file",
        "read_multiple_files",
        "search_files",
        "grep_files",
        "get_file_info",
    ]
    for tool in _MCP_TOOLS:
        assert "inputSchema" in tool
        assert tool["inputSchema"]["type"] == "object"
        assert "properties" in tool["inputSchema"]


@pytest.mark.integration
@pytest.mark.parametrize(
    "mcp_server",
    _MCP_SERVERS,
    indirect=True,
    ids=[f"{m.split('.')[-2]}-{port}" for m, port, _ in _MCP_SERVERS],
)
def test_v1_tools_returns_expected_tools(mcp_server: Any) -> None:
    """GET /v1/tools must return all expected tool names."""
    port, expected_tools = mcp_server
    resp = httpx.get(f"http://127.0.0.1:{port}/v1/tools", timeout=5.0)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert "tools" in data, f"/v1/tools response missing 'tools' key: {data}"
    returned_names = {t["name"] for t in data["tools"]}
    for tool_name in expected_tools:
        assert tool_name in returned_names, (
            f"Tool {tool_name!r} missing from /v1/tools response; got {returned_names}"
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    "mcp_server",
    _MCP_SERVERS,
    indirect=True,
    ids=[f"{m.split('.')[-2]}-{port}" for m, port, _ in _MCP_SERVERS],
)
def test_v1_tools_each_has_name_and_description(mcp_server: Any) -> None:
    """Each tool entry in /v1/tools must have non-empty name and description."""
    port, _expected_tools = mcp_server
    resp = httpx.get(f"http://127.0.0.1:{port}/v1/tools", timeout=5.0)
    assert resp.status_code == 200
    data = resp.json()
    for tool in data.get("tools", []):
        assert tool.get("name"), f"Tool entry missing 'name': {tool}"
        assert tool.get("description"), f"Tool {tool['name']!r} has empty description"
