## Goal

Confirm that the health-check path keeps today's fixed terminate window when no budget is supplied, so making termination budget-aware does not change a path that is not part of the shutdown sequence (REQ-010: termination bounded by the shutdown deadline, without changing non-shutdown callers).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the terminate-timeout expectations in the health-check cases of this file.
- Out of scope: the terminator (row 12), the manager (row 13), and the shutdown coordinator (row 11).

## Assumptions

- The health-check call sites are not in the shutdown path: `scripts/agent/http_lifecycle_health_checker.py:76`, `:166`, `:210`, `:226` call the terminate path with no budget, and this file asserts those windows.
- The remaining-deadline parameter is optional (rows 12, 13), so these call sites keep the module default.

## Design decisions

- Assert the default explicitly rather than leaving the cases silent: the point of these cases is that a non-shutdown caller is unaffected, and an explicit default assertion is what proves it.
- Do not add a budget to any health-check case: giving one would couple a health path to shutdown state it does not own.
- Compatibility impact: none; the expectations are restated, not changed.

## Alternatives considered

- remove the timeout assertions as redundant with row 36 — rejected: this file is the only place the health path's window is pinned.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_health_check.py`

### Procedure
1. Keep the existing terminate-timeout expectations and state in each case that no remaining deadline is supplied.
2. Add one case that asserts the default window is used when the call carries no budget, so the fallback is pinned here rather than implied.

### Method

- Expectation restatement plus one fallback case; no new fixture.

### Details

- The cases assert the call arguments, which is what distinguishes "default used" from "default happened to match".

## Compatibility considerations

- No existing expectation is weakened; the file's behavior assertions are unchanged.

## Security considerations

- N/A: no path or command line is asserted.

## Rollback considerations

- Revert this row's commit with rows 12 and 13.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_http_lifecycle_health_check.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle_health_check.py -q` | the health-check path keeps the default window |

## Completion criteria

- A health-check terminate call with no budget is asserted to use the module default.

## Out of Scope

- Clamping, the confirm window, and the shutdown sequence.

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
- **Related target files**: `tests/agent/test_http_lifecycle_health_check.py`, `scripts/agent/http_lifecycle_health_checker.py`
