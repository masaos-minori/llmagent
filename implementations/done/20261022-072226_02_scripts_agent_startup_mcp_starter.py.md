## Goal

Add an explicit `except StartupInterrupted: raise` guard in
`McpServerStarter.start_servers()` before the broad first-attempt tuple, so a shutdown
signal is never routed through the retry helper (`REQ-002`, `REQ-005`).

## Scope

- **In-Scope**:
  - Add `except StartupInterrupted: raise` immediately before the
    `except (OSError, RuntimeError, TimeoutError, ConnectionRefusedError,
    ConnectionResetError, BrokenPipeError)` tuple in `start_servers()`
    (`scripts/agent/startup_mcp_starter.py`, before line 88).
  - KEEP `RuntimeError` in the tuple (preserves genuine-RuntimeError retry, `REQ-005`).
- **Out-of-Scope**:
  - Removing `RuntimeError` from the tuple.
  - Any change to signal registration, the shutdown event, or graceful-shutdown timing.
  - Changes to `scripts/agent/startup.py` (the exception rebase is a separate procedure).

## Assumptions

- **ASM-001**: After the `startup.py` rebase, `StartupInterrupted` is a `BaseException`, so
  it already escapes the tuple; this guard is defense-in-depth and makes intent visible.
- **ASM-002**: The raise sites (`startup_mcp_starter.py:63,77,138`) and
  `retry_once_with_delay` (`shared/retry_helper.py:49,54`) all raise `StartupInterrupted`;
  the guard sits above every one of them on this call path.

## Design decisions

- Keep `RuntimeError` in the tuple: it also matches genuine transient errors that are
  intentionally retried (`REQ-005`). Removing it would regress that handling.
- Add the explicit guard *before* the tuple so a `StartupInterrupted` is re-raised
  immediately without entering `retry_once_with_delay()` (`REQ-002`).

## Alternatives considered

- Relying solely on the `BaseException` rebase to exclude `StartupInterrupted` from the
  tuple: sufficient functionally, but the explicit guard documents intent for future
  readers (the issue's stated motivation).

## Implementation

### Target file

`scripts/agent/startup_mcp_starter.py`

### Procedure

1. Insert `except StartupInterrupted: raise` immediately before the existing
   `except (OSError, RuntimeError, ...)` tuple in `start_servers()` (before line 88).
2. Do NOT remove `RuntimeError` from the tuple.

### Method

In `start_servers()`, the current structure is:

```python
                try:
                    started_at = await self._start_http_subprocess_once(key, cfg)
                    if started_at is not None:
                        last_startup_time = started_at
                except (
                    OSError,
                    RuntimeError,
                    TimeoutError,
                    ConnectionRefusedError,
                    ConnectionResetError,
                    BrokenPipeError,
                ) as e:
```

Prepend an `except StartupInterrupted: raise` clause between the `try` body and the broad
tuple:

```python
                try:
                    started_at = await self._start_http_subprocess_once(key, cfg)
                    if started_at is not None:
                        last_startup_time = started_at
                except StartupInterrupted:
                    raise
                except (
                    OSError,
                    RuntimeError,
                    TimeoutError,
                    ConnectionRefusedError,
                    ConnectionResetError,
                    BrokenPipeError,
                ) as e:
```

### Details

`StartupInterrupted` is raised via lazy local imports inside `start_servers()` at the
existing sites (lines 61, 75). Add ONE local import at the top of `start_servers()` (right
after `last_startup_time = 0.0`, before the `for` loop):

```python
        from agent.startup import StartupInterrupted
```

Do NOT add a module-level import: `agent.startup` imports `McpServerStarter` at module
load (`startup.py:24`), so a module-level `from agent.startup import StartupInterrupted`
in `startup_mcp_starter` would break load order (`StartupInterrupted` is defined at
`startup.py:30`, after that import site). The local import executes at call time, by which
point `agent.startup` is fully loaded — matching the existing pattern at lines 61 and 75.

## Compatibility considerations

`retry_once_with_delay` (`shared/retry_helper.py:42`) catches `except Exception`; a
`BaseException` `StartupInterrupted` already escapes it. This guard only affects the
first-attempt tuple in `start_servers()`.

## Security considerations

N/A: no auth, secret, or crypto impact.

## Rollback considerations

Revert the single added clause (and the import) — a single logical commit.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/agent/startup_mcp_starter.py` | Unit: `StartupInterrupted` propagates without retry; genuine `RuntimeError` retries | `pytest` (T-001, T-002) | AC-002, AC-005 |
| `tests/agent/` (full) | Regression | `pytest` | All green |

## Completion criteria

- A `StartupInterrupted` raised from a mocked subprocess start propagates out of
  `start_servers()` without invoking `retry_once_with_delay` (AC-002, T-001).
- A genuine `RuntimeError` from `_start_http_subprocess_once()` still triggers exactly one
  retry (AC-005, T-002).

## Out of Scope

`scripts/agent/startup.py` (exception rebase is a separate procedure), retry timing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261022-095438 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261022-095438 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261022-095438 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261022-095438 | N/A: no docs map to `startup_mcp_starter.py` |

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
- **Requirement ID**: REQ-002, REQ-005
- **Source issue**: `issues/20261021-220332_star002_make-startupinterrupted-distinguishable-from-ordinary-runtimeerror-in-broad-startup-handlers.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261021-232426_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-072226
- **Related target files**: `scripts/agent/startup_mcp_starter.py`