## Goal

Confirm that the lifecycle surface the agent factory assembles accepts the remaining deadline, so the object the shutdown coordinator calls is the one that can carry a budget (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: the `shutdown_all()` expectations against the factory-assembled lifecycle object.
- Out of scope: the protocol (row 14), the routers (row 15), and the coordinator (row 5).

## Assumptions

- The factory wires the lifecycle object the coordinator calls, and this file asserts that surface through 10 `shutdown_all` references.
- The parameter is optional (rows 13, 14, 15), so the factory itself needs no change; only the assertions about the assembled object do.

Step 3b verification against the current source (20261125-122600):

- The file has 19 `shutdown_all` references after this row's change, not 10.
- The new class is `TestLifecycleShutdownSurfaceAcceptsBudget` (`tests/agent/test_agent_factory.py:493`). `test_shutdown_all_declares_an_optional_budget` (`:505`) is parametrized over `_ServerLifecycleRouter`, `_SubprocessLifecycleManager`, and `LifecycleManagerProtocol`, and pins `inspect.Parameter.KEYWORD_ONLY` with `default is None` on each `shutdown_all` declaration. That is the contract rows 14 and 15 must keep for the factory's wiring to stay valid.
- `test_assembled_router_forwards_the_budget_it_is_given` (`:513`) is the one forwarding case: the object the factory assembles passes the budget it is given down to the low-level manager.

## Design decisions

- Assert the assembled object's method accepts the parameter, rather than asserting the factory passes one: the factory does not own the deadline, the shutdown sequence does (row 7).
- Keep the existing assembly assertions intact so a change in wiring is still caught by this file.
- Compatibility impact: none outside this file.

## Alternatives considered

- skip this file and rely on row 39 — rejected: row 39 tests doubles, and this file is the one that proves the real assembled object matches them.

## Implementation
### Target file
`tests/agent/test_agent_factory.py`

### Procedure
1. Update the `shutdown_all()` expectations so the assembled lifecycle method accepts the optional remaining-deadline parameter.
2. Add one case that calls the assembled method with a deadline and asserts it is accepted.
3. Leave the existing assembly and wiring assertions unchanged.

### Method

- Assertion updates against the real assembled object; no new fixture.

### Details

- The case asserts acceptance, not behavior: behavior is covered by rows 35 and 39.

## Compatibility considerations

- Overlap: this file is also a target row of the frozen cliplc005 Plan (`plans/20261124-110935_cliplc005_staged-reload-transaction.md`) and of the cliplc003 Plan (`plans/done/20261124-001800_cliplc003_maintenance-job-framework.md`). `tools/plan_dependency_order.py` places this Plan before cliplc005, and cliplc003's procedures under `implementations/20261124-122732_` land first; re-run `tools/check_plan_target_overlaps.py` after each lands.

## Security considerations

- N/A: no path or command line is asserted.

## Rollback considerations

- Revert this row's commit with rows 13, 14 and 15.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/test_agent_factory.py` | Unit | `uv run pytest tests/agent/test_agent_factory.py tests/agent/test_lifecycle.py -q` | the assembled lifecycle surface accepts the budget |

## Completion criteria

- The factory-assembled lifecycle object accepts a remaining deadline on `shutdown_all()`.

## Out of Scope

- The factory's own wiring and the termination behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-122329 | 20261125-122329 | TestLifecycleShutdownSurfaceAcceptsBudget (:493) parametrized over the three lifecycle surfaces |
| 2 | Add or update tests per Validation plan | Completed | 20261125-122329 | 20261125-122329 | this row is the test row this row is the test row; test_shutdown_all_declares_an_optional_budget (:505) pins KEYWORD_ONLY with default None, test_assembled_router_forwards_the_budget_it_is_given (:513) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-122329 | 20261125-122329 | ruff format/check, pytest Pass |

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
- **Related target files**: `tests/agent/test_agent_factory.py`, `scripts/agent/lifecycle_router.py`