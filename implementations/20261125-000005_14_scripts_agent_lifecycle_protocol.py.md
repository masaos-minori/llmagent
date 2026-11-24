## Goal

Add the optional remaining-deadline parameter to the lifecycle protocol's `shutdown_all()` so every implementation of the protocol can be reached with a budget (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the `shutdown_all()` signature in the protocol.
- Out of scope: the implementations (rows 11, 13, 15) and the callers (rows 5, 7, 16).

## Assumptions

- The protocol method is `async def shutdown_all(self) -> list[tuple[str, TerminationOutcome]]` (`scripts/agent/lifecycle_protocol.py:36`), and it is one of the five `shutdown_all()` definitions the shutdown sequence must reach.
- Implementations already return one pair per server whose exit was not confirmed, so only the parameter changes.

## Design decisions

- The parameter is optional with no default behavior change: an implementation that ignores it keeps today's fixed windows, which lets rows 11, 13 and 15 land in any order after this one.
- The docstring states that the value is a remaining deadline, not a timeout to add, so an implementation cannot treat it as a fresh window.
- Compatibility impact: none for callers that pass nothing; implementations must accept the keyword.

## Alternatives considered

- add the parameter only to the concrete classes — rejected: the coordinator calls through the protocol, so a parameter the protocol does not declare cannot be passed.

## Implementation
### Target file
`scripts/agent/lifecycle_protocol.py`

### Procedure
1. Add the optional remaining-deadline parameter to `shutdown_all()` (`scripts/agent/lifecycle_protocol.py:36`).
2. State in the docstring that the value is the time left in the shutdown sequence, and that an implementation must not exceed it.

### Method
- Signature-only change; the protocol body stays a stub.

### Details
- The parameter name matches the one rows 11, 13 and 15 use, so the delegations read consistently across the five definitions.

## Compatibility considerations

- Any class implementing the protocol must accept the new keyword; the implementations are rows 11, 13 and 15, and the test doubles are rows 39 and 40.

## Security considerations

- N/A: signature only.

## Rollback considerations

- Revert this row's commit with rows 39 and 40: the signature expectations are asserted there.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/lifecycle_protocol.py` | Unit | `uv run pytest tests/agent/test_lifecycle.py tests/agent/test_agent_factory.py -q` | protocol implementations accept the parameter |

## Completion criteria

- The protocol declares the optional parameter, and every implementation and test double accepts it.

## Out of Scope

- Window clamping, the confirm window, and the step machine.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 39, row 40 |
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
- **Related target files**: `scripts/agent/lifecycle_protocol.py`, `tests/agent/test_lifecycle.py`
