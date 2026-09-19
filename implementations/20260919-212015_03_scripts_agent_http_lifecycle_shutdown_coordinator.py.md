## Goal
Update `ShutdownCoordinator.shutdown_all()`'s one direct access to
`manager._stderr_log_paths` so it keeps working once Step 02 of this pass removes
that attribute from `HttpServerLifecycleManager` (`REQ-001`).

## Scope
- In scope: the single line `manager._stderr_log_paths.clear()` inside
  `ShutdownCoordinator.shutdown_all()`.
- Out of scope: every other line in `shutdown_all()` (process termination,
  `_http_pgids`/`_stderr_files` handling, SIGINT absorption/restoration) — unchanged.
  This is the same discipline the manager's other direct-attribute accesses in this
  function already follow (`manager._http_pgids`, `manager._stderr_files` — an
  existing, unchanged convention in this file, not something this refactor addresses).

## Assumptions
- Step 01 of this pass
  (`implementations/20260919-212015_01_scripts_agent_http_lifecycle_stderr_log_manager.py.md`)
  has already added `StderrLogManager.clear()`, and Step 02
  (`implementations/20260919-212015_02_scripts_agent_http_lifecycle.py.md`) confirms
  `HttpServerLifecycleManager._stderr_log_manager` (the `StderrLogManager` instance)
  is unchanged by this pass — it already exists at `http_lifecycle.py:80`.

## Design decisions
- Replace `manager._stderr_log_paths.clear()` with
  `manager._stderr_log_manager.clear()` — reaches into the manager's existing
  `_stderr_log_manager` collaborator instead of a dict this refactor removes,
  consistent with this function's existing pattern of reading the manager's internal
  attributes directly (it is not a `HttpServerLifecycleManager` public-API caller;
  it is a tightly-coupled collaborator of that class, same as before this change).

## Alternatives considered
- Add a `HttpServerLifecycleManager.clear_stderr_log_paths()` public delegating method
  and call that instead: rejected as an unnecessary indirection layer for a single
  internal call site — `shutdown_all()` already reaches into several of the manager's
  private attributes directly by established convention in this same function, so
  routing through `manager._stderr_log_manager.clear()` (one hop to an existing
  collaborator) is consistent with that convention rather than introducing a new one.

## Implementation
### Target file
scripts/agent/http_lifecycle_shutdown_coordinator.py

### Procedure
1. Replace the single line `manager._stderr_log_paths.clear()` (current line 132)
   with `manager._stderr_log_manager.clear()`.

### Method
Replaces current line 132 (immediately before `manager._last_health_check.clear()` at
line 133, both inside the `try` block after the per-server termination loop):
```python
manager._stderr_log_manager.clear()
manager._last_health_check.clear()
```

### Details
No other line in this file changes. `manager._last_health_check.clear()` (line 133)
is unaffected and unchanged.

## Compatibility considerations
No public signature change — `ShutdownCoordinator.shutdown_all(manager, terminator=...)`
is unchanged. Behavior is identical: after `shutdown_all()` completes, every tracked
stderr log path is cleared, same as before (now via `StderrLogManager.clear()`
instead of a dict this class no longer owns).

## Security considerations
N/A: no new external input or I/O — this is an internal-collaborator call-site
substitution only.

## Rollback considerations
Revert this file's one-line diff. No dependency on this file from any other file in
this pass except `http_lifecycle.py` (already unchanged by this file — Step 02
removes the attribute this line used to read, but does not read this file itself).

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -v`
  (updated in Step 07 of this pass to assert against the new call) — must pass.
- `rg "_stderr_log_paths" scripts/agent/http_lifecycle_shutdown_coordinator.py` — must
  return no matches.
- `uv run mypy scripts/agent/http_lifecycle_shutdown_coordinator.py` — confirm no new
  errors (the `TYPE_CHECKING`-only `HttpServerLifecycleManager` import already exposes
  `_stderr_log_manager` for type-checking purposes since it is an instance attribute
  of that class).

## Completion criteria
- `manager._stderr_log_paths` no longer appears anywhere in this file.
- `manager._stderr_log_manager.clear()` is called in `shutdown_all()` in the same
  place the old call was.
- `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -v` passes.

## Out of scope
- Any change to process termination, SIGINT handling, or `_http_pgids`/`_stderr_files`
  clearing logic in this file (`plans/20260919-211529_plan.md` Scope).
- The pre-existing vulture finding (`unused variable 'signum'`, this file's line 38)
  — confirmed pre-existing and unrelated during the Plan's Step 5 baseline scan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test update tracked separately in Step 07 of this pass |
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
- **Requirement ID**: `REQ-001` (consolidate stderr-log-path ownership; update the ShutdownCoordinator call site the source Issue missed)
- **Source issue**: issues/20260919-210241_refactor_003_deduplicate-stderr-path-tracking-and-cleanup-logic-in-http_lifecycle.py.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-211529_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-212015
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py
