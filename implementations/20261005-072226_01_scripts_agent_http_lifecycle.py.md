## Goal

Remove the dead outer `httpx.AsyncClient` opened in `HttpServerLifecycleManager.start()` (shadowed by the inner client in `_health_poll_until_ready()`) and drop the unused `client` parameter from `_health_poll_until_ready()`, preserving all behavior.

## Scope

- Modify `scripts/agent/http_lifecycle.py`: delete the outer `async with httpx.AsyncClient(...)` block in `start()`, remove the `client` parameter and its docstring entry from `_health_poll_until_ready()`, update the call site to drop the `client` argument.

## Assumptions

- After removing the outer client, `MCPSERVER_HEALTH_TIMEOUT` remains referenced by `compute_health_check_timeout(...)`, so no import or global becomes unused.
- `httpx` stays imported and used (inner client + `httpx.HTTPError` handling), so no unused-import warning is introduced.
- No existing test asserts on the number of `httpx.AsyncClient` constructions (verified: none found).

## Design decisions

- Delete the outer `async with httpx.AsyncClient(...)` block entirely rather than refactoring to reuse it — the inner client is the authoritative one and the outer one performs zero requests.
- Drop the `client` parameter from `_health_poll_until_ready()` since it is never referenced inside that method.

## Alternatives considered

- Keep the outer client but suppress the linter warning: rejected because it preserves dead code and a misleading signature.
- Pass the outer client through to `_health_poll_until_ready()` and use it there: rejected because the inner client already handles all health-check requests; reusing the outer one would require changing the poll loop logic.

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
Delete the outer `async with httpx.AsyncClient(...)` wrapper in `start()` and stop passing a client to `_health_poll_until_ready()`. Drop the `client` parameter (and its docstring `Args:` entry) from `_health_poll_until_ready()`.

### Method
1. In `start()` (line ~469): replace the two-line `async with httpx.AsyncClient(...)` block with a direct call to `_health_poll_until_ready()` without the `client` argument.
2. In `_health_poll_until_ready()` (line ~368): remove the `client: httpx.AsyncClient,` parameter from the signature and its corresponding docstring `Args:` entry.

### Details
**Change 1 — `start()` (lines 469–476):**

Before:
```python
if cfg.startup_timeout_sec > 0:
    deadline = time.monotonic() + cfg.startup_timeout_sec
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(timeout=MCPSERVER_HEALTH_TIMEOUT)
    ) as client:
        await self._health_poll_until_ready(
            server_key, cfg, proc, client, deadline, shutdown_event
        )
```

After:
```python
if cfg.startup_timeout_sec > 0:
    deadline = time.monotonic() + cfg.startup_timeout_sec
    await self._health_poll_until_ready(
        server_key, cfg, proc, deadline, shutdown_event
    )
```

**Change 2 — `_health_poll_until_ready()` (lines 363–393):**

Before:
```python
async def _health_poll_until_ready(
    self,
    server_key: str,
    cfg: McpServerConfig,
    proc: subprocess.Popen[bytes],
    client: httpx.AsyncClient,
    deadline: float,
    shutdown_event: asyncio.Event | None,
) -> None:
    """Poll /health endpoint until the server becomes healthy or timeout expires.

    Polls the health endpoint in a loop, checking for early exit and shutdown
    events between polls. Raises HttpStartupError on early exit, shutdown,
    or timeout.

    Note: A new AsyncClient is created per call site (not reused across calls).
    This prioritizes correctness — no leaked connections on failure paths —
    over connection pooling benefits, which are marginal for short-lived
    health checks against localhost.

    Args:
        server_key: Server identifier key.
        cfg: Server configuration.
        proc: Subprocess instance to monitor.
        client: Async HTTP client for health check requests.
        deadline: Monotonic time at which to abort polling.
        shutdown_event: Optional event to race against poll sleep.

    Raises:
        HttpStartupError: On early exit, shutdown, or timeout.
    """
```

After:
```python
async def _health_poll_until_ready(
    self,
    server_key: str,
    cfg: McpServerConfig,
    proc: subprocess.Popen[bytes],
    deadline: float,
    shutdown_event: asyncio.Event | None,
) -> None:
    """Poll /health endpoint until the server becomes healthy or timeout expires.

    Polls the health endpoint in a loop, checking for early exit and shutdown
    events between polls. Raises HttpStartupError on early exit, shutdown,
    or timeout.

    Note: A new AsyncClient is created per call site (not reused across calls).
    This prioritizes correctness — no leaked connections on failure paths —
    over connection pooling benefits, which are marginal for short-lived
    health checks against localhost.

    Args:
        server_key: Server identifier key.
        cfg: Server configuration.
        proc: Subprocess instance to monitor.
        deadline: Monotonic time at which to abort polling.
        shutdown_event: Optional event to race against poll sleep.

    Raises:
        HttpStartupError: On early exit, shutdown, or timeout.
    """
```

## Compatibility considerations

- The `client` parameter removal changes the private method signature. Since `_health_poll_until_ready()` has only one caller (inside `start()`), updating that single call site eliminates any risk of stale callers.
- No public API surface is affected.

## Security considerations

- Removing the outer client eliminates a potential resource leak on failure paths where the outer context manager might not be entered (e.g., if an exception occurs before the `async with` line). However, the current code already enters the outer context unconditionally when `cfg.startup_timeout_sec > 0`, so this is purely a cleanup benefit, not a security fix.

## Rollback considerations

- Revert both changes atomically: restore the outer `async with httpx.AsyncClient(...)` block in `start()` and the `client` parameter in `_health_poll_until_ready()`.
- If a test depends on double construction count, revert only that test adjustment.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Static: format, lint, type | `uv run ruff format` / `ruff check` / `uv run mypy` on the file | Clean; no new errors |
| tests/agent/test_http_lifecycle_integration.py | Integration (behavior lock) | `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` | Passes before and after the edit |
| Full suite | Regression | `uv run pytest tests/` | No new failures |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |

## Completion criteria

- [ ] The outer `async with httpx.AsyncClient(...)` block is removed from `start()` and replaced with a direct call to `_health_poll_until_ready()` without the `client` argument.
- [ ] The `client: httpx.AsyncClient` parameter and its docstring `Args:` entry are removed from `_health_poll_until_ready()`.
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.
- [ ] `mypy` passes on the modified file.
- [ ] All integration tests in `tests/agent/test_http_lifecycle_integration.py` pass.
- [ ] No new failures in the full test suite (`uv run pytest tests/`).

## Out of scope

- Any change to health-check logic, timeout computation, or the `HealthChecker` module.
- Refactoring other lifecycle methods.
- Adding/removing env-var handling.
- Documentation updates beyond method docstrings.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003
- **Source issue**: issues/20261004-065632_mcp003_start-opens-an-unused-httpx.asyncclient-shadowed-inside-_health_poll_until_ready.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-084356_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-072226
- **Related target files**: scripts/agent/http_lifecycle.py
