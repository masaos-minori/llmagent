# Implementation: Phase 3 — Fix tests/test_mcp_tools_validation.py

## Goal

Eliminate real `os.killpg` calls in `test_mcp_tools_validation.py` by replacing the `_process_group_gone` assertion's `os.killpg(pgid, 0)` probe with a `proc.poll()`-based check, and by patching `os.killpg` in the `mcp_server` fixture scope.

## Scope

- `tests/test_mcp_tools_validation.py` only.
- Three changes: `_process_group_gone` signature/call, `mcp_server` fixture monkeypatch, remove unused import if `import signal` becomes unused.

## Assumptions

1. `proc` is always available at the assertion site where `_process_group_gone` is called (L134-138 of the current file). Verified: both callers (`_terminate_process_group` and the inline use) have `proc` as a local variable.
2. `monkeypatch.setattr` on `os.killpg` used inside a `@pytest.fixture()` persists into the fixture teardown phase, because monkeypatch reverts after the fixture function returns (not after `yield`).

## Implementation

### Target file

`tests/test_mcp_tools_validation.py`

### Procedure

1. Change `_process_group_gone(pgid: int) -> bool` → `_process_group_gone(proc: subprocess.Popen) -> bool`, replacing `os.killpg(pgid, 0)` with `proc.poll() is not None`.
2. Update the call at L135 to pass `proc` instead of `pgid`.
3. Add `monkeypatch: pytest.MonkeyPatch` parameter to `mcp_server` fixture and call `monkeypatch.setattr(os, "killpg", MagicMock())` at the start.
4. If `import signal` becomes unused after changes, add `# noqa: F401` or clean up appropriately (check whether `signal.SIGTERM` and `signal.SIGKILL` are still used elsewhere in the file).

### Method

In-place edits to existing functions. No new functions.

### Details

#### Change 1: `_process_group_gone` — switch from killpg probe to proc.poll

Before (L80-88):

```python
def _process_group_gone(pgid: int) -> bool:
    """Return True if no process in pgid is alive (signal 0 probe)."""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    return False
```

After:

```python
def _process_group_gone(proc: subprocess.Popen) -> bool:
    """Return True if proc has exited (proxy for process-group cleanliness)."""
    return proc.poll() is not None
```

#### Change 2: Call site of `_process_group_gone` (L134-138)

Before:

```python
    if pgid is not None:
        assert _process_group_gone(pgid), (
            f"process group {pgid} still has live members after "
            f"terminate+kill — MCP server subprocess tree was not fully reaped"
        )
```

After:

```python
    if pgid is not None:
        assert _process_group_gone(proc), (
            f"process group {pgid} still has live members after "
            f"terminate+kill — MCP server subprocess tree was not fully reaped"
        )
```

#### Change 3: `mcp_server` fixture — patch `os.killpg` (L141-175)

Before:

```python
@pytest.fixture()
def mcp_server(request: pytest.FixtureRequest) -> Any:
    """Fixture: start an MCP server subprocess, yield (port, expected_tools), then stop it."""
    module, tools = request.param
    ...
```

After:

```python
@pytest.fixture()
def mcp_server(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Any:
    """Fixture: start an MCP server subprocess, yield (port, expected_tools), then stop it."""
    monkeypatch.setattr(os, "killpg", MagicMock())
    module, tools = request.param
    ...
```

This patches `os.killpg` for the entire fixture lifetime (setup, test, teardown). The skip-path `_terminate_process_group(proc, timeout=3)` (L168) and the teardown `_terminate_process_group(proc, timeout=5)` (L175) both call `os.killpg` via the patched reference.

#### Change 4 (if needed): Clean up unused imports

If `import signal` becomes unused after changes, add a `# noqa: F401` comment. However, `signal.SIGTERM` and `signal.SIGKILL` are still used in `_terminate_process_group` (L113, L124), so `import signal` remains used and no change is needed.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Phase 3 fix | `uv run pytest tests/test_mcp_tools_validation.py -v -k "test_v1_tools or test_read_tools"` | all pass |
| Full file | `uv run pytest tests/test_mcp_tools_validation.py -v` | all pass |
| Lint | `uv run ruff check tests/test_mcp_tools_validation.py` | 0 errors |
| Safety: no killpg(, 0) | `rg "killpg" tests/test_mcp_tools_validation.py` | only inside `_terminate_process_group` (guarded by try/except) |
