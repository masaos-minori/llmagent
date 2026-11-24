## Goal

Update the startup-path lifecycle expectations so the starter's `shutdown_all()` calls match the signature that can carry a remaining deadline (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the two `shutdown_all()` expectations in this file.
- Out of scope: the rollback path (row 16), the routers (row 15), and the coordinator (row 11).

## Assumptions

- The starter calls `shutdown_all()` in the startup path at two points, and today asserts the no-argument form.
- The parameter is optional (rows 13, 14, 15), so the starter keeps calling without a deadline unless a budget is armed (row 16).

## Design decisions

- Assert both forms: the no-argument call keeps working, and a call that carries a deadline is accepted.
- Do not change what the starter itself passes: the rollback path owns that decision (row 16), and this file only pins the surface it calls.
- Compatibility impact: none outside this file.

## Alternatives considered

- delete the no-argument expectation — rejected: a startup that never armed a budget must keep today's behavior (Plan Unknowns UNK-03).

## Implementation
### Target file
`tests/agent/test_startup_mcp_starter.py`

### Procedure
1. Update the two `shutdown_all()` expectations so the called surface accepts the optional remaining-deadline parameter.
2. Keep the no-argument call asserted as today's default path.

### Method

- Expectation updates only; no new fixture.

### Details

- The assertions are about the call surface, which is what row 16 changes the arguments of.

## Compatibility considerations

- Existing startup-path cases keep their current behavior assertions.

## Security considerations

- N/A: no path or command line is asserted.

## Rollback considerations

- Revert this row's commit with row 16.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_startup_mcp_starter.py` | Unit | `uv run pytest tests/agent/test_startup_mcp_starter.py tests/agent/test_startup_rollback.py -q` | the startup path accepts the new signature |

## Completion criteria

- Both startup-path `shutdown_all()` call sites are asserted against the signature that accepts a remaining deadline.

## Out of Scope

- The rollback path's deadline decision.

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
- **Related target files**: `tests/agent/test_startup_mcp_starter.py`, `scripts/agent/startup.py`
