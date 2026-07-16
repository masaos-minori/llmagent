"""tests/integration/test_mcp_transport_crash.py

Integration tests: Agent Loop <-> MCP Servers, stdio transport crash modes.

Companion to test_agent_mcp_integration.py (TC-A, HTTP-only). These tests
exercise the raw subprocess/pipe boundary directly since no agent-layer
StdioLifecycleManager exists in this codebase today (see plan Assumption 3,
plans/20260716-135105_plan.md) -- assertions target what any future stdio
transport implementation would need to survive.

Run 5x for flakiness check (subprocess timing is the main risk):
    for i in {1..5}; do uv run pytest tests/integration/test_mcp_transport_crash.py -v --timeout=30; done
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import httpx
import pytest
import respx


async def _hanging_stdio_server() -> asyncio.subprocess.Process:
    """Start a subprocess that reads one line from stdin, then sleeps forever."""
    script = "import sys, time\nsys.stdin.readline()\ntime.sleep(3600)\n"
    proc = await asyncio.create_subprocess_exec(
        "python",
        "-c",
        script,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    return proc


@pytest.mark.asyncio
async def test_d01_stdio_killed_mid_response_yields_eof() -> None:
    """Subprocess killed mid-response -- reader must see EOF, not a hang or exception."""
    script = (
        "import sys, time\n"
        "sys.stdin.readline()\n"
        "sys.stdout.write('partial')\n"
        "sys.stdout.flush()\n"
        "time.sleep(3600)\n"
    )
    proc = await asyncio.create_subprocess_exec(
        "python",
        "-c",
        script,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    try:
        proc.stdin.write(b'{"id": "1"}\n')
        await proc.stdin.drain()
        await asyncio.sleep(0.1)  # let it write and flush before kill
        proc.kill()
        await proc.wait()
        # Draining the remaining buffered bytes must end in EOF (b""), never a hang.
        while True:
            chunk = await asyncio.wait_for(proc.stdout.read(4096), timeout=2.0)
            if chunk == b"":
                break
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()


@pytest.mark.asyncio
async def test_d02_stdio_truncated_json_then_close() -> None:
    script = (
        "import sys\n"
        "sys.stdin.readline()\n"
        'sys.stdout.write(\'{"id": "x", "resu\')\n'  # deliberately truncated
        "sys.stdout.flush()\n"
    )
    proc = await asyncio.create_subprocess_exec(
        "python",
        "-c",
        script,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    try:
        proc.stdin.write(b'{"id": "1"}\n')
        await proc.stdin.drain()
        line = await asyncio.wait_for(proc.stdout.readline(), timeout=2.0)
        with pytest.raises(json.JSONDecodeError):
            json.loads(line.decode())
    finally:
        if proc.returncode is None:
            proc.kill()
        await asyncio.wait_for(proc.wait(), timeout=5.0)


@pytest.mark.asyncio
async def test_d03_stdio_hang_times_out_and_process_is_reaped() -> None:
    """Subprocess never responds -- a bounded wait_for times out; process is still reaped."""
    proc = await _hanging_stdio_server()
    assert proc.stdin is not None
    assert proc.stdout is not None
    try:
        proc.stdin.write(b'{"id": "1"}\n')
        await proc.stdin.drain()
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(proc.stdout.readline(), timeout=1.0)
    finally:
        proc.kill()
        await asyncio.wait_for(proc.wait(), timeout=5.0)
        assert proc.returncode is not None


@pytest.mark.asyncio
async def test_d04_stdio_buffered_output_after_kill() -> None:
    script = (
        "import sys\n"
        "sys.stdin.readline()\n"
        "sys.stdout.write('partial output')\n"
        "sys.stdout.flush()\n"
        "import time; time.sleep(3600)\n"
    )
    proc = await asyncio.create_subprocess_exec(
        "python",
        "-c",
        script,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    try:
        proc.stdin.write(b'{"id": "1"}\n')
        await proc.stdin.drain()
        await asyncio.sleep(0.1)  # let it write and flush before kill
        proc.kill()
        await proc.wait()
        # Must not raise -- either buffered bytes or EOF, never an exception.
        data = await asyncio.wait_for(proc.stdout.read(), timeout=2.0)
        assert isinstance(data, bytes)
    finally:
        if proc.returncode is None:
            proc.kill()
            await proc.wait()


@pytest.mark.asyncio
async def test_d05_http_timeout_races_lifecycle_termination() -> None:
    """An in-flight ToolExecutor.execute() HTTP call and a concurrent
    HttpServerLifecycleManager._terminate_with_timeout() call must both
    resolve independently -- termination completes within its escalation
    window, and the in-flight call resolves to a TransportError, not a hang.
    """
    from agent.http_lifecycle import HttpServerLifecycleManager
    from shared.mcp_config import McpServerConfig, StartupMode, TransportType
    from shared.tool_executor import ToolExecutor

    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:19099",
        cmd=[],
        tool_names=["_d05_tool"],
        startup_mode=StartupMode.PERSISTENT,
    )

    async def _timeout_after_brief_delay(request: httpx.Request) -> httpx.Response:
        # Genuinely overlaps with the concurrent terminate_task below, then
        # raises directly rather than relying on respx's mock transport to
        # honor httpx's client-level read timeout (it does not).
        await asyncio.sleep(0.2)
        raise httpx.ReadTimeout("simulated read timeout", request=request)

    def _make_running_proc(pid: int = 424242) -> MagicMock:
        proc = MagicMock()
        proc.pid = pid
        proc.stderr = None
        proc.poll = MagicMock(
            side_effect=lambda: (
                0 if (proc.terminate.called or proc.kill.called) else None
            )
        )
        proc.wait = MagicMock(return_value=0)
        return proc

    with respx.mock(base_url="http://127.0.0.1:19099", assert_all_called=False) as mock:
        mock.post("/v1/call_tool").mock(side_effect=_timeout_after_brief_delay)
        async with httpx.AsyncClient() as http:
            executor = ToolExecutor(
                http=http,
                cache_ttl=0,
                server_configs={"d05_server": cfg},
            )
            executor._resolver.resolve = lambda _: "d05_server"

            call_task = asyncio.create_task(executor.execute("_d05_tool", {}))

            mgr = HttpServerLifecycleManager()
            proc = _make_running_proc()
            terminate_task = asyncio.create_task(
                mgr._terminate_with_timeout(proc, "d05_server", timeout=1.0)
            )

            result, _ = await asyncio.wait_for(
                asyncio.gather(call_task, terminate_task), timeout=3.0
            )

    assert result.is_error
    assert result.error_type == "transport"
    proc.terminate.assert_called_once()
