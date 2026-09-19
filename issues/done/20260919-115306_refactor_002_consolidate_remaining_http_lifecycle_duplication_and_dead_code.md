# Consolidate remaining http_lifecycle duplication and dead code

## Priority
Medium

## Summary
Consolidate remaining cross-module duplication in `scripts/agent/http_lifecycle*.py` modules and remove dead code paths identified by prior refactoring issues. Eliminate duplicate shutdown logic between `HttpServerLifecycleManager.shutdown_all()` and `ShutdownCoordinator.shutdown_all()`, fix the circular import in `HealthChecker.compute_health_check_timeout()`, and resolve the hardcoded health-recheck interval constant.

## Background
Three prior refactoring issues have been completed against `http_lifecycle.py`:

1. `20260911-214848_refactor_http_lifecycle_eliminate_cross_module_duplication.md` — proposed delegating termination, shutdown, snapshot, and liveness logic to concern-specific sub-modules.
2. `20260913-081127_refactor_http_lifecycle_complexity_type_safety.md` — focused on reducing cyclomatic complexity and fixing type mismatches.
3. `20260915-102515_refactor_http_lifecycle_module_split.md` — the most detailed: consolidated shutdown cleanup into `ShutdownCoordinator`, renamed `ProcessInfoSnapshot` to `RawProcessSnapshot` in the snapshot module, added rate-limited verify wrapper to `HealthChecker`, split `_cleanup_server_resources()`, deleted `terminate()`, and fixed the SIGINT handler duplication. Of these, `terminate()` deletion and `ProcessInfoSnapshot`→`RawProcessSnapshot` rename were already applied; the rest remain unapplied.

However, inspection of the current source reveals some of these issues are marked "done" but their changes have not been fully applied — the code still contains duplication they identified. This issue consolidates the remaining unapplied work from those three issues into a single execution-focused issue.

## Problem
Six concrete issues remain after reviewing the current state of the codebase against the three prior issue proposals:

1. **Duplicate `shutdown_all()`** — `HttpServerLifecycleManager.shutdown_all()` and `ShutdownCoordinator.shutdown_all()` both implement SIGTERM→SIGKILL process iteration. Operationally observed: `HttpServerLifecycleManager.shutdown_all()` pops entries from `_http_procs`, clears `_http_pgids`, closes/clears `_stderr_files`, and clears `_stderr_log_paths`/`_last_health_check`; `ShutdownCoordinator.shutdown_all()` does none of this cleanup and never mutates `manager`'s state. Additionally, `ShutdownCoordinator.shutdown_all()` accepts a `terminator` parameter whose value is never used — callers-supplied terminators are ignored.

2. **Duplicate `_absorb_sigint_during_shutdown`** — `HttpServerLifecycleManager` defines this as a static method; `ShutdownCoordinator` also defines it. The one in `HttpServerLifecycleManager` should be removed once delegation is established.

3. **`terminate()` already deleted**: `ProcessTerminator.terminate()` was removed by the prior issue — zero callers remain. No action needed here.

4. **Circular import in `HealthChecker.compute_health_check_timeout()`** — Imports `MCPSERVER_HEALTH_TIMEOUT` from `agent.http_lifecycle` at runtime inside the method body. This is fragile under certain import orders.

5. **Hardcoded health-recheck interval** — `verify_running_async()` hardcodes the literal `10.0` instead of using `HealthChecker.HEALTH_RECHECK_INTERVAL_SEC = 10.0`. Both values are identical today but diverge on the next edit.

6. **`ProcessSnapshotProvider` is fully wired-in but unused** — Instantiated in `HttpServerLifecycleManager.__init__`, but `self._snapshot_provider` is never read by any method. Its public methods (`get_info()`, `get_snapshot()`, `list_processes()`) have no callers in `scripts/` or `tests/`. The entire 544-line module is dead code.

## Reason for Change
- Two independent shutdown implementations cause maintenance burden and risk of divergence — the two are not equivalent today, so consolidating them requires reconciling behavior, not just picking one
- The `terminator` parameter bug in `ShutdownCoordinator.shutdown_all()` is a latent correctness risk that becomes live once real callers route through it
- Circular import in `HealthChecker` will break under certain import orders
- Dead code (`terminate()`, `ProcessSnapshotProvider`) increases cognitive load and confuses readers about which code path is actually exercised
- Constant duplication (health-recheck interval) means the next developer will create a new `10.0` literal instead of reading the existing constant

## Implementation Intent
Establish a single delegation path per concern. Each item corresponds to one of the six problems identified above.

1. **Unified shutdown**: Before removing `HttpServerLifecycleManager.shutdown_all()`, first port its resource-cleanup steps (clearing `_http_pgids`, closing and clearing `_stderr_files`, clearing `_stderr_log_paths`/`_last_health_check`) into `ShutdownCoordinator.shutdown_all()`, and fix the dead `terminator` parameter override so a caller-supplied terminator is actually used. Only once `ShutdownCoordinator.shutdown_all()` is behavior-equivalent should `HttpServerLifecycleManager.shutdown_all()` become a thin delegating wrapper (kept callable for backward compat). Move `_absorb_sigint_during_shutdown` to `ShutdownCoordinator` as a static method only; delete the duplicate from `HttpServerLifecycleManager`.

2. **Delete unreachable `terminate()`**: Already done by the prior issue — no further action needed.

3. **Fix circular import**: Pass `MCPSERVER_HEALTH_TIMEOUT` as a parameter to `HealthChecker.compute_health_check_timeout()` or extract it to a shared constants module. Do not rely on lazy imports inside method bodies.

4. **Use `HealthChecker.HEALTH_RECHECK_INTERVAL_SEC`**: Replace the hardcoded `10.0` literal in `verify_running_async()` with a reference to `HealthChecker.HEALTH_RECHECK_INTERVAL_SEC`. Keep the rate-limiting wrapper logic (10-second interval) but delegate the actual HTTP request to `HealthChecker.verify_running_async()`. **Do not delegate the URL naively**: `HttpServerLifecycleManager.verify_running_async()` builds the health URL as `cfg.url.rstrip("/") + "/health"` while `HealthChecker.verify_running_async()` builds it as `url or getattr(cfg, "health_url", _DEFAULT_HEALTH_URL)`. `McpServerConfig` has no `health_url` field — only `url` — so the delegating call MUST pass `url=cfg.url.rstrip("/") + "/health"` explicitly to preserve current behavior.

5. **Decide on `ProcessSnapshotProvider` fate**: Either wire it up to an actual caller (e.g., add a `get_deep_process_snapshot()` method for diagnostics) or delete it as dead code. This is a product/architecture question — recommend filing a separate narrowly-scoped issue if wiring it up is desired. For this issue's scope, if deleting, ensure no callers exist before removal. If keeping, note that `http_lifecycle_process_snapshot.ProcessInfoSnapshot` was already renamed to `RawProcessSnapshot` by the prior issue — no rename needed here.

6. **Split `_cleanup_server_resources()`**: Separate into `_read_stderr_for_cleanup()` (returns stderr content) and `_clear_server_tracking_data()` (removes health check timestamps, stderr file handles, paths). Call them separately where needed.

Keep `HttpServerLifecycleManager` as the orchestrator but reduce it to < 150 lines by delegating to the six sub-modules. Keep `StartupFailure` and `HttpStartupError` where they are.

## Target Files or Areas
- `scripts/agent/http_lifecycle.py` — primary refactor target
- `scripts/agent/http_lifecycle_shutdown_coordinator.py` — consolidate shutdown logic here
- `scripts/agent/http_lifecycle_process_terminator.py` — delete unreachable `terminate()` method
- `scripts/agent/http_lifecycle_health_checker.py` — fix circular import, use recheck interval constant
- `scripts/agent/http_lifecycle_process_snapshot.py` — decide: wire up or delete; `ProcessInfoSnapshot`→`RawProcessSnapshot` rename already applied
- `scripts/agent/http_lifecycle_errors.py` — no changes expected
- `scripts/agent/http_lifecycle_command_validator.py` — no changes expected
- `scripts/agent/http_lifecycle_stderr_log_manager.py` — no changes expected
- `tests/agent/` — existing tests must still pass after refactor

## Required Changes
- Port `HttpServerLifecycleManager.shutdown_all()`'s resource-cleanup steps into `ShutdownCoordinator.shutdown_all()` (pgids, stderr file handles, stderr log paths, last-health-check timestamps) and fix the dead `terminator` parameter override, before turning `HttpServerLifecycleManager.shutdown_all()` into a delegating wrapper
- Move `_absorb_sigint_during_shutdown` to `ShutdownCoordinator` only; delete the duplicate from `HttpServerLifecycleManager`
- Delete `ProcessTerminator.terminate()` (already deleted by prior issue); `terminate_with_timeout()` remains the sole public termination method
- Fix `HealthChecker.compute_health_check_timeout()` circular import — pass timeout constant as parameter or extract to shared constants
- Replace the hardcoded `10.0` literal in `verify_running_async()` with `HealthChecker.HEALTH_RECHECK_INTERVAL_SEC`; delegate the HTTP request to `HealthChecker.verify_running_async()`, passing `url=cfg.url.rstrip("/") + "/health"` explicitly (do not rely on `HealthChecker`'s `getattr(cfg, "health_url", _DEFAULT_HEALTH_URL)` fallback — `McpServerConfig` has no `health_url` field)
- Split `_cleanup_server_resources()` into two methods: `_read_stderr_for_cleanup()` and `_clear_server_tracking_data()`
- Decide on `ProcessSnapshotProvider` fate: either wire it to an actual caller or delete as dead code; if keeping, note that `ProcessInfoSnapshot` was already renamed to `RawProcessSnapshot` by the prior issue — no rename needed here
- Ensure all existing tests pass without modification (behavior-preserving refactor)
- Add unit tests for each extracted standalone function (minimum coverage)

## Constraints
- Behavior-preserving: public API (`HttpServerLifecycleManager.start()`, `restart()`, `verify_running()`, `verify_running_async()`, `list_processes()`, `get_process_info()`, `get_process_snapshot()`, `shutdown_all()`) must remain unchanged
- No changes to config dataclass schemas or validator functions
- No changes to `StartupFailure` / `HttpStartupError` DTO shape
- Must not introduce new circular imports
- Existing test fixtures under `tests/agent/` covering `http_lifecycle*` must work without modification, except for the one delegation-order change implied by Implementation Intent #1 (cleanup must be ported before delegation, or existing shutdown tests will observe missing cleanup)
- `shutdown_all()` must remain callable on `HttpServerLifecycleManager` for backward compat — just delegate internally, and only after `ShutdownCoordinator.shutdown_all()` is verified behavior-equivalent
- If deleting `ProcessSnapshotProvider`, confirm no external callers exist first

## Acceptance Criteria
- [ ] `ShutdownCoordinator.shutdown_all()` performs the same resource cleanup (`_http_pgids`, `_stderr_files` close+clear, `_stderr_log_paths`, `_last_health_check`) that `HttpServerLifecycleManager.shutdown_all()` performs today, verified before the delegation switch
- [ ] `ShutdownCoordinator.shutdown_all()`'s `terminator` parameter, when supplied, is actually used instead of being overwritten
- [ ] `HttpServerLifecycleManager.shutdown_all()` delegates to `ShutdownCoordinator.shutdown_all()` instead of duplicating logic, only after the above two items are verified
- [ ] `_absorb_sigint_during_shutdown` exists only in `ShutdownCoordinator`
- [ ] `ProcessTerminator.terminate()` is already deleted (confirmed zero callers); `terminate_with_timeout()` remains the sole public termination method
- [ ] `HealthChecker.compute_health_check_timeout()` has no circular import
- [ ] `verify_running_async()` uses `HealthChecker.HEALTH_RECHECK_INTERVAL_SEC` instead of a hardcoded `10.0` literal
- [ ] `verify_running_async()` delegates to `HealthChecker.verify_running_async()`, passing `url=cfg.url.rstrip("/") + "/health"` explicitly
- [ ] `_cleanup_server_resources()` split into two separate methods
- [ ] `ProcessSnapshotProvider` is either wired to a live caller or deleted as dead code; if kept, `ProcessInfoSnapshot` was already renamed to `RawProcessSnapshot` by the prior issue
- [ ] All existing tests pass: `uv run pytest tests/agent/ -q --ignore=tests/integration/`
- [ ] New unit tests exist for each extracted standalone function (minimum 1 test each)
- [ ] No new circular imports introduced
- [ ] `ruff check` and `mypy` pass on all modified/new files

## Testing Expectations
- Run existing test suite: `uv run pytest tests/agent/ -q --ignore=tests/integration/`
- Add unit tests for each extracted standalone function
- Verify mypy passes: `uv run mypy scripts/agent/http_lifecycle*.py`
- Verify ruff passes: `uv run ruff check scripts/agent/http_lifecycle*.py`

## Documentation Impact
Update module docstrings in the four affected sub-modules to describe responsibility boundaries. No external documentation updates needed — the public API surface is unchanged.

## Out of Scope
- Adding new lifecycle operations (e.g., graceful restart with zero-downtime)
- Changing `StartupFailure` / `HttpStartupError` DTO shape
- Modifying config dataclass definitions
- Adding integration tests for the `/reload` command
- Removing `# noqa` suppressions unless clearly unjustified after refactor
- Changing `McpServerConfig` schema
- Making the health-recheck interval configurable via `McpServerConfig` (would require a config dataclass schema change, prohibited above) — resolving the pre-existing `10.0`-literal-vs-`HEALTH_RECHECK_INTERVAL_SEC`-constant duplication (Implementation Intent #4) is in scope; making the value itself configurable is not
- Deciding whether `ProcessSnapshotProvider` should be wired up to a real caller or deleted as dead code — this issue only resolves the name collision it causes (Implementation Intent #5); see Unresolved Questions Q1

## Dependencies
N/A: none

## Unresolved Questions
- **Q1**: Should `ProcessSnapshotProvider` be wired up to an actual caller (e.g., a new `get_deep_process_snapshot()` method for diagnostics), or deleted as dead code? The entire module (544 lines) is instantiated in `HttpServerLifecycleManager.__init__` but `self._snapshot_provider` is never read by any method, and its public methods have no callers anywhere in `scripts/` or `tests/`. This issue does not decide the question — the `ProcessInfoSnapshot` name collision with `_build_snapshot()` was already resolved by the prior issue's rename to `RawProcessSnapshot`. Recommend filing a separate, narrowly-scoped issue to make this decision, since it is a product/architecture question (does anything actually need deep `/proc` introspection?) rather than a mechanical refactor step.

- **Q2**: Should `ProcessTerminator.terminate_with_timeout()` return a boolean indicating whether the process exited gracefully vs. being killed? A plain `bool` cannot distinguish "process had already exited before this call" from "process exited gracefully after SIGTERM." Recommend a small enum (e.g., `ALREADY_EXITED` / `GRACEFUL` / `KILLED`) as the return type instead. Both current call sites discard the return value already, so changing it from `None` to an enum is not a breaking change for any existing caller.

- **Q3**: Is the 10-second rate limit in `verify_running_async()` appropriate for production use, or should it be configurable via `McpServerConfig`? Not configurable in this issue's scope — making it configurable would require a `McpServerConfig` schema change, which Constraints prohibits. What's actionable now: fix the duplication between the hardcoded `10.0` literal and `HealthChecker.HEALTH_RECHECK_INTERVAL_SEC` (Implementation Intent #4); whether to make the interval configurable at all is a separate, later issue.

## AI Implementation Instruction
Do not rewrite unrelated files. Preserve the public API: `HttpServerLifecycleManager.start()`, `restart()`, `verify_running()`, `verify_running_async()`, `list_processes()`, `get_process_info()`, `get_process_snapshot()`, `shutdown_all()`. Each extracted module must have a clear responsibility boundary — do not create cross-cutting dependencies between the modules. Test after each extraction step, not just at the end. For the shutdown consolidation specifically: port `ShutdownCoordinator.shutdown_all()`'s cleanup and fix its `terminator` bug first, run the existing shutdown tests against it directly, and only then switch `HttpServerLifecycleManager.shutdown_all()` to delegate — do not flip the delegation before the cleanup parity is verified. Stop and report if you find a circular import that cannot be resolved without further changes.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-115306
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle_process_terminator.py, scripts/agent/http_lifecycle_health_checker.py, scripts/agent/http_lifecycle_process_snapshot.py
