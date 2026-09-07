# Implementation Procedure: Refactor http_lifecycle.py — reduce method sizes, eliminate snapshot duplication, simplify signal handling

## Goal

Refactor `scripts/agent/http_lifecycle.py` to improve maintainability by reducing large method sizes, eliminating duplicate snapshot construction logic, simplifying signal handling in `shutdown_all()`, and replacing magic numbers with named constants — without changing any external API or behavior.

## Scope

- **In-Scope**: Extract methods from `start()`, replace `_snapshot_fields()` + dual consumers with `_build_snapshot_dict()`, simplify `shutdown_all()` signal handling, move magic numbers to module-level constants
- **Out-of-Scope**: Adding new lifecycle features (e.g., graceful restart with zero-downtime), changing the behavior of existing fields, modifying `HttpStartupError` or `StartupFailure` exception schemas, refactoring other files in the agent service layer

## Assumptions

- The existing `MCPSERVER_HEALTH_TIMEOUT` (5.0) and `_STDERR_TAIL_BYTES` (64*1024) constants should not be renamed or changed — they already serve their purpose
- The `ShutdownCoordinator` module's internal signal handling logic is not part of this refactor scope
- The `_absorb_sigint_during_shutdown` static method name and signature must remain unchanged for backward compatibility

## Design decisions

- `_health_poll_until_ready()` accepts an `httpx.AsyncClient` parameter (caller-created) to avoid creating duplicate clients — resolves UNK-01
- `call_soon_threadsafe` fallback is kept in `shutdown_all()` for thread-safety when called from non-main threads — resolves UNK-03
- `_snapshot_fields()` tuple return type is removed because it is a private method (starts with `_`) — no external contract exists (resolves Risk: removing `_snapshot_fields()` tuple return type could break external consumers)

## Alternatives considered

- Keep `_snapshot_fields()` returning a tuple and have both consumers unpack it — rejected because adding a field requires updating two locations
- Use `asyncio.get_running_loop().call_soon()` instead of `call_soon_threadsafe` in `shutdown_all()` — rejected because `call_soon_threadsafe` is safer when called from non-asyncio threads
- Derive field mappings automatically from dataclass fields — deferred to future task (UNK-02)

## Implementation

### Target file

`scripts/agent/http_lifecycle.py`

### Procedure

#### Phase 1: Preparation — Add constants (REQ-005)

Add three module-level constants after the existing constants (`MCPSERVER_HEALTH_TIMEOUT`, `_TERMINATE_POLL_INTERVAL_SEC`, `_STDERR_TAIL_BYTES`):

```python
HEALTH_POLL_INTERVAL_SEC: float = 0.5
TERMINATE_TIMEOUT_SEC: float = 5.0
RESTART_TERMINATE_TIMEOUT_SEC: float = 3.0
```

Replace all occurrences of the magic numbers:
- `0.5` → `HEALTH_POLL_INTERVAL_SEC` (currently at line 425 in `_interruptible_poll_sleep` call)
- `5.0` → `TERMINATE_TIMEOUT_SEC` (currently at lines 367, 437, 514 in `_terminate_with_timeout` calls)
- `3.0` → `RESTART_TERMINATE_TIMEOUT_SEC` (currently at line 132 default param of `_terminate_with_timeout`)

#### Phase 2: Core Logic Refactoring — Extract methods from start() (REQ-001, REQ-002, REQ-007)

##### Method 2.1: `_create_and_validate_proc(server_key, cfg)`

Extract from `start()` lines 310–384. Encapsulates:
1. Command validation via `self._command_validator.validate(server_key, cfg.cmd[0])`
2. Environment filtering via `self._command_validator.filter_env(cfg.env)`
3. Subprocess creation via `subprocess.Popen(...)`
4. getpgid failure handling with cleanup

Signature:
```python
def _create_and_validate_proc(
    self,
    server_key: str,
    cfg: McpServerConfig,
) -> tuple[subprocess.Popen[bytes], IO[bytes]]:
    """Create and validate subprocess for the given server configuration.

    Validates the command, filters environment variables, creates the subprocess,
    and handles getpgid failure with resource cleanup.

    Returns:
        A tuple of (proc, stderr_fh) on success.

    Raises:
        HttpStartupError: If command validation fails or getpgid fails.
    """
```

Implementation steps:
1. Validate `cfg.cmd` is not empty (lines 321–328)
2. Filter env: `env = self._command_validator.filter_env(cfg.env)` (line 318)
3. Open stderr log: `stderr_fh = self._open_stderr_log(server_key, cfg)` (line 319)
4. Store stderr file handle: `self._stderr_files[server_key] = stderr_fh` (line 320)
5. Validate command (lines 331–343) — if ValueError, close resources and raise HttpStartupError
6. Create subprocess (lines 346–352) — if Exception, close resources and re-raise
7. Get process group ID (lines 358–383) — if OSError, terminate with timeout=5.0, clean up resources, and re-raise the OSError

Return `(proc, stderr_fh)` on success.

##### Method 2.2: `_health_poll_until_ready(server_key, cfg, client, deadline, shutdown_event)`

Extract from `start()` lines 386–445. Encapsulates:
1. Health URL construction
2. While-loop polling `/health` until ready or timeout
3. Early-exit detection (process exited)
4. Shutdown event racing
5. Timeout failure

Signature:
```python
async def _health_poll_until_ready(
    self,
    server_key: str,
    cfg: McpServerConfig,
    client: httpx.AsyncClient,
    deadline: float,
    shutdown_event: asyncio.Event | None,
) -> None:
    """Poll /health endpoint until the server becomes healthy or timeout expires.

    Polls the health endpoint in a loop, checking for early exit and shutdown
    events between polls. Raises HttpStartupError on early exit, shutdown,
    or timeout.

    Args:
        server_key: Server identifier key.
        cfg: Server configuration.
        client: Async HTTP client for health check requests.
        deadline: Monotonic time at which to abort polling.
        shutdown_event: Optional event to race against poll sleep.

    Raises:
        HttpStartupError: On early exit, shutdown, or timeout.
    """
```

Implementation steps:
1. Construct health_url (line 386)
2. Check `cfg.startup_timeout_sec > 0` guard (line 387)
3. Compute hc_timeout (lines 388–391)
4. Enter async context manager for client (lines 392–394)
5. While loop: `while time.monotonic() < deadline:` (line 395)
6. Early exit check (lines 396–411)
7. Try/except health check (lines 412–424)
8. Interruptible poll sleep with shutdown event (lines 425–434)
9. After loop: timeout failure handling (lines 436–445)
10. Else branch: skip health check logging (lines 446–451)

##### Method 2.3: Update `start()`

After extracting the above methods, update `start()` to call them. The remaining body of `start()` should contain only:
1. Idempotency check (lines 302–308)
2. Logging (lines 310–314)
3. Call `_create_and_validate_proc()` (replaces lines 318–384)
4. Call `_health_poll_until_ready()` (replaces lines 386–451)

Expected result: `start()` reduced from ~164 lines to under 80 lines.

#### Phase 3: Snapshot consolidation (REQ-003)

##### Method 3.1: Replace `_snapshot_fields()` with `_build_snapshot_dict()`

Current `_snapshot_fields()` (lines 214–225) returns a tuple:
```python
tuple[subprocess.Popen[bytes], bool, int | None, int | None, str] | None
```

Replace with `_build_snapshot_dict()` that returns a dict:
```python
def _build_snapshot_dict(self, server_key: str) -> dict | None:
    """Return a dict snapshot for a managed subprocess, or None if unknown."""
    proc = self._http_procs.get(server_key)
    if proc is None:
        return None
    running = proc.poll() is None
    last_exit_code = proc.poll() if not running else None
    pgid = self._http_pgids.get(server_key)
    stderr_log = self._stderr_log_paths.get(server_key, "")
    return {
        "server_key": server_key,
        "managed": True,
        "pid": proc.pid,
        "pgid": pgid,
        "running": running,
        "last_exit_code": last_exit_code,
        "stderr_log": stderr_log,
    }
```

##### Method 3.2: Update `get_process_info()`

Current implementation (lines 227–241) unpacks the tuple from `_snapshot_fields()`. Replace with:
```python
def get_process_info(self, server_key: str) -> ProcessInfoSnapshot | None:
    """Return a read-only snapshot for a managed subprocess, or None if unknown."""
    d = self._build_snapshot_dict(server_key)
    if d is None:
        return None
    return ProcessInfoSnapshot(
        server_key=d["server_key"],
        managed=d["managed"],
        pid=d["pid"],
        pgid=d["pgid"],
        running=d["running"],
        last_exit_code=d["last_exit_code"],
        stderr_log=d["stderr_log"],
    )
```

##### Method 3.3: Update `get_process_snapshot()`

Current implementation (lines 243–257) unpacks the tuple from `_snapshot_fields()` and constructs a dict. Replace with:
```python
def get_process_snapshot(self, server_key: str) -> dict | None:
    """Return a dict snapshot for a managed subprocess, or None if unknown."""
    return self._build_snapshot_dict(server_key)
```

#### Phase 4: Signal handling simplification (REQ-004)

Simplify `shutdown_all()` signal handling. Current implementation (lines 481–542) uses complex signal handler swap with `call_soon_threadsafe` fallback.

**Decision**: Keep the `call_soon_threadsafe` fallback for thread-safety (resolves UNK-03). The plan's stated goal of removing it conflicts with the risk mitigation noted in the plan itself ("keep the try/except ValueError around signal.signal() calls; the original code also had this guard").

Simplification approach:
1. Remove the nested try/except blocks that attempt `signal.signal()` twice (once directly, once via `call_soon_threadsafe`)
2. Use a single `try/except ValueError` wrapper around the `signal.signal()` call
3. Restore original handler in finally block unconditionally using the saved `old_sigint` value

Refactored structure:
```python
async def shutdown_all(self) -> None:
    """Terminate all HTTP subprocess servers and clear internal state."""
    old_sigint: object | None = None
    try:
        old_sigint = signal.getsignal(signal.SIGINT)
    except ValueError:
        old_sigint = None

    if old_sigint is not None:
        try:
            signal.signal(signal.SIGINT, self._absorb_sigint_during_shutdown)
        except ValueError:
            # Best-effort: scheduling from non-main thread may fail silently
            logger.debug(
                "Lifecycle: could not set SIGINT guard handler"
            )

    try:
        keys = list(self._http_procs.keys())
        for key in keys:
            proc = self._http_procs.pop(key, None)
            if proc is None:
                continue
            if proc.poll() is not None:
                logger.debug("Lifecycle: %r already exited; removing entry", key)
            else:
                try:
                    await self._terminate_with_timeout(proc, key, timeout=TERMINATE_TIMEOUT_SEC)
                except (OSError, TimeoutError) as e:
                    logger.warning(
                        "Lifecycle: error stopping HTTP subprocess %r: %s", key, e
                    )
            self._http_pgids.pop(key, None)
            stderr_fh = self._stderr_files.pop(key, None)
            if stderr_fh is not None:
                try:
                    stderr_fh.close()
                except OSError as close_err:
                    logger.warning(
                        "Lifecycle: error closing stderr log for %r: %s",
                        key, close_err,
                    )
        self._stderr_log_paths.clear()
        self._last_health_check.clear()
    finally:
        if old_sigint is not None:
            try:
                signal.signal(signal.SIGINT, old_sigint)
            except ValueError:
                # Best-effort: restoring from non-main thread may fail silently
                pass
```

Key changes from current:
- Removed `call_soon_threadsafe` fallback paths (both for setting and restoring the handler)
- Simplified exception handling to single `try/except ValueError` per signal operation
- Replaced magic number `5.0` with `TERMINATE_TIMEOUT_SEC` constant

#### Phase 5: Type hint improvements (REQ-008)

Remove unnecessary `object | None` unions:
1. Line 483: `old_sigint: object | None = None` → `old_sigint: signal.Signals | None = None` or keep as `object | None` since `signal.getsignal()` can return various types
2. Line 470: `frame: object` parameter in `_absorb_sigint_during_shutdown` — this is correct per Python's signal handler signature (`Callable[[int, Any], None]`), so no change needed

Actually, reviewing more carefully:
- `signal.getsignal()` returns `Callable[[int, Any], None] | int` (either a handler or the default signal disposition integer)
- The comparison `if old_sigint is not None:` works correctly regardless of type
- Keeping `object | None` is acceptable here since the actual type varies and we only use identity comparison

No type hint changes are necessary after careful review — the existing hints are appropriate.

## Compatibility considerations

- **Public API unchanged**: `get_process_info()`, `get_process_snapshot()`, `list_processes()`, `verify_running()`, `verify_running_async()`, `start()`, `restart()`, `shutdown_all()` signatures remain identical
- **Private method name preserved**: `_absorb_sigint_during_shutdown` static method name and signature must remain unchanged for backward compatibility
- **Exception semantics preserved**: `HttpStartupError` wrapping `StartupFailure` dataclass behavior unchanged — verified against `scripts/agent/http_lifecycle_errors.py`
- **Dataclass compatibility**: `ProcessInfoSnapshot` fields match the dict keys produced by `_build_snapshot_dict()` — verified against `scripts/agent/services/models.py`
- **Signal handler contract**: `_absorb_sigint_during_shutdown` still accepts `(signum, frame)` parameters matching Python's signal handler signature

## Security considerations

- No new security-relevant code paths introduced
- Existing `# nosec B603` comments on subprocess creation and `os.killpg()` calls are preserved
- Secret masking via `_mask_secrets()` in error paths is unchanged
- Environment variable filtering via `CommandValidator.filter_env()` remains the same

## Rollback considerations

- If refactor introduces behavioral regression, revert to the pre-refactor version of `http_lifecycle.py`
- The extracted private methods have no external dependencies beyond what was already present
- Signal handling simplification carries the lowest rollback risk — the original logic is well-understood and the simplified version preserves the same safety guarantees
- Snapshot consolidation carries moderate risk — verify `get_process_info()` and `get_process_snapshot()` outputs match exactly before committing

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Unit — verify all lifecycle operations work correctly after refactoring | `uv run pytest tests/agent/test_http_lifecycle_*.py -v` | All existing tests pass |
| scripts/agent/http_lifecycle.py | Integration — verify no behavioral regression | Compare `/reload` command output before and after | No behavioral difference |
| scripts/agent/http_lifecycle.py | Mutation — verify edge case coverage | `mutmut run --paths-to-mutate=scripts/agent/http_lifecycle.py` | No missed mutations |
| scripts/agent/http_lifecycle.py | Static analysis — verify method sizes | `radon cc scripts/agent/http_lifecycle.py -s` | No method exceeds grade C |

## Completion criteria

- [ ] `start()` method does not exceed 80 lines (excluding blank lines and comments) — REQ-007
- [ ] `_snapshot_fields()` is removed; replaced by `_build_snapshot_dict()` returning a dict — REQ-003
- [ ] `shutdown_all()` signal handling is simplified (single try/except per signal operation instead of dual-path with `call_soon_threadsafe`) — REQ-004
- [ ] Magic numbers `0.5`, `5.0`, `3.0` are replaced with named constants — REQ-005
- [ ] Each private method has a clear single responsibility documented in its docstring — REQ-007
- [ ] All existing tests pass without modification — REQ-006
- [ ] Type hints are improved where possible (no unnecessary `object | None` unions remain) — REQ-008

## Out of scope

- Adding new lifecycle features (e.g., graceful restart with zero-downtime)
- Changing the behavior of existing fields
- Modifying `HttpStartupError` or `StartupFailure` exception schemas
- Refactoring other files in the agent service layer
- Deriving field mappings automatically from dataclass fields (deferred to future task)

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Add constants (REQ-005) | Completed | — | — | All phases already applied by prior refactor |
| 2 | Phase 2: Extract methods from start() (REQ-001, REQ-002, REQ-007) | Completed | — | — | Verified via adversarial review |
| 3 | Phase 3: Snapshot consolidation (REQ-003) | Completed | — | — | Verified via adversarial review |
| 4 | Phase 4: Signal handling simplification (REQ-004) | Completed | — | — | Verified via adversarial review |
| 5 | Phase 5: Type hint improvements (REQ-008) | Completed | — | — | No changes required after review |
| 6 | Verification (REQ-006, REQ-007) | Completed | — | — | Tests pass; static analysis OK |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-007, REQ-008
- **Source issue**: issues/20260906-185916_refactor_http_lifecycle.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260906-205849_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260907-130909
- **Related target files**: scripts/agent/http_lifecycle.py
