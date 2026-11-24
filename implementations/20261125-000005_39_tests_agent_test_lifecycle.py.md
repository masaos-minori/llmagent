## Goal

Update the protocol and router signature expectations so every lifecycle implementation and test double in this file accepts the optional remaining-deadline parameter (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the `shutdown_all()` and `terminate_with_timeout()` expectations in this file.
- Out of scope: the protocol declaration (row 14), the routers (row 15), the manager (row 13), and the coordinator (row 11).

## Assumptions

- This file is the signature-level consumer: 15 `shutdown_all` and 20 `terminate_with_timeout` references, including the doubles that stand in for the protocol implementations.
- A double that does not accept the new keyword fails as soon as a caller forwards it, so the doubles must change in the same release unit as rows 14 and 15.

## Design decisions

- Update the doubles to accept the parameter and assert it is forwarded, rather than accepting it and ignoring it: the point of the signature tests is that the value survives the delegation chain.
- Keep the no-argument cases: they are what prove the parameter is optional.
- Compatibility impact: none outside this file.

## Alternatives considered

- rely on the integration file (row 35) to catch a missing keyword — rejected: an integration failure would name the wrong layer.

## Implementation
### Target file
`tests/agent/test_lifecycle.py`

### Procedure
1. Add the optional remaining-deadline parameter to every `shutdown_all()` double in this file so it matches the protocol declaration (row 14).
2. Assert that each router delegation forwards the value it received (row 15).
3. Keep the existing no-argument cases asserting today's default behavior.

### Method

- Signature and forwarding assertions on the doubles; no new fixture.

### Details

- The forwarding assertion is made on the recorded call arguments of the double, which is how a dropped argument would be caught.

## Compatibility considerations

- Doubles here mirror rows 14 and 15; landing this file before those rows fails, landing it after leaves them unguarded.

## Security considerations

- N/A: no path or command line is asserted.

## Rollback considerations

- Revert this row's commit with rows 13, 14 and 15.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_lifecycle.py` | Unit | `uv run pytest tests/agent/test_lifecycle.py tests/agent/test_agent_factory.py -q` | every implementation and double accepts and forwards the parameter |

## Completion criteria

- No `shutdown_all()` definition or double rejects the parameter, and each router's forwarding is asserted.

## Out of Scope

- Clamping, the confirm window, and the step machine.

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
- **Related target files**: `tests/agent/test_lifecycle.py`, `scripts/agent/lifecycle_protocol.py`, `scripts/agent/lifecycle_router.py`
