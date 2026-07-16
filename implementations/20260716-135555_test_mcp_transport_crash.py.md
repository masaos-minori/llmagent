# Implementation: tests/integration/test_mcp_transport_crash.py (new — stdio subprocess crash/hang chaos tests, D01–D05)

Source plan: `plans/20260716-135105_plan.md`

## Goal

Add integration tests exercising the raw stdio subprocess/pipe boundary
directly (kill mid-response, truncated JSON, hang, post-kill buffered
output, HTTP timeout racing lifecycle termination) — a gap the existing
`tests/integration/test_agent_mcp_integration.py` (HTTP-only, `respx`
-mocked) and `tests/integration/test_robustness_chaos.py` (3D, also
HTTP-only) never reach, since no agent-layer `StdioLifecycleManager`
exists in this codebase today (per the source plan's Assumption 3).

## Scope

**In:**
- Create `tests/integration/test_mcp_transport_crash.py` with 5 test
  functions (D01–D05, per the source plan's Design §2 table and §4
  Example Test Skeleton):
  1. `test_d01_stdio_killed_mid_response_yields_eof` — subprocess killed
     mid-response; reader must see EOF (`b""`), not a hang or exception.
  2. `test_d02_stdio_truncated_json_then_close` — subprocess writes
     truncated JSON then exits; caller's JSON decode raises
     `json.JSONDecodeError`, not a hang.
  3. `test_d03_stdio_hang_times_out_and_process_is_reaped` — subprocess
     never responds; a bounded `asyncio.wait_for(..., timeout=1.0)` raises
     `asyncio.TimeoutError`; `proc.kill()` + `proc.wait()` still completes
     (no zombie).
  4. `test_d04_stdio_buffered_output_after_kill` — after `proc.kill()`, a
     read on stdout either returns any already-buffered bytes or empty
     (EOF) — must not raise an unhandled exception.
  5. `test_d05_http_timeout_races_lifecycle_termination` — an in-flight
     `ToolExecutor.execute()` HTTP call races
     `HttpServerLifecycleManager._terminate_with_timeout()`; termination
     completes within its SIGTERM→SIGKILL escalation window, and the
     in-flight call resolves to a `TransportError`, not a hang.

**Out:**
- Any modification to `tests/integration/test_agent_mcp_integration.py`,
  `tests/integration/test_robustness_chaos.py`, or `tests/test_lifecycle.py`
  — read-only references for patterns to reuse (see Assumptions), not
  edited.
- Any production code change (`scripts/agent/http_lifecycle.py`,
  `scripts/shared/tool_executor.py`, etc.) — this plan is test-only.
- Implementing a new `StdioLifecycleManager` — explicitly out of scope
  per the source plan's Assumption 3; tests target the subprocess/pipe
  boundary directly, not a nonexistent agent-layer abstraction.

## Assumptions

1. `tests/integration/conftest.py`'s existing `stdio_echo_server` fixture
   (lines 17-35) demonstrates the exact subprocess-construction pattern
   (`asyncio.create_subprocess_exec` with `stdin=PIPE, stdout=PIPE`) to
   follow for all D-series tests — reuse its style, do not invent a
   different subprocess-launching convention.
2. D01–D04 use inline Python one-liner scripts passed via `python -c`
   (matching `stdio_echo_server`'s own technique) rather than separate
   `.py` fixture files — no new files beyond the test module itself.
3. D05 reuses `tests/test_lifecycle.py`'s existing `_make_mock_proc`
   helper (per the source plan's Implementation Step 2) — import or
   replicate its exact construction, do not duplicate similar-but-different
   mock-process logic. Verify the helper's exact import path
   (`tests/test_lifecycle.py`, module-level or nested function) before
   writing D05; if it is not importable as-is (e.g. a local closure), copy
   its logic verbatim into this new file with a comment noting the source.
4. UNK-01 from the source plan (whether `respx.mock()` and real
   `asyncio.create_subprocess_exec` coexist safely in one test under
   `asyncio_mode = "auto"`) must be resolved before D05 is finalized — per
   the source plan's Implementation Step 1, write a throwaway smoke test
   combining both first; if no conflict is found, fold the confirmation
   directly into D05 without keeping a separate smoke-test file.
5. `pytest.mark.asyncio` is used explicitly on every async test function,
   matching 100% of existing async tests in this codebase's convention
   (confirmed during planning), even though `asyncio_mode = "auto"` in
   `pyproject.toml` would run them without the marker.

## Implementation

### Target file

`tests/integration/test_mcp_transport_crash.py` (new file)

### Procedure

1. Create the file with the module docstring and helper function shown in
   the source plan's Design §4 Example Test Skeleton — use it verbatim as
   the starting point for `_hanging_stdio_server()` and
   `test_d03_stdio_hang_times_out_and_process_is_reaped`:
   ```python
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

   import pytest


   async def _hanging_stdio_server() -> asyncio.subprocess.Process:
       """Start a subprocess that reads one line from stdin, then sleeps forever."""
       script = (
           "import sys, time\n"
           "sys.stdin.readline()\n"
           "time.sleep(3600)\n"
       )
       proc = await asyncio.create_subprocess_exec(
           "python",
           "-c",
           script,
           stdin=asyncio.subprocess.PIPE,
           stdout=asyncio.subprocess.PIPE,
       )
       return proc
   ```
2. Add `test_d03_stdio_hang_times_out_and_process_is_reaped` exactly as
   given in the Example Test Skeleton (D03 body).
3. Add `test_d01_stdio_killed_mid_response_yields_eof` exactly as given in
   the Example Test Skeleton (D01 body).
4. Add `test_d02_stdio_truncated_json_then_close`:
   ```python
   @pytest.mark.asyncio
   async def test_d02_stdio_truncated_json_then_close() -> None:
       script = (
           "import sys\n"
           "sys.stdin.readline()\n"
           "sys.stdout.write('{\"id\": \"x\", \"resu')\n"  # deliberately truncated
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
           proc.kill()
           await asyncio.wait_for(proc.wait(), timeout=5.0)
   ```
5. Add `test_d04_stdio_buffered_output_after_kill`:
   ```python
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
   ```
6. Add `test_d05_http_timeout_races_lifecycle_termination` — resolve
   Assumption 3/4 first (confirm `_make_mock_proc`'s exact location in
   `tests/test_lifecycle.py` and confirm `respx` + real subprocess
   coexistence per UNK-01), then implement combining:
   - a `respx`-mocked HTTP endpoint that never responds (or responds after
     a delay exceeding the test's timeout budget) for an in-flight
     `ToolExecutor.execute()` call, launched as a background `asyncio.Task`;
   - a call to `HttpServerLifecycleManager._terminate_with_timeout()` (or
     an equivalent constructed instance, following `tests/test_lifecycle.py`'s
     existing setup pattern) against a mock process while the HTTP call is
     still in flight;
   - assert the in-flight call's `asyncio.Task` resolves to a
     `TransportError`-shaped `ToolCallResult` within a bounded time, and
     that termination itself does not hang.

### Method

Five independent async test functions using real `asyncio.create_subprocess_exec`
subprocesses (D01–D04) and one hybrid test combining `respx` HTTP mocking
with a real/mocked lifecycle manager (D05) — no new fixtures in this file
itself (fixtures are added to `conftest.py` separately per the companion
doc, though this file's initial implementation may use local helper
functions as shown in the Example Test Skeleton before any refactor to
shared fixtures).

### Details

- Every subprocess-launching test must have a `finally` block that kills
  and reaps the process — no test may leave a zombie or orphaned process
  behind, even on assertion failure.
- Use `asyncio.wait_for(..., timeout=N)` for every read that could
  theoretically hang — never a bare blocking read with no timeout.
- Keep timeouts generous (1-2s) per the source plan's Risk R-1 mitigation
  — do not use sub-100ms timeouts that could false-fail under CI load.
- Do not use `time.sleep()` (blocking) anywhere in async test bodies —
  use `await asyncio.sleep()`.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| New tests pass | `uv run pytest tests/integration/test_mcp_transport_crash.py -v` | 5 passed |
| No hang | `uv run pytest tests/integration/test_mcp_transport_crash.py -v --timeout=30` | completes well under 30s per test |
| Flakiness check | `for i in {1..5}; do uv run pytest tests/integration/test_mcp_transport_crash.py -v --timeout=30; done` | 5/5 clean runs |
| No zombie processes | manual: `ps aux \| grep python` immediately after the test run | no orphaned `python -c ...` processes remain |
| Lint | `uv run ruff check tests/integration/test_mcp_transport_crash.py` | 0 errors |
| Type check | `uv run mypy tests/integration/test_mcp_transport_crash.py` | no new errors |
| Existing suite unaffected | `uv run pytest tests/integration/test_agent_mcp_integration.py tests/integration/test_robustness_chaos.py -v` | all 30 existing tests (TC-A + 3A-3D) still pass unchanged |
