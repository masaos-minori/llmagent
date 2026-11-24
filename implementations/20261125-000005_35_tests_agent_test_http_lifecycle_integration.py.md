## Goal

Extend the largest lifecycle shutdown integration test with a deadline: assert that the whole shutdown path stays inside a supplied remaining budget and that unconfirmed processes are reported (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the shutdown integration cases in this file.
- Out of scope: the coordinator (row 11), the terminator (row 12), and the manager delegation (row 13), which this file exercises but does not define.

## Assumptions

- This file is the largest consumer of the termination path (36 `shutdown_all` and 22 `terminate_with_timeout` references), so it is where a clamped window is observable end to end.
- The existing cases assert outcomes and process cleanup, not durations, so the new cases must measure against a supplied deadline rather than against wall-clock expectations.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | this row is the test row |
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
- **Related target files**: `tests/agent/test_http_lifecycle_integration.py`, `scripts/agent/http_lifecycle_shutdown_coordinator.py`, `scripts/agent/http_lifecycle.py`
