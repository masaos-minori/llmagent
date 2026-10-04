# Implementation Procedure: Remove dead outer AsyncClient and unused client param in HTTP MCP startup poll

## Goal

Remove the dead outer `httpx.AsyncClient` opened in `HttpServerLifecycleManager.start()` (shadowed and never used inside `_health_poll_until_ready()`) and drop the now-unused `client` parameter from `_health_poll_until_ready()`, with no change to health-poll timing, timeouts, or failure semantics. Implements REQ-001 (remove outer client), REQ-002 (drop `client` param), REQ-003 (preserve all observable behavior).

## Scope

Modify exactly one file, `scripts/agent/http_lifecycle.py`:

- In `start()`: delete the outer `async with httpx.AsyncClient(...)` wrapper and call `_health_poll_until_ready()` without a client argument.
- In `_health_poll_until_ready()`: remove the unused `client: httpx.AsyncClient` parameter and its docstring `Args:` entry.
- Keep the single authoritative inner client inside `_health_poll_until_ready()` byte-for-byte unchanged.

Reference / verification dependency only (MUST NOT be modified): `tests/agent/test_http_lifecycle_integration.py`.

## Assumptions

- After removing the outer client, `MCPSERVER_HEALTH_TIMEOUT` remains referenced by `compute_health_check_timeout(...)` at line 391, so no import or global becomes unused.
- `httpx` stays imported and used (inner client + `httpx.HTTPError` handling), so no unused-import warning is introduced.
- There is exactly one caller of `_health_poll_until_ready()` (line 469); confirmed via `rg`.

## Design decisions

- Behavior-preserving dead-code removal (Plan Path A): ≤ 3 files, both edited symbols are private to `HttpServerLifecycleManager`, no public/runtime interface change, no database schema change. Architecture analysis, dependency graphing, and historical analysis are skipped per Plan.
- Minimal, localized edits. The authoritative inner client, its `hc_timeout` computation, the poll loop, deadline, and `shutdown_event` racing are left equivalent.
- Because there is no behavior change, the existing integration suite is the behavior lock: it MUST pass before AND after the edit.

## Alternatives considered

- Leave the dead outer client in place: rejected — wasted connection-setup work on the hot startup path and a misleading signature that invites future bugs (e.g. fixing the timeout on the wrong client).
- Reuse the caller's client inside `_health_poll_until_ready()` instead of removing it: rejected — out of scope and would change timeout semantics (the method intentionally binds its own `hc_timeout`-based client). REQ-003 forbids altering the poll/timeout/failure behavior.

## Implementation

### Target file

`scripts/agent/http_lifecycle.py` — the single `Implementation Target Files` row this document implements.

### Procedure

1. **Phase 1 — Preparation (behavior lock).** Run `tests/agent/test_http_lifecycle_integration.py` and record the pass state as the golden baseline. (REQ-003)
2. **Phase 2 — Core logic (refactor).** Edit `start()` to delete the outer `async with httpx.AsyncClient(...)` block and drop the client argument; edit `_health_poll_until_ready()` to remove the `client` parameter and its docstring `Args:` line. (REQ-001, REQ-002)
3. **Phase 3 — Verification.** Run ruff format, ruff check, mypy on the touched file; re-run the full integration suite; confirm diff-cover ≥ 90% on changed lines. (REQ-003)

### Method

Behavior-lock first, then two localized hunks, then static + behavioral re-verification. Each hunk is independently reversible.

### Details

**Edit 1 — `start()` outer block (current lines 464–471).** Replace:

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

with:

```python
        if cfg.startup_timeout_sec > 0:
            deadline = time.monotonic() + cfg.startup_timeout_sec
            await self._health_poll_until_ready(
                server_key, cfg, proc, deadline, shutdown_event
            )
```

Preserve the `if cfg.startup_timeout_sec > 0:` guard and the skip log in the `else` branch (lines 472–476). Do not touch anything outside this block.

**Edit 2 — `_health_poll_until_ready()` signature (current lines 363–371).** Remove the `client: httpx.AsyncClient,` parameter:

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
```

becomes:

```python
    async def _health_poll_until_ready(
        self,
        server_key: str,
        cfg: McpServerConfig,
        proc: subprocess.Popen[bytes],
        deadline: float,
        shutdown_event: asyncio.Event | None,
    ) -> None:
```

**Edit 3 — `_health_poll_until_ready()` docstring `Args:` (current line 382).** Remove the `client:` entry:

```python
            client: Async HTTP client for health check requests.
```

Delete this line only.

**Unchanged — inner client re-bind (current lines 393–395).** Leave byte-for-byte:

```python
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=hc_timeout)
        ) as client:
```

This remains the sole authoritative health-check client. Verify no other reference to the removed parameter survives anywhere in the file.

## Compatibility considerations

Both edited symbols are private to `HttpServerLifecycleManager`; there is a single internal call site, updated in Edit 1. No external API, transport, or runtime interface changes. The command-validator allowlist and any other lifecycle methods are untouched.

## Security considerations

Dead-code removal only. No security-relevant logic, allowlist, or validation path is touched. No new attack surface is introduced; the authoritative inner client and its timeout remain the sole health-check client.

## Rollback considerations

Two small, localized hunks plus one docstring line deletion. Reverse via `git checkout scripts/agent/http_lifecycle.py` or by reverting the three hunks. Confirm the integration-suite behavior lock returns to green after any revert.

## Validation plan

| Target / Scope | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle.py` | Static: format, lint, type | `uv run ruff format` / `ruff check` / `uv run mypy --no-namespace-packages --no-incremental scripts/agent/http_lifecycle.py` | Clean; no new errors |
| `tests/agent/test_http_lifecycle_integration.py` | Integration (behavior lock) | `uv run pytest tests/agent/test_http_lifecycle_integration.py -v` | Passes before and after the edit |
| Full suite | Regression | `uv run pytest tests/` | No new failures |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |

Note: the integration suite drives `start()` through mocked `time.monotonic` / `subprocess.Popen` / `asyncio.sleep` to force deterministic early-exit and timeout paths; it does not construct or assert on `httpx.AsyncClient` construction count. Removing the outer client therefore cannot regress a call-count assertion, but the suite is still run as the mandatory behavior lock (Plan UNK-01).

## Completion criteria

- AC1: `start()` no longer constructs an `AsyncClient` that goes unused — the outer `async with httpx.AsyncClient(...)` block is gone and the call passes no client. ↔ REQ-001
- AC2: Health polling still works end-to-end on both the startup-success and timeout-failure paths with unchanged timing, timeouts, and failure semantics. ↔ REQ-003
- AC3: `_health_poll_until_ready()` has no `client` parameter; the single authoritative inner client remains the sole health-check client. ↔ REQ-002
- ruff format, ruff check, and mypy are clean on the touched file; the integration-suite behavior lock passes.

## Out of scope

- Any change to health-check logic, timeout computation, or the `HealthChecker` module.
- Refactoring other lifecycle methods.
- Adding/removing env-var handling.
- Modifying any file other than `scripts/agent/http_lifecycle.py`.
- Modifying `tests/agent/test_http_lifecycle_integration.py` (behavior lock: run, not modified).
- Documentation updates (N/A: issue reports no documentation required; docstring edits are code-only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run integration suite as behavior-lock baseline | Pending | — | — | |
| 2 | Remove outer AsyncClient in start(); drop client param + docstring | Pending | — | — | |
| 3 | Run ruff/mypy, re-run integration suite, diff-cover | Pending | — | — | |

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
- **Generated at**: 20261004-183507
- **Related target files**: scripts/agent/http_lifecycle.py
