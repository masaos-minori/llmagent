# Implementation: scripts/agent/http_lifecycle_process_terminator.py

## Goal

Ensure full coverage of termination logic — verify that `terminate_with_timeout()` covers all behaviors previously handled by `_terminate_with_timeout()` in `HttpServerLifecycleManager`. Add any missing behaviors (early-exit check when `proc.poll()` returns non-None, warning about children remaining when pgid wasn't used, fallback to `proc.terminate()` when `os.killpg()` fails).

## Scope

- Modify `scripts/agent/http_lifecycle_process_terminator.py` only.
- Add missing behavioral differences from `_terminate_with_timeout()` to `terminate_with_timeout()`:
  1. Early-exit when `proc.poll()` returns non-None (already present in `_terminate_with_timeout()` line 138).
  2. Warning about children remaining when pgid wasn't used (present in `_terminate_with_timeout()` lines 151-155).
  3. Fallback to `proc.terminate()` when `os.killpg()` fails (present in `_terminate_with_timeout()` lines 146-147).

## Assumptions

- The `terminate_with_timeout()` method already handles SIGTERM → SIGKILL escalation correctly.
- The early-exit check (step 1) should be added as the first thing in `terminate_with_timeout()`.
- The pgid fallback warning (step 2) should be emitted after successful SIGTERM but before waiting for exit.
- The `proc.terminate()` fallback (step 3) should replace the bare `except (OSError, ProcessLookupError)` handler around `os.killpg()`.

## Design decisions

- Add the early-exit check at the beginning of `terminate_with_timeout()` — simplest and most defensive approach.
- Add the pgid fallback warning as a conditional log message after SIGTERM succeeds but before polling for exit.
- For the `proc.terminate()` fallback, modify the `except` handler around `os.killpg()` to call `proc.terminate()` as a fallback before raising an error.

## Alternatives considered

- **Create a wrapper method**: Would keep `terminate_with_timeout()` unchanged but adds indirection. Not needed since we can fix the root cause directly.
- **Add parameters to control behavior**: Would make the API more complex. Simpler to just add the missing behaviors unconditionally.

## Implementation

### Target file

`scripts/agent/http_lifecycle_process_terminator.py`

### Procedure

1. Read `_terminate_with_timeout()` in `http_lifecycle.py` to confirm the exact behavioral differences.
2. Add early-exit check at the beginning of `terminate_with_timeout()`: if `proc.poll() is not None`, return immediately.
3. Add pgid fallback warning after SIGTERM succeeds: if pgid was not found via `os.getpgid()`, emit a warning that children may remain.
4. Modify the `except` handler around `os.killpg()` to fall back to `proc.terminate()` before raising an error.

### Method

```python
# Step 2: Add early-exit check at beginning of terminate_with_timeout()
# After line 137 (the docstring end):
#     if proc.poll() is not None:
#         logger.info("Process %s already exited", server_key)
#         return

# Step 3: Add pgid fallback warning after SIGTERM
# After line 152 (os.killpg(pgid, signal.SIGTERM)):
#     # After sending SIGTERM, warn if pgid wasn't used
#     if not used_pgid:
#         logger.warning(
#             "Lifecycle: %r terminated, but children may remain (no pgid available)",
#             server_key,
#         )

# Step 4: Modify except handler for os.killpg() failure
# Change the except handler around os.killpg():
# Before (line ~151-155):
#     try:
#         os.killpg(pgid, signal.SIGTERM)  # nosec B603
#     except ProcessLookupError:
#         logger.warning("Process group %d already terminated", pgid)
#         return
# After:
#     try:
#         os.killpg(pgid, signal.SIGTERM)  # nosec B603
#     except ProcessLookupError:
#         logger.warning("Process group %d already terminated", pgid)
#         return
#     except OSError:
#         # Fallback to proc.terminate() when killpg fails
#         logger.warning(
#             "Lifecycle: os.killpg() failed for %r pid=%d; falling back to proc.terminate()",
#             server_key,
#             getattr(proc, "pid", None),
#         )
#         proc.terminate()
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- Need to carefully reconcile the behavioral differences between `_terminate_with_timeout()` and `terminate_with_timeout()` — the plan explicitly notes these differences must be reconciled during migration.
- The pgid tracking (`used_pgid`) variable needs to be introduced in `terminate_with_timeout()` to track whether `os.killpg()` was actually used.

## Compatibility considerations

- **No breaking change** for existing callers of `terminate_with_timeout()` — the method signature remains the same.
- The added warnings will appear in logs but do not change the return value or exception behavior.

## Security considerations

- No new security surface introduced. Adding fallback mechanisms does not introduce new attack vectors.

## Rollback considerations

- Revert the behavioral additions to `terminate_with_timeout()`.
- If the `proc.terminate()` fallback causes unexpected behavior, remove it and investigate further.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| Termination behavior | Unit test | `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py -v` | All existing tests pass without modification |
| Behavioral equivalence | Manual verification | Compare `_terminate_with_timeout()` output with `terminate_with_timeout()` output | Identical behavior for all edge cases |
| Type checking | Static | Type checker against modified file | No type errors |
| Lint checking | Static | Lint tool against modified file | No lint errors |

## Completion criteria

- [ ] Early-exit check added: `if proc.poll() is not None: return`.
- [ ] Pgid fallback warning added after SIGTERM succeeds but before polling.
- [ ] `proc.terminate()` fallback added in `except OSError` handler around `os.killpg()`.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/agent/http_lifecycle.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_shutdown_coordinator.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_process_snapshot.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/http_lifecycle_health_checker.py` — handled by a separate implementation procedure document.
- Modifying `scripts/agent/factory.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify behavioral differences with _terminate_with_timeout() | Completed | — | — | |
| 2 | Add early-exit check | Completed | — | — | |
| 3 | Add pgid fallback warning | Completed | — | — | |
| 4 | Add proc.terminate() fallback | Completed | — | — | |
| 5 | Run validation sequence (rules/toolchain.md) | Completed | — | — | ruff + mypy passed |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260911-214848_refactor_http_lifecycle_eliminate_cross_module_duplication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-235117_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-005035
- **Related target files**: scripts/agent/http_lifecycle_process_terminator.py
