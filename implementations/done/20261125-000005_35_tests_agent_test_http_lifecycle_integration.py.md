## Goal

Extend the largest lifecycle shutdown integration test with a deadline: assert that the whole shutdown path stays inside a supplied remaining budget and that unconfirmed processes are reported (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the shutdown integration cases in this file.
- Out of scope: the coordinator (row 11), the terminator (row 12), and the manager delegation (row 13), which this file exercises but does not define.

## Assumptions

- This file is the largest consumer of the termination path (36 `shutdown_all` and 22 `terminate_with_timeout` references), so it is where a clamped window is observable end to end.
- The existing cases assert outcomes and process cleanup, not durations, so the new cases must measure against a supplied deadline rather than against wall-clock expectations.

Step 3b verification against the current source (20261125-122600):

- Procedure step 1's "asserts the call returns within it" is implemented the way this file's Method states it: the assertion is on the window handed to `terminate_with_timeout()` and on the returned pairs, never on a measured duration. A measured assertion would be the flaky kind.
- The three cases are `TestShutdownSequenceWithBudget`: `test_supplied_deadline_bounds_the_window_given_to_termination` (a 15 s budget cannot be spent as the module's 30 s window, asserted against `_SHUTDOWN_TIMEOUT_SEC`), `test_spent_deadline_reports_the_server_it_could_not_confirm` (a spent budget hands a 0.0 window and still returns `("a", TerminationOutcome.EXIT_UNCONFIRMED)`, OD-05), and `test_sigint_during_cleanup_reaches_the_budget` (the guard the coordinator installs calls `budget.request_interrupt()`, and the previous handler is restored in `finally`).
- Existing default-path cases are untouched, as step 4 requires.

## Design decisions

- Add a small-deadline case: supply a remaining deadline shorter than the default windows and assert the shutdown completes within it and reports the servers it could not confirm.
- Keep the existing default-path cases unchanged so the fallback behavior (row 11, row 12) stays covered.
- Assert the unconfirmed list rather than log text, because the list is the contract the step record consumes (REQ-012).
- Compatibility impact: existing cases keep passing unchanged.

## Alternatives considered

- assert elapsed time against the real clock — rejected: timing assertions in an integration test are the first thing to go flaky; the assertion is that the supplied window is honored, not that a duration matches.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_integration.py`

### Procedure
1. Add a case that calls `shutdown_all()` with a remaining deadline shorter than the default windows and asserts the call returns within it.
2. Add a case that a server whose exit cannot be confirmed appears in the returned unconfirmed list when the deadline is short.
3. Add a case that a SIGINT delivered during cleanup is not absorbed (row 11) and reaches the budget's interrupt request.
4. Leave the existing default-path cases untouched.

### Method

- Deadlines are supplied as test values, and the assertions are about the returned outcomes and the recorded interrupt, not about measured durations.

### Details

- The cases use the same fixtures as the existing integration cases, so no new harness is introduced.

## Compatibility considerations

- Additive cases; the existing 36 call sites in this file keep their current expectations.

## Security considerations

- N/A: no path or command line is asserted.

## Rollback considerations

- Revert this row's commit with rows 11, 12 and 13.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_http_lifecycle_integration.py` | Integration | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | the deadline is honored and unconfirmed processes are reported |
| `tests/agent/test_http_lifecycle_integration.py` | Integration | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -q` | the coordinator cases agree with the integration cases |

## Completion criteria

- A short remaining deadline shortens the shutdown path and produces an unconfirmed entry for every server whose exit was not proved.

## Out of Scope

- The clamping implementation and the confirm window.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-122329 | 20261125-122329 | TestShutdownSequenceWithBudget (3 cases) asserts the window handed to termination, never a measured duration |
| 2 | Add or update tests per Validation plan | Completed | 20261125-122329 | 20261125-122329 | this row is the test row this row is the test row; existing default-path cases untouched |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-122329 | 20261125-122329 | ruff format/check, pytest Pass; check_mock_patch_targets Pass |

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
- **Related target files**: `tests/agent/test_http_lifecycle_integration.py`, `scripts/agent/http_lifecycle_shutdown_coordinator.py`, `scripts/agent/http_lifecycle.py`