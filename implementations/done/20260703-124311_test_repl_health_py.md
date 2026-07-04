## Goal

Extend `tests/test_repl_health.py` to cover `_probe_mcp_health_detail()` with three new test cases while keeping all existing `probe_mcp_health()` tests intact.

## Scope

- In-Scope:
  - Add `_probe_mcp_health_detail` to the import from `agent.repl_health`
  - Add a new `TestProbeMcpHealthDetail` class with three test cases:
    1. HTTP 200 with no `restart_recommended` field → `reachable=True, restart_recommended=False`
    2. HTTP 503 + `restart_recommended=true` in body → `reachable=True, restart_recommended=True`
    3. Connection exception → `reachable=False`
- Out-of-Scope:
  - Changes to existing `TestProbeMcpHealth` class
  - Adding tests for `_watchdog_check_http` (covered in `test_watchdog.py`)

## Assumptions

1. `_probe_mcp_health_detail` is importable from `agent.repl_health` after Step 4 is complete.
2. The existing `TestProbeMcpHealth` class is unchanged.
3. `httpx.AsyncClient.get` is mocked via `AsyncMock`; the mock `resp` object needs a `.json()` method returning the desired body dict.
4. For the exception case, `http.get.side_effect = httpx.ConnectError("fail")` matches the existing pattern in `TestProbeMcpHealth`.

## Implementation

### Target file

`/home/masaos/llmagent/tests/test_repl_health.py`

### Procedure

1. Open `/home/masaos/llmagent/tests/test_repl_health.py`.
2. Update the import of `probe_mcp_health` (line 15-21) to also import `_probe_mcp_health_detail`:
   ```python
   from agent.repl_health import (
       _check_tool_definitions,
       _probe_mcp_health_detail,
       audit_security_defaults,
       check_readiness,
       check_workflow_definition,
       probe_mcp_health,
   )
   ```
3. After the `TestProbeMcpHealth` class (around line 63), insert the new test class:

```python
# ── _probe_mcp_health_detail() ────────────────────────────────────────────────


class TestProbeMcpHealthDetail:
    @pytest.mark.asyncio
    async def test_reachable_true_restart_false_when_200_no_body_field(self) -> None:
        """HTTP 200 with no restart_recommended field: reachable=True, restart_recommended=False."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"status": "ok", "ready": True}
        http.get = _async_result(resp)

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is True
        assert result.status_code == 200
        assert result.restart_recommended is False
        assert result.operator_action_required is False

    @pytest.mark.asyncio
    async def test_reachable_true_restart_true_when_503_and_restart_recommended(self) -> None:
        """HTTP 503 + restart_recommended=true in body: reachable=True, restart_recommended=True."""
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 503
        resp.json.return_value = {
            "status": "degraded",
            "ready": False,
            "restart_recommended": True,
            "operator_action_required": False,
        }
        http.get = _async_result(resp)

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is True
        assert result.status_code == 503
        assert result.restart_recommended is True
        assert result.operator_action_required is False

    @pytest.mark.asyncio
    async def test_reachable_false_on_connection_exception(self) -> None:
        """Connection failure: reachable=False, status_code=None."""
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get.side_effect = httpx.ConnectError("fail")

        result = await _probe_mcp_health_detail(http, "http://localhost:8000")

        assert result.reachable is False
        assert result.status_code is None
        assert result.restart_recommended is False
        assert result.operator_action_required is False
        assert result.body == {}
```

4. No other changes to the file.

### Method

- `resp.json.return_value = {...}` configures the mock so `resp.json()` (a regular method call, not async) returns the body dict.
- The `_async_result(resp)` helper already defined at line 24 returns an `AsyncMock` whose call returns `resp`; reuse it for the new tests.
- All existing tests in `TestProbeMcpHealth` remain unchanged and must continue to pass.

### Details

- File: `tests/test_repl_health.py`
- Existing `_async_result` helper (line 24-27) returns `AsyncMock` with `.return_value = value`; the new tests can reuse this.
- `resp.json` is a regular (non-async) method on `httpx.Response`; `MagicMock()` gives it a `.return_value` to set.
- The new `TestProbeMcpHealthDetail` class is placed immediately after `TestProbeMcpHealth` for logical grouping.

## Validation plan

```bash
# Run the extended test file
uv run pytest tests/test_repl_health.py -v

# Specifically the new class
uv run pytest tests/test_repl_health.py::TestProbeMcpHealthDetail -v

# Lint
uv run ruff check tests/test_repl_health.py
```

Expected outcomes:
- All three new `TestProbeMcpHealthDetail` cases pass.
- All existing `TestProbeMcpHealth` cases still pass.
- No ruff lint errors.
