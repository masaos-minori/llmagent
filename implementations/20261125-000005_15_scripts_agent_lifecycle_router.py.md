## Goal

Forward the remaining deadline through both router delegations so the budget reaches the lifecycle implementations the coordinator calls through the routers (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the two `shutdown_all()` definitions in this module.
- Out of scope: the protocol declaration (row 14), the HTTP manager implementation (row 13), and the shutdown coordinator (row 11).

## Assumptions

- Two of the five `shutdown_all()` definitions live here: the HTTP delegation (`scripts/agent/lifecycle_router.py:79-81`) and the composite router's own definition (`scripts/agent/lifecycle_router.py:257-260`), which sets `self._shutting_down` and then delegates to the subprocess manager.
- Both return the unconfirmed-server list unchanged, so forwarding a parameter does not alter the return contract.

## Design decisions

- Pure forwarding: the routers do not clamp, default, or interpret the value, because the coordinator (row 11) is the component that owns clamping.
- The composite router forwards the same value to the subprocess manager it already calls, so the two delegations cannot end up with different windows.
- Compatibility impact: none for callers that pass nothing.

## Alternatives considered

- let the router default the value to its own constant — rejected: a default inside a delegation is a second authority, which is what REQ-010 removes.

## Implementation
### Target file
`scripts/agent/lifecycle_router.py`

### Procedure
1. Add the optional remaining-deadline parameter to the HTTP router's `shutdown_all()` (`scripts/agent/lifecycle_router.py:79-81`) and pass it to `self._http_mgr.shutdown_all()`.
2. Add the same parameter to the composite router's `shutdown_all()` (`scripts/agent/lifecycle_router.py:257-260`) and pass it to `self._subprocess_mgr.shutdown_all()`, keeping the existing state marking and per-server state updates.

### Method
- Signature plus one argument per delegation; no logic is added.

### Details
- The parameter name matches the protocol declaration (row 14) so the keyword passes through all five definitions consistently.

## Compatibility considerations

- Test doubles that implement these methods must accept the keyword (row 39, row 40).

## Security considerations

- N/A: forwarding only.

## Rollback considerations

- Revert this row's commit with row 39: the router signature expectations are asserted there.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/lifecycle_router.py` | Unit | `uv run pytest tests/agent/test_lifecycle.py -q` | both delegations accept and forward the parameter |

## Completion criteria

- A deadline passed to either router reaches the implementation it delegates to, and a call with no deadline behaves as today.

## Out of Scope

- Clamping, defaults, and the confirm window.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | row 39 |
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
- **Related target files**: `scripts/agent/lifecycle_router.py`, `tests/agent/test_lifecycle.py`
