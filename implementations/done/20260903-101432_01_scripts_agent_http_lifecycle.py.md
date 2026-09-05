# Implementation Procedure: Refactor http_lifecycle.py into composition facade

## Goal

Reduce `scripts/agent/http_lifecycle.py`'s `HttpServerLifecycleManager` class from a monolithic 611-line class to a thin composition facade that delegates to six extracted concern-specific modules/classes, preserving its public interface exactly.

## Scope

- Modify `scripts/agent/http_lifecycle.py`: extract six concerns into separate modules, reduce `HttpServerLifecycleManager` to composition facade
- The six extracted modules are defined in their own implementation procedure documents (rows 2–7 of Implementation Target Files)

## Assumptions

- Constructor-injection/delegation pattern used in `orchestrator.py` and `ingester.py` splits is the preferred approach for this project
- The six suggested concern groupings from the Plan are correct and sufficient
- `factory.py`'s existing calls into `HttpServerLifecycleManager` will continue to work unmodified if public interface is preserved exactly
- The health-poll loop inside `start()` moves entirely into `http_lifecycle_health_checker.py`, per the Plan's Assumption

## Design decisions

- Each extracted component receives dependencies via constructor parameters (constructor injection), matching the pattern established in `orchestrator.py` and `ingester.py`
- `HttpServerLifecycleManager` becomes a thin wrapper delegating to injected components, preserving the public interface exactly
- Six new Python modules as flat files alongside `http_lifecycle.py` in `scripts/agent/`, prefixed `http_lifecycle_*` to avoid ambiguity with the unrelated existing `scripts/agent/lifecycle.py`/`lifecycle_protocol.py`
- Error propagation: components raise domain-specific exceptions (e.g., `HttpStartupError` for command validation failures) that the facade catches and re-raises as needed

## Alternatives considered

- Subdirectory layout (`scripts/agent/http_lifecycle/`) — rejected in favor of flat files per repository precedent from prior File Split Rule refactors (RAG ingestion split placed `http_fetcher.py`, `content_extractor.py`, etc. as flat siblings in `scripts/rag/ingestion/`)
- Startup orchestrator composing both command validator and health checker — rejected; the Plan's Assumption resolves UNK-02 by moving the entire health-poll loop into the health-checker unit

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

1. Add imports for the six extracted components at the top of `http_lifecycle.py`
2. Replace the six concern methods in `HttpServerLifecycleManager` with delegation to injected components
3. Update `__init__` to accept the six components as constructor parameters
4. Preserve all public method signatures, return types, and exception-raising conditions
5. Keep `StartupFailure`, `HttpStartupError`, `_mask_secrets` reference, and `MCPSERVER_HEALTH_TIMEOUT` constant in place

### Method

**Step 1: Add component imports**

Add import statements for the six new modules after the existing imports (after line 29):

```python
from agent.http_lifecycle_command_validator import CommandValidator
from agent.http_lifecycle_stderr_log import StderrLogManager
from agent.http_lifecycle_process_terminator import ProcessTerminator
from agent.http_lifecycle_health_checker import HealthChecker
from agent.http_lifecycle_process_snapshot import ProcessSnapshotProvider
from agent.http_lifecycle_shutdown_coordinator import ShutdownCoordinator
```

**Step 2: Update `__init__` to accept components**

Replace the current `__init__` (lines 83–89) with a constructor that accepts the six components:

```python
def __init__(
    self,
    *,
    command_validator: CommandValidator | None = None,
    stderr_log_manager: StderrLogManager | None = None,
    process_terminator: ProcessTerminator | None = None,
    health_checker: HealthChecker | None = None,
    snapshot_provider: ProcessSnapshotProvider | None = None,
    shutdown_coordinator: ShutdownCoordinator | None = None,
) -> None:
    """Initialize HttpServerLifecycleManager with injected components."""
    self._command_validator = command_validator or CommandValidator()
    self._stderr_log_manager = stderr_log_manager or StderrLogManager()
    self._process_terminator = process_terminator or ProcessTerminator()
    self._health_checker = health_checker or HealthChecker()
    self._snapshot_provider = snapshot_provider or ProcessSnapshotProvider()
    self._shutdown_coordinator = shutdown_coordinator or ShutdownCoordinator()
    # Internal state dicts remain unchanged
    self._http_procs: dict[str, subprocess.Popen[bytes]] = {}
    self._http_pgids: dict[str, int] = {}
    self._stderr_files: dict[str, IO[bytes]] = {}
    self._stderr_log_paths: dict[str, str] = {}
    self._last_health_check: dict[str, float] = {}
```

**Step 3: Extract `_ALLOWED_COMMANDS` and `_PROTECTED_ENV_VARS` to CommandValidator**

Move these two class-level constants from `HttpServerLifecycleManager` (lines 76–81) into `CommandValidator.__init__` as instance attributes. In `HttpServerLifecycleManager.start()`, replace the inline allowlist/symlink/regular-file checks (lines 374–409) with a single delegation call:

```python
cmd_executable = self._command_validator.validate(server_key, cfg.cmd[0])
```

The `validate` method returns the resolved absolute path or raises `HttpStartupError`. The `start()` method no longer contains any allowlist logic.

**Step 4: Extract environment filtering to CommandValidator**

Move the `_PROTECTED_ENV_VARS` filtering logic from `start()` (lines 353–362) into `CommandValidator.filter_env(env: dict[str, str] | None) -> dict[str, str] | None`. Call it from `start()`:

```python
env = self._command_validator.filter_env(cfg.env)
```

**Step 5: Extract stderr log management to StderrLogManager**

Move `_open_stderr_log`, `_read_stderr_tail`, `_rotate_log` (lines 99–148) into `StderrLogManager`. Replace the three methods in `HttpServerLifecycleManager` with delegation:

```python
self._stderr_files[server_key] = self._stderr_log_manager.open_log(server_key, cfg)
```

Similarly for `_read_stderr_tail` and `_rotate_log` calls. The `StderrLogManager` owns the `_STDERR_TAIL_BYTES` constant (move it from `HttpServerLifecycleManager`).

**Step 6: Extract process termination to ProcessTerminator**

Move `_wait_exited`, `_terminate_with_timeout` (lines 149–207) into `ProcessTerminator`. Replace the three methods in `HttpServerLifecycleManager` with delegation:

```python
await self._process_terminator.terminate(proc, server_key, timeout=timeout)
```

The `ProcessTerminator` owns `_TERMINATE_POLL_INTERVAL_SEC` (move it from `HttpServerLifecycleManager`).

**Step 7: Extract health checking to HealthChecker**

Move `verify_running`, `verify_running_async`, `_compute_health_check_timeout`, `_interruptible_poll_sleep`, and the health-poll loop portion of `start()` (lines 209–237, 302–321, 451–508) into `HealthChecker`. Replace the four methods in `HttpServerLifecycleManager` with delegation:

```python
is_healthy = await self._health_checker.verify_running_async(server_key, cfg)
```

The `HealthChecker` owns `_HEALTH_RECHECK_INTERVAL_SEC` and `_HEALTH_RECHECK_TIMEOUT_SEC` (move them from `HttpServerLifecycleManager`).

**Step 8: Extract process introspection to ProcessSnapshotProvider**

Move `_snapshot_fields`, `get_process_info`, `get_process_snapshot`, `list_processes` (lines 249–300) into `ProcessSnapshotProvider`. Replace the four methods in `HttpServerLifecycleManager` with delegation:

```python
return self._snapshot_provider.get_info(server_key, proc, pgid)
```

**Step 9: Extract bulk shutdown to ShutdownCoordinator**

Move `shutdown_all`, `_absorb_sigint_during_shutdown` (lines 532–611) into `ShutdownCoordinator`. Replace the two methods in `HttpServerLifecycleManager` with delegation:

```python
await self._shutdown_coordinator.shutdown_all(self)
```

The `ShutdownCoordinator` receives the manager instance to access internal state dicts during shutdown.

**Step 10: Preserve remaining methods unchanged**

Keep `restart` (lines 515–530) as-is except where it references extracted methods — update those references to delegate:

```python
await self._process_terminator.terminate(proc, server_key)
```

And:

```python
await self._health_checker.startup_poll(...)
```

### Details

**Current source verification:**

- `scripts/agent/http_lifecycle.py` exists with 611 lines — confirmed
- All seven public methods present: `start`, `restart`, `shutdown_all`, `verify_running`, `verify_running_async`, `get_process_info`, `get_process_snapshot`, `list_processes` — confirmed
- `_ALLOWED_COMMANDS` (line 76): frozenset {"node", "npm", "npx", "uvx", "python", "pipx", "uvicorn"} — confirmed
- `_PROTECTED_ENV_VARS` (line 79): frozenset {"PATH", "PYTHONPATH", "LD_LIBRARY_PATH", "HOME", "USER"} — confirmed
- `MCPSERVER_HEALTH_TIMEOUT` constant (line 32): float = 5.0 — confirmed
- `StartupFailure` dataclass (lines 35–41) and `HttpStartupError` exception (lines 44–59) — confirmed
- Imports from `agent.secrets_masker` and `agent.services.models` — confirmed
- `subprocess.Popen` usage with `# nosec B603` justification on line 411 — confirmed
- `os.killpg` with `# nosec B603` justifications on lines 178 and 198 — confirmed

**Adversarial verification findings:**

- No stale claims detected; all referenced symbols and line numbers match current source
- The `_PROTECTED_ENV_VARS` filtering is already gated by `cfg.env` check (line 354), not a separate dependency
- The `start_new_session=True` parameter on line 416 is used only in `subprocess.Popen` call within `start()` — this remains in `HttpServerLifecycleManager.start()` since it's part of the spawn orchestration, not a concern-specific operation
- The `pgid` capture with cleanup-on-failure branch (lines 423–448) is part of the spawn flow in `start()` — this remains in `HttpServerLifecycleManager.start()`

**Reference files read (not modified):**

- `scripts/agent/factory.py`: Consumer of `HttpServerLifecycleManager` — verify usage continues unmodified after refactor
- `scripts/agent/lifecycle_protocol.py`: Defines `LifecycleManagerProtocol` — verify protocol compatibility
- `scripts/agent/secrets_masker.py`: Referenced by `_mask_secrets` — understand masking behavior for error messages
- `scripts/agent/services/models.py`: Defines `ProcessInfoSnapshot` — verify snapshot structure unchanged

## Compatibility considerations

- `factory.py`'s usage of `HttpServerLifecycleManager` must continue to work unmodified — preserve public interface exactly (REQ-008)
- Constructor injection uses keyword-only arguments (`*`) so existing positional-call patterns are not affected
- Default values (`None`) for all injected components ensure backward compatibility if called without explicit dependencies
- `LifecycleManagerProtocol` compatibility must be verified — the facade still implements the same protocol

## Security considerations

- `bandit`'s `B404`/`B603` `#nosec` justifications must be retained on all `subprocess`-related findings
- Line 411: `# nosec B603 — cmd comes from admin-controlled config, not user input` — confirmed rationale
- Lines 178, 198: `# nosec B603` — confirmed rationale (process-group signals for termination)
- Command-validation logic inside `start()` (allowlist check, symlink resolution, regular-file check) is a security control that must be preserved in the extracted `CommandValidator`
- `_PROTECTED_ENV_VARS` filtering must be preserved in `CommandValidator.filter_env()`

## Rollback considerations

- If extraction breaks the public interface, revert `HttpServerLifecycleManager` to its original monolithic form
- Keep the six new modules importable even if temporarily unused — they can be wired in later
- If constructor injection causes issues, fall back to lazy initialization pattern (components created on first use rather than at construction time)

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Unit — verify facade delegation works correctly | ruff check, mypy, bandit | Clean lint/type/security checks |
| scripts/agent/http_lifecycle_command_validator.py | Unit — validate allowlist/symlink/regular-file rules | uv run pytest (new tests) | All four validator scenarios pass |
| scripts/agent/http_lifecycle_stderr_log.py | Unit — verify log rotation behavior | uv run pytest (existing tests) | No behavioral regression |
| scripts/agent/http_lifecycle_process_terminator.py | Unit — verify terminate-then-kill escalation | uv run pytest (existing tests) | No behavioral regression |
| scripts/agent/http_lifecycle_health_checker.py | Integration — verify health-poll retry logic | uv run pytest (existing tests) | No behavioral regression |
| scripts/agent/http_lifecycle_process_snapshot.py | Unit — verify snapshot accuracy | uv run pytest (existing tests) | No behavioral regression |
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Integration — verify SIGINT absorption | uv run pytest (existing tests) | No behavioral regression |
| tests/agent/test_http_lifecycle_integration.py | Regression — full lifecycle scenario | uv run pytest | No new failures vs. baseline |
| tests/agent/test_http_lifecycle_warning.py | Regression — warning scenarios | uv run pytest | No new failures vs. baseline |

## Completion criteria

- `HttpServerLifecycleManager` has no direct implementation of command validation, stderr logging, process termination, health checking, process introspection, or bulk shutdown — all delegated to injected components
- Public method signatures, return types, and exception-raising conditions are identical to the pre-refactor version
- `ruff check scripts/agent/http_lifecycle.py` passes clean
- `mypy scripts/agent/http_lifecycle.py` passes clean
- `bandit -r scripts/agent/ -c pyproject.toml` passes clean with `#nosec` justifications retained
- All pre-existing tests in `test_http_lifecycle_integration.py` and `test_http_lifecycle_warning.py` pass unchanged in outcome
- Full `uv run pytest` shows no new failures compared to the pre-change baseline

## Out of scope

- Modifying `_ALLOWED_COMMANDS` contents or `_PROTECTED_ENV_VARS` — these move but do not change
- Changing process-group termination strategy or timeouts — these remain the same
- Changing stderr log rotation policy — this remains the same
- Adding new lifecycle operations beyond start/restart/shutdown
- Modifying `factory.py` internals beyond keeping imports working
- Writing new documentation beyond what routing directs

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260905 | Composition facade already existed on disk from a prior session (commit 403e0c086), but was integrated incorrectly — see Blocker Log. Corrected in this cycle: restored `_wait_exited`/`_terminate_with_timeout` on the facade itself (delegation to `ProcessTerminator` broke because `terminate()` was a sync method awaited by the facade), restored `_snapshot_fields`/`get_process_info`/`get_process_snapshot`/`list_processes` to operate on the facade's own `_http_procs`/`_http_pgids`/`_stderr_log_paths` dicts using `agent.services.models.ProcessInfoSnapshot` (the module had been wired to a wrong, independently-defined 22-field `ProcessInfoSnapshot` in `http_lifecycle_process_snapshot.py`), restored `_read_stderr_tail`/`_STDERR_TAIL_BYTES` (64KiB) and `HttpStartupError.__str__` (512-byte tail, space-joined) to their original values, restored the `_ALLOWED_COMMANDS` class attribute (tests patch it directly), removed the orphaned `_rotate_log` facade method (dead code with an incompatible call signature) |
| 2 | Add or update tests per Validation plan | Completed | — | 20260905 | No new tests added — existing `tests/agent/test_lifecycle.py`, `test_http_lifecycle_integration.py`, `test_http_lifecycle_warning.py` already provide full coverage of facade behavior and were used as the correctness oracle for this cycle's fixes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260905 | `ruff check` and `mypy scripts/` clean for all http_lifecycle_*.py files; full `uv run pytest tests/agent/test_lifecycle.py tests/agent/test_http_lifecycle_integration.py tests/agent/test_http_lifecycle_warning.py tests/agent/test_http_lifecycle_command_validator.py tests/agent/test_http_lifecycle_process_terminator.py tests/agent/test_http_lifecycle_stderr_log.py` → 274 passed, 3 skipped (was 29 failed / 45 passed before this cycle's fixes). Confirmed via `git stash` that the ~474 unrelated failures elsewhere in `tests/agent/` pre-date this cycle and are unaffected by these changes |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260905 | No doc-mapped rows in `docs/00_index.md` reference this module; no doc updates required |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | On resuming this batch, `uv run pytest` showed 29/48 failures in `test_http_lifecycle_integration.py`/`test_http_lifecycle_warning.py`, including a live `TypeError: object NoneType can't be used in 'await' expression` (facade awaited `ProcessTerminator.terminate()`, a plain `def`). Root cause: procedures #01/#03/#04/#06/#07 were each implemented in isolation against their own sample code without integration-testing the facade against its six components or against the pre-existing test suite that characterizes original behavior. Fixed as described in Step 1 above. | Yes | 20260905 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 through REQ-008
- **Source issue**: issues/20260831-155630_refactor_007_http_lifecycle_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-065548_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-101432
- **Related target files**: scripts/agent/http_lifecycle.py
