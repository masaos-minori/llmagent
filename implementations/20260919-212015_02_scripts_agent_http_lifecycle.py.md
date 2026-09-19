## Goal
Remove `HttpServerLifecycleManager`'s duplicated `_stderr_log_paths` dict (route
through `StderrLogManager`'s new accessor methods from Step 01 of this pass instead),
and collapse the repeated cleanup-and-raise blocks in `_create_and_validate_proc` and
`_health_poll_until_ready` into shared private helpers — `REQ-001`, `REQ-002`,
`REQ-003`, `REQ-004`.

## Scope
- In scope: `HttpServerLifecycleManager.__init__`, `_open_stderr_log`,
  `_read_stderr_tail`, `_read_stderr_for_cleanup` (removed), `_clear_server_tracking_data`,
  `_cleanup_server_resources`, `_build_snapshot`, `_create_and_validate_proc`,
  `_health_poll_until_ready` — all within `scripts/agent/http_lifecycle.py`.
- Out of scope: `start`, `restart`, `shutdown_all`, `verify_running`,
  `verify_running_async`, `get_process_info`, `get_process_snapshot`, `list_processes`
  public signatures and observable behavior — unchanged (`plans/20260919-211529_plan.md`
  Constraints, carried from the source Issue). `_http_procs`, `_http_pgids`,
  `_stderr_files`, `_last_health_check` dicts — unchanged, still owned here.

## Assumptions
- Step 01 of this pass (`implementations/20260919-212015_01_scripts_agent_http_lifecycle_stderr_log_manager.py.md`)
  has already added `StderrLogManager.get_log_path`/`forget`/`clear` — this document's
  Method assumes those methods exist on `self._stderr_log_manager`.
- Step 03 of this pass updates `ShutdownCoordinator.shutdown_all()`'s call site
  separately — no change to that file is made here.

## Design decisions
- `_stderr_log_paths` is deleted entirely (not reduced to a thin cache) — every read
  site is routed through `self._stderr_log_manager.get_log_path(server_key)` and every
  removal through `self._stderr_log_manager.forget(server_key)`, since
  `StderrLogManager` already has the data and no caching benefit was identified.
- Two new private helpers are added, each covering only the sub-sequence that is
  byte-for-byte identical across its call sites (not the full branch, which differs in
  a branch-specific extra step):
  - `_close_and_forget_stderr(self, server_key: str, stderr_fh: IO[bytes]) -> None` —
    closes `stderr_fh`, pops `_stderr_files`, calls `_stderr_log_manager.forget()`.
    Used by `_create_and_validate_proc`'s three failure branches (current lines
    275-278, 302-306, 327-331), which differ afterward (one re-raises as
    `HttpStartupError`, one bare-re-raises, one additionally pops
    `_http_procs`/`_http_pgids` and re-raises the original `OSError`).
  - `_raise_startup_failure(self, server_key: str, reason: str, stderr_full: str) ->
    NoReturn` — pops `_http_procs`/`_http_pgids`, builds `StartupFailure(server_key,
    reason, stderr_full)`, raises `HttpStartupError`. Used by
    `_health_poll_until_ready`'s three branches (current lines 372-387, 399-410,
    412-423), each of which computes `stderr_full` via the existing
    `self._cleanup_server_resources(server_key)` call itself (kept per-branch — see
    Alternatives considered) before calling this helper with its own `reason` string.
- `_read_stderr_for_cleanup` is deleted; `_cleanup_server_resources` calls
  `self._read_stderr_tail(server_key)` directly (REQ-004).

## Alternatives considered
- A single mega-helper that also computes `stderr_full` internally (i.e.
  `_fail_startup(self, server_key, reason) -> NoReturn` doing
  `self._cleanup_server_resources(...)` itself): rejected because the early-exit
  branch needs the stderr content *before* raising, to pass to a `logger.error` call
  that only that branch makes, and the timeout branch needs to call
  `self._terminate_with_timeout(...)` between reading stderr and raising — folding
  `_cleanup_server_resources` into the helper would force those two branches to read
  stderr twice (once via the helper, once again for their own extra step) or would
  require a callback parameter, which is more complex than leaving one
  `self._cleanup_server_resources(server_key)` line per branch and sharing only the
  truly identical pop+build+raise tail in `_raise_startup_failure`.

## Implementation
### Target file
scripts/agent/http_lifecycle.py

### Procedure
1. Remove the `_stderr_log_paths` dict from `__init__` (current line 87).
2. Simplify `_open_stderr_log` to no longer duplicate path-tracking (current lines
   90-96).
3. Change `_read_stderr_tail` to read via `self._stderr_log_manager.get_log_path()`
   (current lines 98-110, specifically the `log_path = ...` line at 100).
4. Delete `_read_stderr_for_cleanup` (current lines 167-169); change
   `_cleanup_server_resources` (current lines 179-183) to call `_read_stderr_tail`
   directly.
5. Change `_clear_server_tracking_data` (current lines 171-177) to call
   `self._stderr_log_manager.forget(server_key)` instead of
   `self._stderr_log_paths.pop(server_key, None)`.
6. Change `_build_snapshot` (current lines 185-202) to read the stderr log path via
   `self._stderr_log_manager.get_log_path(server_key) or ""` instead of
   `self._stderr_log_paths.get(server_key, "")` (current line 193).
7. Add the `_close_and_forget_stderr` helper; replace the three matching cleanup
   sequences in `_create_and_validate_proc` (current lines 275-278, 302-306, 327-331)
   with calls to it.
8. Add the `_raise_startup_failure` helper; replace the three matching
   pop+build+raise sequences in `_health_poll_until_ready` (current lines 383-387,
   406-410, 419-423) with calls to it, keeping each branch's own
   `self._cleanup_server_resources(server_key)` call and any branch-specific extra
   step (the early-exit `logger.error` call; the timeout branch's
   `await self._terminate_with_timeout(...)` call) in place immediately before the
   helper call.
9. Add `NoReturn` to the `typing` import (already imports `IO, Any, cast` from
   `typing` — add `NoReturn` to that same import line).

### Method
`__init__` (remove the `_stderr_log_paths` line from the current block at 84-88):
```python
self._http_procs: dict[str, subprocess.Popen[bytes]] = {}
self._http_pgids: dict[str, int] = {}
self._stderr_files: dict[str, IO[bytes]] = {}
self._last_health_check: dict[str, float] = {}
```

`_open_stderr_log` (replaces current lines 90-96):
```python
def _open_stderr_log(self, server_key: str, cfg: McpServerConfig) -> IO[bytes]:
    """Open an append-mode file for the server's stderr output."""
    return self._stderr_log_manager.open_log(server_key, cfg)
```

`_read_stderr_tail` (replaces the `log_path = ...` line at current line 100):
```python
log_path = self._stderr_log_manager.get_log_path(server_key)
```

`_clear_server_tracking_data` / `_cleanup_server_resources` (replaces current lines
167-183):
```python
def _clear_server_tracking_data(self, server_key: str) -> None:
    """Remove health check timestamps, stderr file handles, and paths for a server."""
    fh = self._stderr_files.pop(server_key, None)
    if fh is not None:
        fh.close()
    self._stderr_log_manager.forget(server_key)
    self._last_health_check.pop(server_key, None)

def _cleanup_server_resources(self, server_key: str) -> str:
    """Read stderr tail, close stderr file handle, and remove tracking data for a server."""
    stderr_content = self._read_stderr_tail(server_key)
    self._clear_server_tracking_data(server_key)
    return stderr_content
```

`_build_snapshot` (replaces `stderr_log = ...` at current line 193):
```python
stderr_log = self._stderr_log_manager.get_log_path(server_key) or ""
```

New helper for `_create_and_validate_proc` (insert immediately before
`_create_and_validate_proc`'s definition, current line 244):
```python
def _close_and_forget_stderr(self, server_key: str, stderr_fh: IO[bytes]) -> None:
    """Close the stderr handle and drop stderr-path tracking (startup-failure cleanup)."""
    stderr_fh.close()
    self._stderr_files.pop(server_key, None)
    self._stderr_log_manager.forget(server_key)
```

`_create_and_validate_proc`'s three branches (replaces current lines 275-278,
302-306, 327-331 respectively — the `raise`/`raise e` statements themselves are
unchanged):
```python
except ValueError as e:
    self._close_and_forget_stderr(server_key, stderr_fh)
    raise HttpStartupError(
        StartupFailure(server_key=server_key, reason=str(e), stderr_full="")
    ) from e
```
```python
except Exception:
    self._close_and_forget_stderr(server_key, stderr_fh)
    raise
```
```python
finally:
    # Always cleanup resources if getpgid fails, even if termination fails
    self._close_and_forget_stderr(server_key, stderr_fh)
    self._http_procs.pop(server_key, None)
    self._http_pgids.pop(server_key, None)
raise e
```

New helper for `_health_poll_until_ready` (insert immediately before
`_health_poll_until_ready`'s definition, current line 338):
```python
def _raise_startup_failure(self, server_key: str, reason: str, stderr_full: str) -> NoReturn:
    """Drop tracked process/pgid entries and raise HttpStartupError with the given reason."""
    self._http_procs.pop(server_key, None)
    self._http_pgids.pop(server_key, None)
    raise HttpStartupError(
        StartupFailure(server_key=server_key, reason=reason, stderr_full=stderr_full)
    )
```

`_health_poll_until_ready`'s three branches (replaces current lines 372-387,
399-410, 412-423 respectively):
```python
if proc.poll() is not None:
    stderr_full = self._cleanup_server_resources(server_key)
    logger.error(
        "Lifecycle: %r exited early; stderr (%s chars): %s",
        server_key,
        len(stderr_full),
        _mask_secrets(stderr_full[:500]),
    )
    self._raise_startup_failure(server_key, "exited early", stderr_full)
```
```python
if await self._interruptible_poll_sleep(HEALTH_POLL_INTERVAL_SEC, shutdown_event):
    stderr_full = self._cleanup_server_resources(server_key)
    self._raise_startup_failure(server_key, "shutdown requested", stderr_full)
```
```python
stderr_full = self._cleanup_server_resources(server_key)
await self._terminate_with_timeout(proc, server_key, timeout=TERMINATE_TIMEOUT_SEC)
self._raise_startup_failure(
    server_key,
    f"did not become healthy within {cfg.startup_timeout_sec}s",
    stderr_full,
)
```

### Details
- Import line change: `from typing import IO, Any, cast` (current line 28) becomes
  `from typing import IO, Any, NoReturn, cast`.
- `_raise_startup_failure` is annotated `-> NoReturn` (not `-> None`) since every call
  site relies on it never returning — mypy must be able to see the function always
  raises for the calling branch's own control flow (e.g. no `return`/fallthrough
  needed after the call).
- The `StartupFailure(server_key=server_key, reason=..., stderr_full="")` literal in
  the `ValueError` branch keeps `stderr_full=""` unchanged (this branch fails before
  any process/stderr exists to read) — `_close_and_forget_stderr` does not compute a
  stderr value, it only performs cleanup.

## Compatibility considerations
No public method signature changes (`plans/20260919-211529_plan.md` Constraints).
`ProcessInfoSnapshot.stderr_log`'s value is unchanged: `get_log_path(...) or ""`
reproduces the exact current fallback-to-empty-string behavior of
`self._stderr_log_paths.get(server_key, "")`. `StartupFailure`'s field values and
`HttpStartupError`'s raised type are unchanged for every failure branch — only how
the failure is assembled internally changes.

## Security considerations
N/A: no new external input, no new subprocess invocation pattern, no new file I/O
path — this step only restructures already-reviewed internal control flow
(`nosec B603`/`B404` annotations on `subprocess.Popen`, lines 296-300, are untouched).

## Rollback considerations
Revert this file's diff. No data migration, no config change. The two new helpers and
the `_stderr_log_paths` removal are all confined to this one file; Steps 01/03/04-07
of this pass are each independently revertable (Step 01's new `StderrLogManager`
methods being additive means reverting this step alone does not break Step 01).

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py tests/agent/test_http_lifecycle_integration.py -v`
  (updated in Steps 05/06 of this pass) — must pass with no behavior change in
  start/restart/health-poll/getpgid-failure paths.
- `uv run radon cc scripts/agent/http_lifecycle.py -s -n B` — `_create_and_validate_proc`
  and `_health_poll_until_ready` must no longer appear (baseline: B(9), B(6)).
- `uv run mypy scripts/agent/http_lifecycle.py` — confirm `NoReturn` typing is
  accepted with no new errors.
- `rg "_stderr_log_paths|_read_stderr_for_cleanup" scripts/agent/http_lifecycle.py` —
  must return no matches.
- `uv run ruff check scripts/agent/http_lifecycle.py` — confirm lint compliance.

## Completion criteria
- `HttpServerLifecycleManager` has no `_stderr_log_paths` attribute.
- `_read_stderr_for_cleanup` no longer exists.
- `_close_and_forget_stderr` and `_raise_startup_failure` exist and are called from
  all three branches of `_create_and_validate_proc` and `_health_poll_until_ready`
  respectively.
- `uv run radon cc scripts/agent/http_lifecycle.py -s -n B` reports no B-or-worse
  grade for either method.
- `uv run pytest tests/agent/test_lifecycle.py tests/agent/test_http_lifecycle_integration.py -v`
  passes.

## Out of scope
- Any change to `http_lifecycle_command_validator.py`, `http_lifecycle_health_checker.py`,
  or `http_lifecycle_process_terminator.py` (`plans/20260919-211529_plan.md` Scope).
- Any behavior change to health-check timing, retry counts, or startup-timeout
  semantics.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test updates tracked separately in Steps 05/06 of this pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation update in scope |

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
- **Requirement ID**: `REQ-001` (route through StderrLogManager accessor), `REQ-002` (extract `_health_poll_until_ready` cleanup helper), `REQ-003` (extract `_create_and_validate_proc` cleanup helper), `REQ-004` (remove `_read_stderr_for_cleanup`)
- **Source issue**: issues/20260919-210241_refactor_003_deduplicate-stderr-path-tracking-and-cleanup-logic-in-http_lifecycle.py.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-211529_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-212015
- **Related target files**: scripts/agent/http_lifecycle.py
