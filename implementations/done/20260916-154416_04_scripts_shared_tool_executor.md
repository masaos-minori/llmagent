## Goal

Move the startup-mode reject gate from `ToolExecutor._check_startup_mode()` into `ToolTransportInvoker.invoke()`, so that both `ToolExecutor.execute()`'s name-based path and any direct caller holding a `ToolTransportInvoker` reference route through one enforcement point. (REQ-004; "No network request ... during ... tool execution")

## Scope

- Add `self._server_configs = server_configs` to `ToolTransportInvoker.__init__`.
- Move the startup-mode rejection logic from `ToolExecutor._check_startup_mode()` into `ToolTransportInvoker.invoke()`.
- Remove `ToolExecutor._check_startup_mode()` since it's no longer needed.

## Assumptions

- `StartupMode.NONE` is defined in `scripts/shared/mcp_config.py` and `McpServerConfig.is_disabled` returns `True` when `startup_mode == StartupMode.NONE`.
- The `ToolExecutor` subclass stores `self._server_configs` in its own `__init__` after calling `super().__init__()`, so the parent class has access to the configs dict.

## Design decisions

- Use `cfg.is_disabled` as the single predicate, consistent with how other parts of the codebase derive "disabled" status. This avoids four independent re-derivations of "is this server disabled" drifting apart over time.
- Move the check into the shared base class rather than keeping it only in the subclass — this ensures all callers go through one enforcement point.
- Keep `_run_gate_chain()` unchanged because it still handles the `StartupCheckStatus.UNAVAILABLE` → FATAL escalation for required servers.

## Alternatives considered

- Keeping `_check_startup_mode()` in `ToolExecutor` and adding a separate check in `ToolTransportInvoker.invoke()` — duplicates the check across two classes, violating the goal of a single enforcement point.
- Adding a new `is_none_mode` property on `StartupMode` — unnecessary since `is_disabled` already covers this.
- Checking `cfg.startup_mode` directly instead of `cfg.is_disabled` — equivalent but less semantic; `is_disabled` is the established convention.

## Compatibility considerations

- Existing non-disabled servers are unaffected; the added `is_disabled` check only prevents transport construction for disabled servers.
- If a disabled server somehow still appears in `server_configs` (e.g., via config reload), it will have no transport entry, and `invoke()` will fail with "No transport configured" — this is acceptable because the server should never be invoked anyway.

## Security considerations

- Preventing HttpTransport construction for disabled servers eliminates the possibility of a disabled server being used for tool execution even if other gates are bypassed.

## Rollback considerations

- Reverting the `is_disabled` check in `__init__` restores the pre-fix behavior where disabled servers get a live transport object.

## Implementation

### Target file

`scripts/shared/tool_transport_invoker.py`

### Procedure

1. **Phase 1: Transport-layer exclusion**
   - In `__init__`'s transport-construction loop (line 53-57), add `and not cfg.is_disabled` to the condition before constructing `HttpTransport`.
   - Current code: `for key, cfg in server_configs.items():` unconditionally constructs `HttpTransport`.
   - New code: `for key, cfg in server_configs.items(): if cfg.is_disabled: continue`

2. **Phase 2a: Move startup-mode gate into `invoke()`**
   - Give `ToolTransportInvoker` access to `server_configs` (store it as `self._server_configs`).
   - Move the startup-mode reject check into `invoke()` itself, so both `ToolExecutor.execute()`'s name-based path and any direct caller holding a `ToolTransportInvoker` reference route through one enforcement point.
   - Current state: `ToolTransportInvoker.invoke()` has no startup-mode check; `ToolExecutor._check_startup_mode()` exists only in the subclass.
   - New state: `ToolTransportInvoker.invoke()` checks `self._server_configs.get(server_key)` and rejects if `cfg.startup_mode == StartupMode.NONE`.

### Method

- **Step 1**: Edit `__init__` at lines 52-57 — add `if cfg.is_disabled: continue` inside the loop.
- **Step 2**: Edit `__init__` — add `self._server_configs = server_configs` before the transport loop.
- **Step 3**: Edit `invoke()` — add startup-mode rejection at the top of the method.

### Details

**Step 1 — `__init__` transport-construction filter:**

```python
# Before (lines 52-57):
self._transports: dict[str, HttpTransport] = {}
for key, cfg in server_configs.items():
    timeout_sec = cfg.call_timeout_sec
    self._transports[key] = HttpTransport(
        http, cfg.url, key, cfg, timeout_sec=timeout_sec
    )

# After:
self._transports: dict[str, HttpTransport] = {}
for key, cfg in server_configs.items():
    if cfg.is_disabled:
        continue
    timeout_sec = cfg.call_timeout_sec
    self._transports[key] = HttpTransport(
        http, cfg.url, key, cfg, timeout_sec=timeout_sec
    )
```

**Step 2 — Store server_configs:**

Add before the transport loop:
```python
self._server_configs = server_configs
```

**Step 3 — `invoke()` startup-mode gate:**

After the health check block (around line 194-195) and before the lifecycle check:

```python
async def invoke(
    self,
    server_key: str,
    tool_name: str,
    args: dict[str, Any],
) -> ToolCallResult:
    """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
    if err := self._check_health(server_key):
        return err

    # REQ-004: reject disabled servers at the shared invocation boundary
    cfg = self._server_configs.get(server_key)
    if cfg is not None and cfg.startup_mode == StartupMode.NONE:
        msg = f"MCP server {server_key!r} is disabled (startup_mode=none) and cannot be used"
        logger.warning(msg)
        return self._error_result(server_key, msg, error_type="tool")

    if self._lifecycle is not None:
        # ... rest unchanged
```

## Validation plan

- Run unit tests: `uv run pytest tests/shared/test_tool_transport_invoker.py tests/shared/test_tool_transport_invoker_merge.py -v`
- Verify disabled-server transport not constructed: add a test with `startup_mode=NONE` and assert `HttpTransport` was not instantiated.
- Verify `invoke()` rejects disabled servers: add a test asserting the error result from `invoke()` for a disabled server.
- Static analysis: `uv run ruff check scripts/shared/tool_transport_invoker.py`, `uv run mypy scripts/shared/tool_transport_invoker.py`, `uv run bandit scripts/shared/tool_transport_invoker.py`.

## Completion criteria

- [ ] `__init__` does not construct `HttpTransport` for disabled servers.
- [ ] `invoke()` rejects disabled servers with an error result.
- [ ] Both `ToolExecutor.execute()` and direct `invoke()` calls reject disabled servers identically.
- [ ] All existing tests pass without regression.
- [ ] No new lint/type/security errors introduced.

## Out of scope

- Modifying `ToolExecutor._check_startup_mode()` / `_run_gate_chain()` — that is handled in the next document (row 4).
- Any MCP server business logic unrelated to the startup/discovery/registry-publication path.

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260917-072329 | 20260917-072329 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260917-072338 | 20260917-072338 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260917-072346 | 20260917-072346 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — |  |

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
- **Requirement ID**: REQ-002, REQ-004
- **Source issue**: issues/20260914-103015_mcpagent01_mcp-server-availability-startup-publication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-114735_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-154416
- **Related target files**: scripts/shared/tool_executor.py