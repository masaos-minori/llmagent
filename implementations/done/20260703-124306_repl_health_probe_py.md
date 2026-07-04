## Goal

Add `_probe_mcp_health_detail()` internal helper to `agent/repl_health.py` that returns a `McpHealthProbeResult`, while preserving `probe_mcp_health()` as a backward-compatible `bool` wrapper.

## Scope

- In-Scope:
  - Import `McpHealthProbeResult` from `agent.shared.health_models`
  - Add `async def _probe_mcp_health_detail(http, base_url) -> McpHealthProbeResult`
  - Update `probe_mcp_health()` to delegate to `_probe_mcp_health_detail()` and return `.reachable and status_code == 200`
- Out-of-Scope:
  - Changes to `_watchdog_check_http()` (covered in Step 5)
  - Changes to `watchdog_loop()` (covered in Step 6)
  - Any other function in `repl_health.py`

## Assumptions

1. `probe_mcp_health(http, base_url) -> bool` is called from `_watchdog_check_http()` (line 306) and from `tests/test_repl_health.py`. After this step, `probe_mcp_health` delegates to `_probe_mcp_health_detail` and must still return `True` on HTTP 200, `False` otherwise — identical behavior to the current implementation.
2. `_probe_mcp_health_detail` must never raise; it catches `httpx.HTTPError`, `OSError`, and `TimeoutError` (same exceptions as current `probe_mcp_health`).
3. Body JSON parse uses `resp.json()` which can raise `json.JSONDecodeError` or `ValueError`; these must be caught with a fallback to empty body and `restart_recommended=False, operator_action_required=False`.
4. `McpHealthProbeResult` is available after Step 3 is complete.

## Implementation

### Target file

`/home/masaos/llmagent/scripts/agent/repl_health.py`

### Procedure

1. Open `/home/masaos/llmagent/scripts/agent/repl_health.py`.
2. Add `McpHealthProbeResult` to the import from `agent.shared.health_models` (currently line 22):
   ```python
   from agent.shared.health_models import HealthCheckResult, McpHealthProbeResult, ServiceWarning
   ```
3. After the existing `probe_mcp_health()` function (currently ends around line 42), insert the new helper:

```python
async def _probe_mcp_health_detail(
    http: httpx.AsyncClient, base_url: str
) -> McpHealthProbeResult:
    """Probe /health and return a structured McpHealthProbeResult.

    Never raises. On network failure returns reachable=False with status_code=None.
    On JSON parse failure falls back to restart_recommended=False, operator_action_required=False.
    """
    try:
        resp = await http.get(f"{base_url}/health", timeout=5.0)
    except (httpx.HTTPError, OSError, TimeoutError):
        return McpHealthProbeResult(
            reachable=False,
            status_code=None,
            restart_recommended=False,
            operator_action_required=False,
            body={},
        )
    try:
        body: dict[str, object] = resp.json()
    except (ValueError, Exception):  # noqa: BLE001 — health check must not fail on body parse errors
        body = {}
    restart_recommended: bool = bool(body.get("restart_recommended", False))
    operator_action_required: bool = bool(body.get("operator_action_required", False))
    return McpHealthProbeResult(
        reachable=True,
        status_code=resp.status_code,
        restart_recommended=restart_recommended,
        operator_action_required=operator_action_required,
        body=body,
    )
```

4. Update `probe_mcp_health()` to delegate to the new helper:

```python
async def probe_mcp_health(http: httpx.AsyncClient, base_url: str) -> bool:
    """Return True if the MCP server at base_url responds to /health with HTTP 200.

    Backward-compatible bool wrapper around _probe_mcp_health_detail().
    Callers that need structured probe results should use _probe_mcp_health_detail() directly.
    """
    result = await _probe_mcp_health_detail(http, base_url)
    return result.reachable and result.status_code == HTTPStatus.OK
```

5. Verify the import of `HTTPStatus` is still present (line 11: `from http import HTTPStatus`). It is — no change needed.

### Method

- `_probe_mcp_health_detail` uses `resp.json()` which in httpx returns a parsed Python object; if the body is not valid JSON this raises `json.JSONDecodeError` (subclass of `ValueError`). The catch `except (ValueError, Exception)` is intentionally broad with `# noqa: BLE001` to match the existing pattern used in `audit_security_defaults()` in this file.
- `bool(body.get("restart_recommended", False))` is defensive: the field could be `None`, `0`, or missing; `bool()` coerces these consistently.
- `probe_mcp_health` behavior is unchanged: `reachable=True` and `status_code=200` iff the server returned HTTP 200.

### Details

- Current `probe_mcp_health` location: lines 30-42, `async def probe_mcp_health(http: httpx.AsyncClient, base_url: str) -> bool:`.
- Insert `_probe_mcp_health_detail` immediately after `probe_mcp_health` (before `check_service_health`).
- The `_probe_mcp_health_detail` name uses a leading underscore indicating it is an internal helper not part of the public API of `repl_health.py`.
- Pattern reference for broad exception catch with noqa: see `audit_security_defaults()` lines 471-477 which use `except Exception: pass`.

## Validation plan

```bash
# Existing probe_mcp_health tests must still pass
uv run pytest tests/test_repl_health.py::TestProbeMcpHealth -v

# Type check
uv run mypy scripts/agent/repl_health.py

# Lint
uv run ruff check scripts/agent/repl_health.py
```

Expected outcomes:
- `TestProbeMcpHealth::test_returns_true_on_200` passes (bool True).
- `TestProbeMcpHealth::test_returns_false_on_non_200` passes (bool False for 503).
- `TestProbeMcpHealth::test_returns_false_on_exception` passes (bool False on ConnectError).
- No new mypy or ruff errors.
