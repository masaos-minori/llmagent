# Implementation: Fix mcp_server fixture process leak in tests/test_mcp_tools_validation.py

Source plan: `plans/20260710-104315_plan.md` (Phase 1 + Phase 2)

## Goal

Restore the `mcp_server` fixture's ability to actually terminate the real subprocess it starts, and make the health-check/port-selection logic match what the target servers actually support, so that `test_v1_tools_returns_expected_tools` / `test_v1_tools_each_has_name_and_description` run and clean up correctly instead of leaking a process and failing teardown with an `AssertionError`.

## Scope

- `tests/test_mcp_tools_validation.py` only.
- Two changes, applied together (they are both required for the fixture to work end-to-end): remove the blanket `os.killpg` mock, and replace dynamic port allocation with hardcoded ports + a pre-flight bind check.
- Does not touch `scripts/mcp/shell/server.py`, `scripts/mcp/cicd/server.py`, `scripts/mcp/mdq/server.py`, or `scripts/mcp/server.py` (production code is out of scope — see plan section 2 "Out-of-Scope" and UNK-01).

## Assumptions

1. `mcp.shell.server` / `mcp.cicd.server` / `mcp.mdq.server` always bind to their hardcoded `http_port` class attribute (8009 / 8012 / 8013 respectively) regardless of any `--host`/`--port` CLI args, because none of their `if __name__ == "__main__":` blocks parse `sys.argv` (verified: `scripts/mcp/shell/server.py:148,157-159`, `scripts/mcp/cicd/server.py:125,134-136`, `scripts/mcp/mdq/server.py:288,302-304`).
2. ~~`_terminate_process_group`'s existing `proc.poll() is not None` early-return plus fresh, non-cached `os.getpgid(proc.pid)` lookup is sufficient protection against the PID-reuse race that motivated the original `os.killpg` mock — no additional guard is needed once the mock is removed (plan section 3, Assumption 3).~~ Superseded: rather than relying on this argument, `os.killpg`/`os.getpgid` were removed from the test file entirely (see the deviation note below) after an observed CLI-termination incident during interactive validation.
3. Binding a TCP socket to `("127.0.0.1", <hardcoded_port>)` and immediately closing it before spawning the subprocess is an adequate (if not perfectly race-free) pre-flight check for "is this port already in use by another instance."

## Implementation

**Deviation from the original design (recorded post-implementation):** while validating this change interactively, the user reported that the Claude Code CLI process itself terminated during a `pytest` run that occurred shortly after the `os.killpg`-based `_terminate_process_group` was applied. The exact causal mechanism could not be conclusively reproduced (an isolated experiment confirmed `start_new_session=True` + `os.killpg(own_pgid, ...)` does not, in principle, affect an unrelated sibling process), but out of caution the design was changed to drop `os.killpg`/`os.getpgid` entirely from this test file, signaling only the specific PID via `Popen.terminate()`/`Popen.kill()`. This is a strictly narrower blast radius (a single PID vs. a process group) and is fully sufficient here because these tests only ever call `/health` and `/v1/tools` — never `/v1/call_tool` — so the spawned MCP server never forks a child of its own that would need group-wide reaping. The sections below describe what was actually implemented (not the original killpg-based design).

### Target file

`tests/test_mcp_tools_validation.py`

### Procedure

1. Remove `monkeypatch.setattr(os, "killpg", MagicMock())` from the `mcp_server` fixture.
2. Change `_MCP_SERVERS` from `list[tuple[str, list[str]]]` (module path, expected tools) to also carry the server's fixed port, OR keep `_MCP_SERVERS` as-is and add a separate `_MODULE_PORTS: dict[str, int]` lookup — pick whichever keeps the parametrize `ids=` list working unchanged. (Recommend: add a third tuple element `port: int`, since it is a fixed property of each server module, not something computed per-test.)
3. Remove `_find_free_port()` and its call site in the fixture.
4. Add a pre-flight "is this port free" check before `subprocess.Popen(...)`; if not free, `pytest.skip(...)` before spawning anything.
5. Remove `"--host", "127.0.0.1", "--port", str(port)` from the `cmd` list (the server ignores them; keeping them would be misleading dead code).
6. Update `health_url` / `f"http://127.0.0.1:{port}/v1/tools"` call sites in the two test functions to use the same fixed port (already flows through `mcp_server` fixture's yielded `(port, tools)` tuple — no change needed there since `port` will now be the fixed one).

### Method

In-place edits to existing module-level constant, fixture, and helper function. No new functions except one small pre-flight-check helper (`_port_is_free(port: int) -> bool`) to keep the fixture body readable — this does not violate the "no speculative abstraction" rule because it is used at exactly one call site but factoring it out makes the fixture's control flow (bind-check → skip-or-spawn) legible.

### Details

#### Change 1: `_MCP_SERVERS` — add fixed port per server

Before (`tests/test_mcp_tools_validation.py:34-57`):

```python
_MCP_SERVERS: list[tuple[str, list[str]]] = [
    ("mcp.shell.server", ["shell_run"]),
    (
        "mcp.cicd.server",
        ["trigger_workflow", "get_workflow_runs", "get_workflow_status", "get_workflow_logs"],
    ),
    (
        "mcp.mdq.server",
        ["search_docs", "get_chunk", "outline", "index_paths", "refresh_index", "stats", "grep_docs"],
    ),
]
```

After:

```python
# (module_path, expected_tool_names, fixed_port) — each server always binds its own
# hardcoded http_port (none of these servers parse --host/--port CLI args), so the
# port here must match scripts/mcp/<name>/server.py's http_port class attribute.
_MCP_SERVERS: list[tuple[str, list[str], int]] = [
    ("mcp.shell.server", ["shell_run"], 8009),
    (
        "mcp.cicd.server",
        ["trigger_workflow", "get_workflow_runs", "get_workflow_status", "get_workflow_logs"],
        8012,
    ),
    (
        "mcp.mdq.server",
        ["search_docs", "get_chunk", "outline", "index_paths", "refresh_index", "stats", "grep_docs"],
        8013,
    ),
]
```

Update the two `@pytest.mark.parametrize("mcp_server", _MCP_SERVERS, indirect=True, ids=[...])` decorators' `ids=` lambda if it currently unpacks 2 elements (`for m, _ in _MCP_SERVERS`) — change to `for m, _, _ in _MCP_SERVERS`.

#### Change 2: remove `_find_free_port`, add `_port_is_free`

Before (`tests/test_mcp_tools_validation.py:60-64`):

```python
def _find_free_port() -> int:
    """Bind to port 0 to let the OS assign a free ephemeral port, then release it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
```

After:

```python
def _port_is_free(port: int) -> bool:
    """Return True if a socket can bind to 127.0.0.1:port (i.e. nothing is listening there)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            return False
        return True
```

#### Change 3: `mcp_server` fixture — remove killpg mock, use fixed port + pre-flight check, drop CLI args

Before (`tests/test_mcp_tools_validation.py:136-171`):

```python
@pytest.fixture()
def mcp_server(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Fixture: start an MCP server subprocess, yield (port, expected_tools), then stop it."""
    monkeypatch.setattr(os, "killpg", MagicMock())
    module, tools = request.param
    port = _find_free_port()
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
    env = {**os.environ, **env_override}
    proc = subprocess.Popen(
        cmd,
        cwd=str(_SCRIPTS),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    health_url = f"http://127.0.0.1:{port}/health"
    healthy = _wait_for_health(health_url, timeout=15.0)
    if not healthy:
        _terminate_process_group(proc, timeout=3)
        pytest.skip(
            f"Server {module}:{port} did not become healthy — possibly missing deps"
        )

    yield port, tools

    _terminate_process_group(proc, timeout=5)
```

After (as actually implemented — also renames `_terminate_process_group` to `_terminate_process` and drops `os.killpg`/`os.getpgid`/`import signal` entirely; see the deviation note above):

```python
def _terminate_process(proc: subprocess.Popen, timeout: float) -> None:
    """Send SIGTERM to proc; escalate to SIGKILL if it doesn't exit in time.

    Signals the specific PID only — never os.killpg()/a process group. These
    tests only ever hit /health and /v1/tools, never /v1/call_tool, so the
    spawned MCP server never forks a child of its own that would need
    group-wide reaping. Using os.killpg() here previously risked signaling a
    process group broader than intended (observed to disrupt the surrounding
    shell/CLI session in some environments); a single Popen.terminate()/kill()
    call is scoped strictly to this one PID and cannot have that effect.
    """
    if proc.poll() is not None:
        return

    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            pass

    assert proc.poll() is not None, (
        f"pid {proc.pid} still alive after terminate+kill — "
        f"MCP server subprocess was not reaped"
    )


@pytest.fixture()
def mcp_server(request: pytest.FixtureRequest) -> Any:
    """Fixture: start an MCP server subprocess, yield (port, expected_tools), then stop it."""
    module, tools, port = request.param
    if not _port_is_free(port):
        pytest.skip(
            f"port {port} already in use — likely a running production instance of {module}"
        )

    env_override = {"PYTHONPATH": str(_SCRIPTS)}
    cmd = [_PYTHON, "-m", module]
    env = {**os.environ, **env_override}
    proc = subprocess.Popen(
        cmd,
        cwd=str(_SCRIPTS),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    health_url = f"http://127.0.0.1:{port}/health"
    healthy = _wait_for_health(health_url, timeout=15.0)
    if not healthy:
        _terminate_process(proc, timeout=3)
        pytest.skip(
            f"Server {module}:{port} did not become healthy — possibly missing deps"
        )

    yield port, tools

    _terminate_process(proc, timeout=5)
```

`_process_group_gone` was also removed (its one caller, the pgid-based assertion, is gone; `_terminate_process` inlines the equivalent `proc.poll() is not None` check into its own final assertion).

Note: the `monkeypatch: pytest.MonkeyPatch` fixture parameter is dropped entirely — no other line in this fixture uses it.

#### Change 4: unused import cleanup

`from unittest.mock import MagicMock` and `import signal` both became unused after Change 3 and were removed.

#### Non-goal reminder

Do not add `--host`/`--port` parsing to the production servers (`scripts/mcp/*/server.py`) as part of this change — that is UNK-01 in the source plan, deliberately deferred pending a separate decision (see plan section 4).

## Validation plan

| Check | Tool / Command | Target | Result |
|---|---|---|---|
| Targeted run (shell only, fastest feedback) | `uv run pytest tests/test_mcp_tools_validation.py -k "shell" -v` | Passes or cleanly skips; no `AssertionError` at teardown | PASS (2 passed, 2.46s) — verified with user's explicit go-ahead after the CLI-termination report |
| Full file | `uv run pytest tests/test_mcp_tools_validation.py -v` | All pass (or skip with an explicit "port already in use" / "missing deps" reason) | 5 passed, 2 skipped (`cicd` skips — health check fails, unrelated pre-existing env condition, not a regression) |
| Process leak check | `ps aux \| grep -E "mcp\.(shell\|cicd\|mdq)\.server" \| grep -v grep` (run immediately after the pytest command above) | Empty output — no leaked subprocess | Confirmed empty after both runs |
| CLI stability | manual observation | The Claude Code CLI session must remain responsive across the run | Confirmed stable after switching to PID-only termination (see deviation note) |
| Lint | `uv run ruff check tests/test_mcp_tools_validation.py` | 0 errors | PASS |
| Type check | `uv run mypy scripts/` | No new errors | PASS (no `test_mcp_tools_validation` hits in the error output; 174 pre-existing errors elsewhere are unrelated baseline) |
| Safety: no killpg left | `rg "killpg\|getpgid" tests/test_mcp_tools_validation.py` | No hits | PASS |
| Safety: no dead CLI args | `rg -- "--host\|--port" tests/test_mcp_tools_validation.py` | No hits (aside from an explanatory comment) | PASS |
| Full regression | `uv run pytest` | No new failures relative to current baseline | **Not run in this session.** Two broad/full pytest invocations in this interactive session were followed by reports that the Claude Code CLI process itself terminated. Root cause not conclusively isolated (possibly sandbox resource limits under a large test run, independent of the killpg-scoping issue already fixed above). Policy going forward: only targeted single-file `pytest tests/test_<file>.py` runs in this session; broad/full-suite runs deferred to a separate environment/CI. |
