## Goal

Bring the lifecycle shutdown path inside the shutdown deadline: take the remaining deadline instead of an independent 30 s window, stop absorbing SIGINT during cleanup, and report terminations that could not be confirmed (REQ-010: termination is bounded by the same deadline; REQ-011: the interrupt path is not defeated; AC-2, AC-4).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: `shutdown_all()` in this coordinator, the per-server terminate windows, the SIGINT guard, and the unconfirmed-termination report.
- Out of scope: the process terminator's confirm window (row 12), the callers that pass the deadline (rows 13, 16), and the step machine (row 5).

## Assumptions

- `_SHUTDOWN_TIMEOUT_SEC = 30.0` (`scripts/agent/http_lifecycle_shutdown_coordinator.py:28`) is a second, independent window: the shutdown sequence can already be inside its own deadline when this constant starts a further 30 s wait.
- `_absorb_sigint_during_shutdown()` (`scripts/agent/http_lifecycle_shutdown_coordinator.py:44-48`) installs a handler that logs and ignores SIGINT for the duration of cleanup (`scripts/agent/http_lifecycle_shutdown_coordinator.py:129`, `:135`, `:139`), which discards the interrupt the budget is trying to deliver.
- The terminate call is built as a kwargs dict at `scripts/agent/http_lifecycle_shutdown_coordinator.py:171-176`, which is where the clamped window is passed.

## Design decisions

- The remaining deadline is a parameter, not a constant: the caller (row 5, row 13, row 16) supplies `remaining()` (row 1) and this coordinator clamps each per-server window to it, so the sum of the per-server waits cannot exceed what the sequence has left.
- Replace the absorbing handler with one that forwards to the budget's `request_interrupt()` (row 1): SIGINT during cleanup must interrupt the step in progress, not be swallowed. Restoring the previous handler in the `finally` (`scripts/agent/http_lifecycle_shutdown_coordinator.py:171-176`) keeps the same install-and-restore shape.
- A server that was terminated but not confirmed is reported with the existing unconfirmed outcome rather than being counted as clean, so the step record reflects what was proved (REQ-012).
- Compatibility impact: a shutdown that starts with little time left now spends only that time in the lifecycle step instead of up to 30 s.

## Alternatives considered

- keep the guard and simply shorten it — rejected: the guard is what makes a second Ctrl-C useless during cleanup, which is the behavior REQ-011 changes.

## Implementation
### Target file
`scripts/agent/http_lifecycle_shutdown_coordinator.py`

### Procedure
1. Add the remaining-deadline parameter to the shutdown entry point (`scripts/agent/http_lifecycle_shutdown_coordinator.py:44-48`) and thread it to the terminate call built at `scripts/agent/http_lifecycle_shutdown_coordinator.py:171-176`.
2. Clamp each per-server window to the remaining deadline before it is passed as `timeout`, and stop starting new servers' termination once the deadline is spent, recording them as not attempted.
3. Replace `_SHUTDOWN_TIMEOUT_SEC` (`scripts/agent/http_lifecycle_shutdown_coordinator.py:28`) as the authority; keep it only as the fallback when no deadline is supplied.
4. Replace the absorbing handler (`scripts/agent/http_lifecycle_shutdown_coordinator.py:100-170`) with one that requests an interrupt on the budget, and keep the handler restore in the `finally`.
5. Report each unconfirmed termination in the returned outcome set so the step record can name it (REQ-012).

### Method
- Clamping is done once per server at the point the window is computed, so the value the terminator sees is always the time actually available.

### Details
- The fallback keeps the module usable from paths that have no budget (row 16's rollback path before its own change lands), so the row can land before its callers.

### Companion test files
- `tests/agent/test_http_lifecycle_shutdown_coordinator.py`
  - Procedure: terminate several servers under one supplied remaining deadline, assert each confirm window is clamped, and assert an unconfirmed server is reported `EXIT_UNCONFIRMED` with a `timed_out` outcome.
  - Validation: `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -q` (REQ-010; AC-1, AC-4).

## Compatibility considerations

- Tests that assert the fixed window must assert the clamped value instead (companion rows 33, and row 35).
- The returned outcome shape is unchanged; only the values it can carry grow.

## Security considerations

- The unconfirmed report names the server key and the outcome, not a command line or path (REQ-013).

## Rollback considerations

- Revert this row's commit with rows 33 and 35: the clamping and SIGINT expectations are asserted there.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -q` | clamped windows, unconfirmed reporting, SIGINT no longer absorbed |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | Integration | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | the whole shutdown path stays inside the deadline |

## Completion criteria

- No per-server termination window exceeds the remaining deadline, and a server whose exit was not confirmed appears in the report.
- A SIGINT delivered during cleanup reaches the budget instead of being logged and ignored.

## Out of Scope

- The confirm window inside the terminator, the protocol and router signatures, and the step machine.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion rows 33, row 35 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-010 (termination bounded by the shutdown deadline), REQ-011 (second-signal behavior)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/http_lifecycle_shutdown_coordinator.py`, `tests/agent/test_http_lifecycle_shutdown_coordinator.py`
