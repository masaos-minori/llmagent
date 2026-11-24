## Goal

Pass the remaining deadline through `shutdown_all()` and the terminate calls this module owns, so the fixed `TERMINATE_TIMEOUT_SEC` no longer decides how long a bounded shutdown may wait (REQ-010: termination bounded by the shutdown deadline; AC-2, AC-4).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: `shutdown_all()` and the three uses of `TERMINATE_TIMEOUT_SEC` in this module.
- Out of scope: the coordinator that clamps the per-server windows (row 11), the terminator's confirm window (row 12), and the protocol and router signatures (rows 14, 15).

## Assumptions

- `TERMINATE_TIMEOUT_SEC: float = 5.0` (`scripts/agent/http_lifecycle.py:49`) is used at three call sites: the shutdown wiring (`scripts/agent/http_lifecycle.py:96`), the health-check wiring (`scripts/agent/http_lifecycle.py:312`), and the startup-failure termination (`scripts/agent/http_lifecycle.py:378`).
- `shutdown_all()` (`scripts/agent/http_lifecycle.py:413-420`) is a thin delegation to the shutdown coordinator and returns the servers whose exit was not confirmed.

## Design decisions

- `shutdown_all()` takes an optional remaining deadline and forwards it unchanged to the coordinator (row 11), which is the component that clamps per-server windows; this module does not clamp.
- The health-check and startup-failure uses keep the constant: they are not shutdown-sequence steps, and giving them a budget they do not own would couple unrelated paths.
- The parameter is optional so the protocol and router delegations (rows 14, 15) can land in either order.
- Compatibility impact: none for callers that pass nothing; the shutdown path changes only once row 5 supplies the deadline.

## Alternatives considered

- make the constant read from the budget — rejected: the module would then depend on shutdown state it does not own, and the health-check path would change behavior for no reason.

## Implementation
### Target file
`scripts/agent/http_lifecycle.py`

### Procedure
1. Add the optional remaining-deadline parameter to `shutdown_all()` (`scripts/agent/http_lifecycle.py:413-420`) and pass it to `self._shutdown_coordinator.shutdown_all()`.
2. Keep `TERMINATE_TIMEOUT_SEC` (`scripts/agent/http_lifecycle.py:49`) as the value used by the shutdown wiring (`scripts/agent/http_lifecycle.py:96`) only as the fallback the coordinator applies when no deadline arrives.
3. Leave the health-check wiring (`scripts/agent/http_lifecycle.py:312`) and the startup-failure termination (`scripts/agent/http_lifecycle.py:378`) on the constant.

### Method
- Threading only: this row changes which value reaches the coordinator, not how termination is performed.

### Details
- The returned list of unconfirmed servers is unchanged in shape, which is what the step record counts (REQ-012).

## Compatibility considerations

- The optional parameter keeps every existing call site working, including the router delegations (row 15) and the factory-assembled lifecycle surface (row 40).

## Security considerations

- N/A: no new output or path handling.

## Rollback considerations

- Revert this row's commit with rows 35 and 39: the integration and signature expectations are asserted there.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/http_lifecycle.py` | Unit | `uv run pytest tests/agent/test_http_lifecycle.py tests/agent/test_lifecycle.py -q` | terminate-timeout expectations hold with and without a supplied deadline |
| `scripts/agent/http_lifecycle.py` | Integration | `uv run pytest tests/agent/test_http_lifecycle_integration.py -q` | the shutdown path honors the supplied deadline |

## Completion criteria

- A deadline supplied to `shutdown_all()` reaches the coordinator, and a call with no deadline behaves exactly as today.

## Out of Scope

- Window clamping, the confirm window, and the SIGINT guard.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | rows 35, 36, 39 |
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
- **Related target files**: `scripts/agent/http_lifecycle.py`, `tests/agent/test_http_lifecycle_integration.py`
