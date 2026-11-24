## Goal

Update the terminate-timeout expectations in this file so they hold against the optional remaining-deadline parameter, with and without a supplied budget (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the four terminate-timeout expectations in this file.
- Out of scope: the manager (row 13), the coordinator (row 11), and the terminator (row 12).

## Assumptions

- The file consumes `terminate_with_timeout()` in four places, all through the manager's wiring, and today asserts the fixed window.
- The parameter is optional (rows 12, 13), so a call with no deadline must keep today's value.

## Design decisions

- Assert both paths: one case with no deadline asserting the existing default, and one case with a supplied deadline asserting the supplied value reaches the terminate call.
- Change only the expectations that the new parameter makes ambiguous; leave the health and start cases untouched.
- Compatibility impact: none outside this file.

## Alternatives considered

- delete the default-path expectation — rejected: the fallback is the behavior the health-check and startup paths depend on (row 37).

## Implementation
### Target file
`tests/agent/test_http_lifecycle.py`

### Procedure
1. Update the four `terminate_with_timeout()` expectations so a call with no remaining deadline still asserts the module default.
2. Add one case that a supplied remaining deadline is forwarded to the terminate call.

### Method

- Expectation updates only; no new fixture or harness.

### Details

- The forwarded value is asserted on the call arguments, which is the observable contract between rows 11, 12 and 13.

## Compatibility considerations

- Existing case names and structure are preserved so the diff stays reviewable.

## Security considerations

- N/A: no path or command line is asserted.

## Rollback considerations

- Revert this row's commit with rows 12 and 13.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_http_lifecycle.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle.py tests/agent/test_http_lifecycle_health_check.py -q` | default and supplied-deadline expectations both pass |

## Completion criteria

- Both the no-deadline default and the supplied-deadline forwarding are asserted.

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
- **Related target files**: `tests/agent/test_http_lifecycle.py`, `scripts/agent/http_lifecycle.py`
