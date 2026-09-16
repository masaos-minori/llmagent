# Refactor scripts/agent/http_lifecycle.py into smaller, testable units

## Priority
Medium

## Summary
Split `scripts/agent/http_lifecycle.py` (532 lines) into focused modules matching its declared six-concern architecture. Eliminate cross-cutting duplication between `HttpServerLifecycleManager`, `ShutdownCoordinator`, and `ProcessSnapshotProvider`. Reduce cyclomatic complexity and improve test isolation.

## Background
The module was extracted from `lifecycle.py` and partially refactored into six concern-specific sub-modules (CommandValidator, StderrLogManager, ProcessTerminator, HealthChecker, ProcessSnapshotProvider, ShutdownCoordinator). However, the main `HttpServerLifecycleManager` class retains ~280 lines of control flow that should have been delegated to those sub-modules. The docstring at line 8 explicitly declares this composition intent but the implementation does not match.

## Problem
The file violates Single Responsibility Principle at multiple levels:

1. **Cross-module duplication — corrected this revision, not actually "identical"**: `shutdown_all()` exists in both `HttpServerLifecycleManager` (line 483) and `ShutdownCoordinator.shutdown_all()` (`http_lifecycle_shutdown_coordinator.py:50`). Verified by direct comparison: the SIGINT guard is genuinely duplicated, but the process-iteration bodies are **not** identical — `HttpServerLifecycleManager.shutdown_all()` pops each entry from `_http_procs` and also clears `_http_pgids`, closes and clears `_stderr_files`, and clears `_stderr_log_paths`/`_last_health_check`; `ShutdownCoordinator.shutdown_all()` does none of this cleanup and never mutates `manager`'s state at all. `ShutdownCoordinator.shutdown_all()` also has a bug independent of this issue: it accepts a `terminator` parameter, assigns `terminator = terminator or manager._process_terminator` (line 76), then unconditionally overwrites it two lines later with `terminator = manager._process_terminator` (line 85) — the parameter is dead on arrival. **Severity note added this revision**: `ShutdownCoordinator.shutdown_all()` itself currently has zero callers anywhere in `scripts/` or `tests/` (confirmed by grep) — only `HttpServerLifecycleManager.shutdown_all()` is ever invoked in practice today. This bug therefore lives entirely in dead code right now; it only becomes a live concern once Implementation Intent #1's delegation switch actually routes real callers through `ShutdownCoordinator.shutdown_all()`, which is exactly why fixing it is a precondition for that switch, not an independent latent risk. `_absorb_sigint_during_shutdown` is similarly duplicated (this part *is* a simple, safe-to-delete duplication).

2. **Process snapshot responsibility leak — corrected this revision, delegation as originally proposed is not possible**: `_build_snapshot()` (line 188) constructs `agent.services.models.ProcessInfoSnapshot` (7 fields: server_key/managed/pid/pgid/running/last_exit_code/stderr_log) directly. `ProcessSnapshotProvider.get_info()` (`http_lifecycle_process_snapshot.py:486`) returns a **different dataclass that happens to share the same name** — `http_lifecycle_process_snapshot.ProcessInfoSnapshot`, with 20+ `/proc`-derived fields (memory_info, io_counters, numa_maps, syscall_info, stack_trace, etc.). These are not interchangeable; routing `_build_snapshot()` through `get_info()` would change `get_process_info()`'s public return type, violating the Constraints' "public API must remain unchanged." (Precision note added this revision: calling this a "name collision" overstates the runtime risk — `http_lifecycle.py` imports only `agent.services.models.ProcessInfoSnapshot` by name (line 35), so no import-time shadowing actually occurs today; the real problem is the maintainability hazard of two same-named-but-incompatible dataclasses living in sibling modules, which is confusing to a reader and would become a real collision the moment anyone imports both names into the same file.) Further verified: `ProcessSnapshotProvider` is constructed in `HttpServerLifecycleManager.__init__` (line 89, `self._snapshot_provider = ...`) but that attribute is **never read anywhere** — `get_info()`, `get_snapshot()`, and `list_processes()` have no callers in `scripts/` or `tests/` (confirmed by grep). The entire 544-line module is wired in but dead.

3. **Health check verification duplication**: `verify_running_async()` (line 157) performs HTTP `/health` polling inline instead of using `HealthChecker.verify_running_async()`.

4. **Resource cleanup mixing**: `_cleanup_server_resources()` (line 178) handles both stderr log reading AND health check timestamp clearing — two unrelated concerns.

5. **ProcessTerminator internal duplication — corrected this revision, not shared logic to merge, but dead code to delete**: `terminate()` and `terminate_with_timeout()` do share ~40 lines of SIGTERM→SIGKILL escalation logic, but verified by grep across `scripts/` and `tests/`: `ProcessTerminator.terminate()` has zero callers anywhere in the codebase (production or test) — only `terminate_with_timeout()` is ever invoked (`http_lifecycle_shutdown_coordinator.py:87`, `http_lifecycle.py:144`). There is no shared logic to reconcile between two live call paths; `terminate()` is simply unreachable code.

6. **ProcessSnapshotProvider over-fetching**: Reads ALL fields from `/proc/[pid]` regardless of caller need (20+ fields per snapshot), many of which are never used by any consumer — compounded by finding #2 above: the entire provider currently has no consumer at all.

7. **Multiple `# noqa` suppressions**: Lines 23, 25, 291 carry security/type suppression comments that are difficult to justify without deeper review.

8. **`list_processes()` duplication (found this revision, not in the original Problem list)**: `ProcessSnapshotProvider.list_processes(manager)` (`http_lifecycle_process_snapshot.py:527-543`) independently reimplements the same role as `HttpServerLifecycleManager.list_processes()` (line 218), iterating `manager._http_procs` directly. Like finding #2, this copy has no callers — it compounds the "dead provider" finding rather than being an actively used duplication.

## Reason for Change
- `HttpServerLifecycleManager.start()` has cyclomatic complexity exceeding 15 (nested loops, conditional branches per section, validator try/catch blocks, outcome classification)
- Two independent shutdown implementations cause maintenance burden and risk of divergence — and, per Problem #1, the two are not equivalent today, so consolidating them requires reconciling behavior, not just picking one
- The declared six-module architecture is incomplete — several concerns remain un-delegated, and one of the six modules (`ProcessSnapshotProvider`) turns out to be fully un-delegated in the sense that nothing calls it at all (Problem #2, #8)
- No unit tests exercise `_interruptible_poll_sleep`, `_create_and_validate_proc`, or `_health_poll_until_ready` independently
- `ProcessTerminator`'s dual public methods suggested the class was extended incrementally without a clean design — verified this revision to be simpler than that: `terminate()` is unreachable, not a design smell to reconcile

## Implementation Intent
Extract concerns into separate modules/functions. Items 1, 2, and 5 are revised this revision from their original form — see the cited Problem findings for why.

1. **Unified shutdown, cleanup-preserving**: Before removing `HttpServerLifecycleManager.shutdown_all()`, first port its resource-cleanup steps (clearing `_http_pgids`, closing and clearing `_stderr_files`, clearing `_stderr_log_paths`/`_last_health_check`) into `ShutdownCoordinator.shutdown_all()`, and fix the dead `terminator` parameter (Problem #1) so a caller-supplied terminator is actually used instead of being silently overwritten. Only once `ShutdownCoordinator.shutdown_all()` is behavior-equivalent to today's `HttpServerLifecycleManager.shutdown_all()` should `HttpServerLifecycleManager.shutdown_all()` become a thin delegating wrapper (kept callable for backward compat per Constraints — see Unresolved Questions Q1). Move `_absorb_sigint_during_shutdown` to `ShutdownCoordinator` as a static method only. Delete the duplicate from `HttpServerLifecycleManager`.

2. **Snapshot: no delegation — resolve the name collision instead**: `_build_snapshot()` is **not** delegated to `ProcessSnapshotProvider.get_info()` — the two return incompatible dataclasses of the same name (Problem #2), and `ProcessSnapshotProvider` has no live consumer to preserve behavior against. Keep `_build_snapshot()`'s current implementation as-is. The only change here is renaming `http_lifecycle_process_snapshot.ProcessInfoSnapshot` to a distinct name (e.g. `RawProcessSnapshot`) so the two same-named-but-different dataclasses stop reading as duplicates of each other. Whether `ProcessSnapshotProvider` should be wired up to an actual caller, or removed as dead code, is out of scope for this issue — see Unresolved Questions Q5.

3. **Health check delegation — URL-construction risk found this revision, must be handled explicitly**: Replace `verify_running_async()` body with a call to `HealthChecker.verify_running_async()`. Keep the rate-limiting wrapper logic (10-second interval) but delegate the actual HTTP request. While doing so, resolve the pre-existing constant duplication: `HealthChecker` already declares `_HEALTH_RECHECK_INTERVAL_SEC = 10.0` (`http_lifecycle_health_checker.py:14`) but nothing reads it — `verify_running_async()` hardcodes the literal `10.0` instead (`http_lifecycle.py:162`). Make the delegated call use `HealthChecker`'s constant rather than keeping two independent `10.0` literals (see Unresolved Questions Q3). **Do not delegate the URL naively**: `HttpServerLifecycleManager.verify_running_async()` builds the health URL as `cfg.url.rstrip("/") + "/health"` (`http_lifecycle.py:171`), while `HealthChecker.verify_running_async()` builds it as `url or getattr(cfg, "health_url", _DEFAULT_HEALTH_URL)` (`http_lifecycle_health_checker.py:49`). `McpServerConfig` (`shared/mcp_config.py:70-96`) has no `health_url` field at all — only `url` — so if the delegated call is made without passing `url=` explicitly, `getattr` always falls through to `_DEFAULT_HEALTH_URL` ("http://localhost:8080/health"), and every server would be health-checked against the same wrong, hardcoded address regardless of its actual `cfg.url`. The delegating call **must** pass `url=cfg.url.rstrip("/") + "/health"` explicitly to `HealthChecker.verify_running_async()` to preserve current behavior.

4. **Cleanup separation**: Split `_cleanup_server_resources()` into two methods: `_read_stderr_for_cleanup()` (returns stderr content) and `_clear_server_tracking_data()` (removes health check timestamps, stderr file handles, paths). Call them separately where needed.

5. **ProcessTerminator: delete unreachable code, don't merge**: `terminate()` has zero callers (Problem #5) — delete it rather than merging it with `terminate_with_timeout()`. No signature reconciliation is needed since there is only one live method to keep.

6. **ProcessSnapshotProvider selective fetching**: Add a `fields` parameter to `from_proc_pid()` and `get_info()` so callers can request only needed fields. Accept `fields: frozenset[str] | None = None` as a keyword-only parameter (not a positional list) — this makes the parameter's set semantics explicit and immune to the reordering concern that motivated Unresolved Questions Q2, without needing a non-standard type. Default behavior remains full fetch for backward compatibility. Given finding #2/#8 (no live consumer), this fetches value only once `ProcessSnapshotProvider` has an actual caller (see Q5) — otherwise it is optimizing dead code.

Keep `HttpServerLifecycleManager` as the orchestrator but reduce it to < 150 lines by delegating to the six sub-modules. Keep `StartupFailure` and `HttpStartupError` where they are. (`ConfigReloadOutcome`/`ConfigReloadValidationError`, mentioned in an earlier draft of this line, belong to the unrelated `config_reload.py` refactor issue — neither class exists in `http_lifecycle.py`; corrected this revision.)

## Target Files or Areas
- `scripts/agent/http_lifecycle.py` — primary refactor target
- `scripts/agent/http_lifecycle_shutdown_coordinator.py` — consolidate shutdown logic here
- `scripts/agent/http_lifecycle_process_terminator.py` — delete unreachable `terminate()` method (not a merge — see Problem #5)
- `scripts/agent/http_lifecycle_health_checker.py` — add rate-limited verify wrapper
- `scripts/agent/http_lifecycle_process_snapshot.py` — add selective field fetching
- `scripts/agent/http_lifecycle_stderr_log_manager.py` — no changes needed (already clean)
- `scripts/agent/http_lifecycle_command_validator.py` — no changes needed (already clean)
- `scripts/agent/http_lifecycle_errors.py` — no changes needed (already clean)
- `tests/agent/` — existing tests must still pass after refactor

## Required Changes
- Port `HttpServerLifecycleManager.shutdown_all()`'s resource-cleanup steps into `ShutdownCoordinator.shutdown_all()` (pgids, stderr file handles, stderr log paths, last-health-check timestamps) and fix the dead `terminator` parameter override at `http_lifecycle_shutdown_coordinator.py:85`, before turning `HttpServerLifecycleManager.shutdown_all()` into a delegating wrapper
- Move `_absorb_sigint_during_shutdown` to `ShutdownCoordinator` only
- Rename `http_lifecycle_process_snapshot.ProcessInfoSnapshot` to a distinct name (e.g. `RawProcessSnapshot`) to resolve the name collision with `agent.services.models.ProcessInfoSnapshot` — do **not** route `_build_snapshot()` through `ProcessSnapshotProvider.get_info()` (incompatible return types; see Implementation Intent #2)
- Replace `verify_running_async()` body with `HealthChecker.verify_running_async()` call, passing `url=cfg.url.rstrip("/") + "/health"` explicitly (do not rely on `HealthChecker`'s `getattr(cfg, "health_url", _DEFAULT_HEALTH_URL)` fallback — `McpServerConfig` has no `health_url` field, so an implicit call would silently health-check the wrong address), and make it use `HealthChecker._HEALTH_RECHECK_INTERVAL_SEC` instead of the currently-hardcoded `10.0` literal at `http_lifecycle.py:162`
- Split `_cleanup_server_resources()` into two methods
- Delete `ProcessTerminator.terminate()` (zero callers — do not merge it with `terminate_with_timeout()`, there is nothing to reconcile)
- Add optional, keyword-only `fields: frozenset[str] | None` parameter to `ProcessSnapshotProvider.from_proc_pid()` and `get_info()`
- Ensure all existing tests pass without modification (behavior-preserving refactor)
- Add unit tests for each extracted standalone function (minimum coverage)

## Constraints
- Behavior-preserving: public API (`HttpServerLifecycleManager.start()`, `restart()`, `verify_running()`, `verify_running_async()`, `list_processes()`, `get_process_info()`, `get_process_snapshot()`, `shutdown_all()`) must remain unchanged
- No changes to config dataclass schemas or validator functions
- No changes to `StartupFailure` / `HttpStartupError` DTO shape
- Must not introduce new circular imports
- ~~Existing test fixtures in `tests/agent/commands/test_agent_cmd_config.py` and `tests/agent/services/test_config_reload*.py` must work without modification~~ **Removed this revision — copy-paste artifact from the unrelated `config_reload.py` refactor issue.** This issue's actual test surface is `tests/agent/` broadly (see Testing Expectations); the correct constraint is that existing test fixtures under `tests/agent/` covering `http_lifecycle*` must work without modification, except for the one delegation-order change implied by Implementation Intent #1 (cleanup must be ported before delegation, or existing shutdown tests will observe missing cleanup)
- `shutdown_all()` must remain callable on `HttpServerLifecycleManager` for backward compat — just delegate internally, and only after `ShutdownCoordinator.shutdown_all()` is verified behavior-equivalent (see Implementation Intent #1)

## Acceptance Criteria
- [ ] `ShutdownCoordinator.shutdown_all()` performs the same resource cleanup (`_http_pgids`, `_stderr_files` close+clear, `_stderr_log_paths`, `_last_health_check`) that `HttpServerLifecycleManager.shutdown_all()` performs today, verified before the delegation switch
- [ ] `ShutdownCoordinator.shutdown_all()`'s `terminator` parameter, when supplied, is actually used instead of being overwritten
- [ ] `HttpServerLifecycleManager.shutdown_all()` delegates to `ShutdownCoordinator.shutdown_all()` instead of duplicating logic, only after the above two items are verified
- [ ] `_absorb_sigint_during_shutdown` exists only in `ShutdownCoordinator`
- [ ] `_build_snapshot()` keeps its current implementation (no delegation to `ProcessSnapshotProvider.get_info()` — the return types are incompatible)
- [ ] `http_lifecycle_process_snapshot.ProcessInfoSnapshot` is renamed so it no longer shares a name with `agent.services.models.ProcessInfoSnapshot`
- [ ] `verify_running_async()` delegates to `HealthChecker.verify_running_async()`, passing `url=cfg.url.rstrip("/") + "/health"` explicitly rather than relying on `HealthChecker`'s `health_url`-attribute fallback (which `McpServerConfig` does not have), and the delegated call reads `HealthChecker`'s `_HEALTH_RECHECK_INTERVAL_SEC` rather than a separately hardcoded `10.0`
- [ ] `_cleanup_server_resources()` split into two separate methods
- [ ] `ProcessTerminator.terminate()` is deleted (confirmed zero callers); `terminate_with_timeout()` remains the sole public termination method
- [ ] `ProcessSnapshotProvider.from_proc_pid()` accepts an optional, keyword-only `fields: frozenset[str] | None` parameter
- [ ] All existing tests pass: `pytest tests/agent/ -q --ignore=tests/integration/`
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
- Making the health-recheck interval configurable via `McpServerConfig` (would require a config dataclass schema change, prohibited above) — resolving the pre-existing `10.0`-literal-vs-`_HEALTH_RECHECK_INTERVAL_SEC`-constant duplication (Implementation Intent #3) is in scope; making the value itself configurable is not
- Deciding whether `ProcessSnapshotProvider` should be wired up to a real caller or deleted as dead code — this issue only resolves the name collision it causes (Implementation Intent #2); see Unresolved Questions Q5

## Dependencies
N/A: none

## Unresolved Questions
All four original questions below are resolved as of this revision; each entry keeps the original question (struck through) for history alongside its resolution. A fifth question, found during this same review, is added at the end.

- ~~Should `shutdown_all()` on `HttpServerLifecycleManager` raise if called directly (since the real work is in `ShutdownCoordinator`)?~~ **Resolved: no, it must not raise.** Constraints explicitly requires `shutdown_all()` to "remain callable on `HttpServerLifecycleManager` for backward compat — just delegate internally"; raising would violate that constraint outright. A `logger.debug()`-level note that the call was delegated is acceptable if desired, but is not required.

- ~~Should `ProcessSnapshotProvider.from_proc_pid()` accept a `frozenset[str]` of field names rather than a list?~~ **Resolved: yes, `frozenset[str] | None`, and keyword-only.** The reordering risk the question raised is really a calling-convention issue, not a type issue — making `fields` keyword-only (`*, fields: frozenset[str] | None = None`) removes any positional-order dependency regardless of the container type chosen. `frozenset` is still the better choice on its own merits: it communicates "an unordered set of names," is hashable (usable as a cache key later if needed), and supports cheap validity checks like `fields - _ALL_FIELD_NAMES`. See Implementation Intent #6.

- ~~Is the 10-second rate limit in `verify_running_async()` appropriate for production use, or should it be configurable via `McpServerConfig`?~~ **Resolved: not configurable in this issue's scope; fix the duplication instead.** Making it configurable would require a `McpServerConfig` schema change, which Constraints prohibits. What's actually actionable now: `HealthChecker._HEALTH_RECHECK_INTERVAL_SEC = 10.0` (`http_lifecycle_health_checker.py:14`) is declared but never read — `verify_running_async()` hardcodes its own `10.0` literal instead (`http_lifecycle.py:162`). Fix that duplication as part of the health-check delegation (Implementation Intent #3); whether to make the interval configurable at all is a separate, later issue (see Out of Scope).

- ~~Should `ProcessTerminator.terminate_with_timeout()` return a boolean indicating whether the process exited gracefully vs. being killed?~~ **Resolved: return a 3-state result, not a bare `bool`.** A plain `bool` cannot distinguish "process had already exited before this call" from "process exited gracefully after SIGTERM" — both would report the same `True`/truthy-ish value, which is exactly the ambiguity the question was trying to resolve. Recommend a small enum (e.g. `ALREADY_EXITED` / `GRACEFUL` / `KILLED`) as the return type instead. `ProcessTerminator` is not in the Constraints' public-API list (only `HttpServerLifecycleManager`'s methods are), and both current call sites (`http_lifecycle_shutdown_coordinator.py:87`, `http_lifecycle.py:144`) discard the return value already, so changing it from `None` to an enum is not a breaking change for any existing caller.

- **Q5 (new this revision)**: Should `ProcessSnapshotProvider` be wired up to an actual caller (e.g. a new `get_deep_process_snapshot()` method for diagnostics), or deleted as dead code? Found during this review: the entire module (544 lines) is instantiated in `HttpServerLifecycleManager.__init__` but `self._snapshot_provider` is never read by any method, and `get_info()`/`get_snapshot()`/`list_processes()` have no callers anywhere in `scripts/` or `tests/`. This issue does not decide the question (see Out of Scope) — it only resolves the `ProcessInfoSnapshot` name collision this dead module causes for `_build_snapshot()` (Implementation Intent #2). Recommend filing a separate, narrowly-scoped issue to make this decision, since it is a product/architecture question (does anything actually need deep `/proc` introspection?) rather than a mechanical refactor step.

## AI Implementation Instruction
Do not rewrite unrelated files. Preserve the public API: `HttpServerLifecycleManager.start()`, `restart()`, `verify_running()`, `verify_running_async()`, `list_processes()`, `get_process_info()`, `get_process_snapshot()`, `shutdown_all()`. Each extracted module must have a clear responsibility boundary — do not create cross-cutting dependencies between the modules. Test after each extraction step, not just at the end. For the shutdown consolidation specifically: port `ShutdownCoordinator.shutdown_all()`'s cleanup and fix its `terminator` bug first, run the existing shutdown tests against it directly, and only then switch `HttpServerLifecycleManager.shutdown_all()` to delegate — do not flip the delegation before the cleanup parity is verified. Stop and report if you find a circular import that cannot be resolved without further changes.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260915-102515
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_shutdown_coordinator.py, scripts/agent/http_lifecycle_process_terminator.py, scripts/agent/http_lifecycle_health_checker.py, scripts/agent/http_lifecycle_process_snapshot.py
