## Goal

Update the one terminate-call expectation in this file so the startup lifecycle path's `terminate_with_timeout()` call matches the signature that can carry a remaining deadline (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the single `terminate_with_timeout()` expectation in this file.
- Out of scope: the terminator (row 12), the manager (row 13), and the startup rollback path (row 16).

## Assumptions

- The file asserts one terminate call made from the startup lifecycle path, today with the fixed window.
- The parameter is optional (row 12), so a call that supplies no deadline keeps today's window.

## Design decisions

- Assert the default path only: the startup lifecycle path in this file does not hold a budget, and inventing one here would test a case that does not exist.
- Keep the existing outcome assertions untouched; only the call-signature expectation changes.
- Compatibility impact: none outside this file.

## Alternatives considered

- add a clamped-window case here — rejected: clamping is asserted in rows 34 and 35, and duplicating it here adds a second place to keep in step.

## Implementation
### Target file
`tests/agent/test_startup_mcp_lifecycle.py`

### Procedure
1. Update the `terminate_with_timeout()` expectation so the call matches the signature that accepts the optional remaining-deadline parameter.
2. Keep the existing outcome and window expectations for the no-deadline call.

### Method

- One expectation update; no new fixture.

### Details

- The assertion is on the call arguments, which is what distinguishes the default path from a budgeted one.

## Compatibility considerations

- No other case in this file is touched.

## Security considerations

- N/A: no path or command line is asserted.

## Rollback considerations

- Revert this row's commit with row 12.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_startup_mcp_lifecycle.py` | Unit | `uv run pytest tests/agent/test_startup_mcp_lifecycle.py tests/agent/test_http_lifecycle_process_terminator.py -q` | the startup terminate call matches the new signature |

## Completion criteria

- The startup lifecycle terminate call is asserted against the signature that accepts a remaining deadline, with the default window still asserted.

## Out of Scope

- Clamping and the confirm window.

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
- **Related target files**: `tests/agent/test_startup_mcp_lifecycle.py`, `scripts/agent/http_lifecycle_process_terminator.py`
