## Goal

Clamp the terminator's confirm window to the time the shutdown sequence actually has left, while keeping the SIGTERM then SIGKILL escalation unconditional, so a bounded shutdown cannot spend 2 s confirming each server after its deadline has passed (REQ-010: termination bounded by the shutdown deadline; AC-4).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: `terminate_with_timeout()`, `wait_exited()`, `_confirm_group_gone()`, and the confirm-window default.
- Out of scope: the per-server windows handed in by the shutdown coordinator (row 11) and the callers that supply the deadline (rows 13, 16).

## Assumptions

- `_DEFAULT_KILL_CONFIRM_TIMEOUT_SEC = 2.0` (`scripts/agent/http_lifecycle_process_terminator.py:27`) is the window in which an exit must be observed after SIGKILL; it is unrelated to the shutdown deadline today.
- The confirm deadline is computed from that constant inside `_confirm_group_gone()` (`scripts/agent/http_lifecycle_process_terminator.py:139-151`), so clamping has to reach that computation, not only the outer `timeout` argument.
- An unconfirmed process is reported with the existing unconfirmed outcome, which is the value the shutdown report counts (REQ-012).

## Design decisions

- The escalation is never skipped: SIGTERM is sent, SIGKILL is sent when the term window expires, and only the confirmation wait is clamped. A short remaining deadline shortens the waiting, never the killing.
- Clamping is applied to both waits (the term wait in `wait_exited()` and the confirm wait in `_confirm_group_gone()`) so the two cannot add up past the deadline.
- The default constant stays as the fallback when no deadline is supplied, which keeps the health-check and startup-failure paths (rows 37, 43) unchanged.
- Compatibility impact: a shutdown near its deadline now reports unconfirmed servers earlier instead of waiting the full window.

## Alternatives considered

- skip confirmation when the deadline is short — rejected: an unconfirmed exit is a fact the report must state, not something to hide by not looking.

## Implementation
### Target file
`scripts/agent/http_lifecycle_process_terminator.py`

### Procedure
1. Add the remaining-deadline parameter to `terminate_with_timeout()` (`scripts/agent/http_lifecycle_process_terminator.py:152-154`) and pass it to the waits it drives (`scripts/agent/http_lifecycle_process_terminator.py:90-105`, `scripts/agent/http_lifecycle_process_terminator.py:107-137`).
2. Clamp each computed deadline with the remaining deadline, keeping `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC` (`scripts/agent/http_lifecycle_process_terminator.py:23`) and `_DEFAULT_KILL_CONFIRM_TIMEOUT_SEC` (`scripts/agent/http_lifecycle_process_terminator.py:27`) as fallbacks.
3. Keep the SIGTERM and SIGKILL sends unconditional, and keep returning the same outcome values so a clamped wait reports unconfirmed rather than success.

### Method
- Clamp at the point each deadline is computed (`min(now + window, now + remaining)`), so a caller that supplies no remaining deadline gets today's behavior exactly.

### Details
- The poll interval is not clamped: a short window must not turn into a busy loop.

### Companion test files
- `tests/agent/test_http_lifecycle_process_terminator.py`
  - Procedure: assert SIGTERM and SIGKILL are still sent when the window is clamped, and that the confirm wait never exceeds the time supplied.
  - Validation: `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py -q` (REQ-010, OD-05; AC-1, AC-4).

## Compatibility considerations

- The parameter is optional, so the existing call sites keep their current behavior until rows 11, 13 and 16 pass a deadline.
- Outcome vocabulary is unchanged, so the tests that assert outcomes keep passing (companion row 34).

## Security considerations

- N/A: no new output; the outcome values already carry no path or command line.

## Rollback considerations

- Revert this row's commit with row 34: the clamped-window expectations are asserted there.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle_process_terminator.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_process_terminator.py -q` | clamped confirm window, SIGTERM and SIGKILL always sent, unconfirmed reported |

## Completion criteria

- A supplied remaining deadline shortens both waits and never prevents SIGTERM or SIGKILL.
- A process still present after the clamped window is reported unconfirmed.

## Out of Scope

- Per-server window selection, the SIGINT guard, and the step machine.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | companion row 34 |
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
- **Requirement ID**: REQ-010 (termination bounded by the shutdown deadline)
- **Source issue**: issues/20261119-145302_cliplc004_bounded-shutdown-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095950_cliplc004_bounded-shutdown-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-000005
- **Related target files**: `scripts/agent/http_lifecycle_process_terminator.py`, `tests/agent/test_http_lifecycle_process_terminator.py`
