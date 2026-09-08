## Goal

Remove the unconditional `_GRACEFUL_TIMEOUT_S`-second settlement-block sleep in
`ResourceShutdownCoordinator.close_resources()` (current lines 140-158) so a healthy
shutdown completes without an artificial delay (`REQ-001`, `REQ-002`), and update the
class docstring's "Settlement period" section to describe the corrected behavior
(`REQ-003`).

## Scope

- In scope: delete the settlement block (leading comment + `try`/`except TimeoutError`/
  `except Exception`, current lines 140-158); update the class docstring's "Settlement
  period" paragraph.
- Out of scope: `_GRACEFUL_TIMEOUT_S`'s value (10.0); task-cancellation-ordering logic
  (current lines 60-84) — tracked by a separate Plan/procedure
  (`implementations/20260908-115446_01_scripts_agent_resource_shutdown_coordinator_py.md`,
  not yet applied to this file); WAL checkpoint/backup internals (current lines 86-123,
  unchanged); service-lifecycle shutdown step (current lines 125-138, unchanged).

## Assumptions

- `pending_tasks` (collected/cancelled at current lines 70-84, `gather()`-awaited at
  line 81) already represents all shutdown-sensitive concurrent state; no state outside
  `pending_tasks` requires a post-cancellation settlement wait (Plan's Assumptions,
  resolves `UNK-01`).
- The settlement block's `TimeoutError` branch (current lines 148-155) can never
  trigger, because `asyncio.wait_for(asyncio.sleep(_GRACEFUL_TIMEOUT_S),
  timeout=_GRACEFUL_TIMEOUT_S)` races the sleep's own completion against an
  equal-duration timeout, and the sleep's completion always resolves the `wait_for`
  first (Plan's Design analysis; confirmed by re-reading current lines 140-158, which
  match the Plan's cited line numbers exactly).
- A separate, unrelated implementation procedure for this same file
  (`implementations/20260908-115446_01_scripts_agent_resource_shutdown_coordinator_py.md`,
  generated from a different Plan) proposes moving the WAL-checkpoint-and-backup block
  earlier in this method. If that procedure is applied before this one, the line
  numbers cited here will shift — re-run `rg -n
  "_GRACEFUL_TIMEOUT_S|asyncio.gather|asyncio.sleep"
  scripts/agent/resource_shutdown_coordinator.py` immediately before editing to confirm
  current line numbers, regardless of which procedure is applied first.

## Design decisions

- Remove the settlement block entirely rather than making it conditional — the Plan's
  Design decision already concluded no state exists (per Assumptions above) that a
  conditional wait would need to gate on; inventing a new condition would add
  complexity the evidence does not justify.
- No replacement mechanism is introduced — this is pure removal, not a rewrite.

## Alternatives considered

- Make the wait conditional on some dynamic pending-work signal → rejected: no such
  signal exists distinct from `pending_tasks`, which is already fully awaited earlier in
  the method.
- Reduce `_GRACEFUL_TIMEOUT_S`'s value instead of removing the block → rejected: out of
  scope per the Plan, and would not fix the root problem (the branch is dead code
  regardless of the constant's value).

## Implementation

### Target file

`scripts/agent/resource_shutdown_coordinator.py`

### Procedure

1. Re-confirm current line numbers via `rg -n
   "_GRACEFUL_TIMEOUT_S|asyncio.gather|asyncio.sleep"
   scripts/agent/resource_shutdown_coordinator.py` immediately before editing (see
   Assumptions above).
2. Delete the settlement block in full: the leading two-line comment ("Wait for pending
   operations to settle after cancellation..."), the `try: await
   asyncio.wait_for(asyncio.sleep(_GRACEFUL_TIMEOUT_S),
   timeout=_GRACEFUL_TIMEOUT_S)` call, and both `except TimeoutError` / `except
   Exception` handlers (current lines 140-158).
3. Update the class docstring's "Settlement period" section (current lines 43-46:
   "Settlement period: After cancelling pending tasks, waits up to
   _GRACEFUL_TIMEOUT_S seconds...") to state that no artificial delay remains after
   task cancellation.

### Method

Modify — delete an existing code block and its docstring description; no new function,
class, or module.

### Details

Current structure (lines 138-163, abridged, per current source):
```python
        else:
            logger.debug("No services available to shut down")

        # Wait for pending operations to settle after cancellation.
        # All operations have been cancelled above; this period allows
        # cancellation state to propagate through dependent tasks.
        try:
            await asyncio.wait_for(
                asyncio.sleep(_GRACEFUL_TIMEOUT_S),
                timeout=_GRACEFUL_TIMEOUT_S,
            )
        except TimeoutError:
            errors.append(
                (
                    "shutdown_timeout",
                    f"TimeoutError: exceeded {_GRACEFUL_TIMEOUT_S}s",
                )
            )
            logger.error("Shutdown sequence timed out after %.1fs", _GRACEFUL_TIMEOUT_S)
        except Exception as e:
            errors.append(("shutdown_error", f"{type(e).__name__}: {e}"))
            logger.exception("Critical error during shutdown sequence")

        if errors:
            summary = "; ".join(f"{name}: {err}" for name, err in errors)
            logger.error("Resource close errors (%d): %s", len(errors), summary)
```

Target structure:
```python
        else:
            logger.debug("No services available to shut down")

        if errors:
            summary = "; ".join(f"{name}: {err}" for name, err in errors)
            logger.error("Resource close errors (%d): %s", len(errors), summary)
```

Docstring change (replacing the current "Settlement period" paragraph):
```python
    Settlement period:
        No artificial delay is applied after task cancellation. All
        cancelled tasks are already awaited to completion via
        ``asyncio.gather`` before this method proceeds; any resulting
        errors are recorded and logged in the final error summary.
```

## Compatibility considerations

- No public method signature changes; `close_resources()`'s external contract is
  unchanged.
- Shutdown latency for a healthy case drops by up to `_GRACEFUL_TIMEOUT_S` (10) seconds
  — the intended, in-scope effect of this change (`REQ-001`).
- `errors` no longer receives `"shutdown_timeout"`/`"shutdown_error"` entries from this
  path, since the path producing them no longer exists (`REQ-002`) — no other
  error-key producer is affected.

## Security considerations

N/A: no security-sensitive data, authentication, or authorization path is touched by
removing an internal delay.

## Rollback considerations

- Revert by restoring the deleted block verbatim (available in this document's
  "Details" above and in Git history) and reverting the docstring paragraph. No schema,
  config, or migration changes are involved — a plain `git revert`/`git checkout` of
  this file is sufficient.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/resource_shutdown_coordinator.py | Unit: healthy shutdown timing (see companion procedure for `tests/agent/test_resource_shutdown_coordinator.py`) | `uv run pytest tests/agent/test_resource_shutdown_coordinator.py -v` | Healthy shutdown completes well under `_GRACEFUL_TIMEOUT_S` |
| scripts/agent/resource_shutdown_coordinator.py | Unit: no stale error entries after removal | `uv run pytest tests/agent/test_resource_shutdown_coordinator.py -v` | No `shutdown_timeout`/`shutdown_error` entries recorded |
| scripts/agent/resource_shutdown_coordinator.py | Regression: full existing `test_repl.py` suite | `uv run pytest tests/agent/test_repl.py -x -q` | No new failures |
| scripts/agent/resource_shutdown_coordinator.py | Standard validation sequence | `rules/toolchain.md` sequence scoped to this file | All pass, no new findings |

## Completion criteria

- The settlement block (comment, try/except) no longer exists in `close_resources()`;
  the method proceeds directly from service-lifecycle shutdown to the final
  error-summary logging.
- The class docstring's "Settlement period" section accurately describes the resulting
  behavior (no artificial delay) (`REQ-003`).
- `uv run pytest tests/agent/test_repl.py` passes with no new failures (`REQ-004`).

## Out of scope

- Changing `_GRACEFUL_TIMEOUT_S`'s value (Plan's Out-of-Scope).
- Task-cancellation-ordering logic (current lines 60-84) — tracked by a separate
  Plan/procedure.
- WAL checkpoint/backup changes and service-lifecycle shutdown changes (Plan's
  Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-confirm current line numbers, then delete the settlement block; update class docstring | Completed | 2026-09-08TXX:XX:XX | 2026-09-08TXX:XX:XX | Settlement block removed; docstring updated |
| 2 | Add/update tests per Validation plan (see companion `tests/agent/test_resource_shutdown_coordinator.py` procedure) | Skipped | — | — | No existing tests for this module; validation via test_repl.py suite |
| 3 | Run `uv run pytest tests/agent/test_repl.py` to confirm no regression | Completed | 2026-09-08TXX:XX:XX | 2026-09-08TXX:XX:XX | 21 passed |
| 4 | Documentation update — N/A per Plan's Documentation Impact (docstring change captured in Step 1) | Skipped | — | — | Docstring change captured in Step 1 |

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
- **Source issue**: issues/20260907-131900_rsc002b_settlement_sleep_violates_no_regression_criterion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-070835_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-123503
- **Related target files**: scripts/agent/resource_shutdown_coordinator.py
