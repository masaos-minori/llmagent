## Goal

Give the startup rollback path the same bounded termination the shutdown sequence uses, so a failed startup cannot spend more time stopping servers than the budget allows (REQ-010: termination bounded by the shutdown deadline).

## Scope
**Release unit**: R6-termination-budget (Phase 6)

- In scope: `_rollback_servers()` and the `shutdown_all()` call it makes.
- Out of scope: the lifecycle implementations (rows 11, 13, 15) and the shutdown step machine (row 5).

## Assumptions

- Rollback is a second, currently unbudgeted caller of the same termination path: `_rollback_servers()` (`scripts/agent/startup.py:132-149`) calls `lifecycle.shutdown_all()` at `scripts/agent/startup.py:139` with no deadline.
- Rollback is not a shutdown step: it runs during startup, so it has no `ShutdownReport` and its failures keep being reported on the console as they are today.

Step 3b verification against the current source (20261125-122600):

- Anchors moved: `_rollback_servers()` is `scripts/agent/startup.py:138-165` and the `shutdown_all()` call is `:147-149`, not `:132-149` / `:139`.
- The procedure's one-call change needs a source for the value, which the Procedure does not name: `StartupOrchestrator.__init__()` (`:50-56`) gained an optional keyword-only `budget` stored as `self._budget` (`:66`), and `scripts/agent/repl.py` passes the same budget object it gives `SignalHandler`, `ReplInputLoop`, and `ResourceShutdownCoordinator`. Without that the rollback could not reach the deadline the shutdown request set.
- The rollback keeps its own reporting: no `ShutdownReport`, the same `CRITICAL: Startup rollback FAILED` fatal line, and the same unconfirmed-server reporting after the call.

## Design decisions

- The rollback path supplies the remaining deadline of the budget the startup path already holds, rather than inventing its own window: one clock covers both the shutdown sequence and a startup rollback.
- The existing error contract is unchanged: a rollback failure is logged and printed and never replaces the startup error being propagated, which is what the `noqa` comment at `scripts/agent/startup.py:140` records.
- Compatibility impact: a rollback that previously waited the full fixed window now waits only what the budget allows, and reports the same unconfirmed list.

## Alternatives considered

- leave rollback unbudgeted — rejected: an unbudgeted caller of the same termination path reproduces the unbounded-wait problem the Plan states, on a path that is already failing.

## Implementation
### Target file
`scripts/agent/startup.py`

### Procedure
1. Pass the remaining deadline to `lifecycle.shutdown_all()` in `_rollback_servers()` (`scripts/agent/startup.py:132-149`, call at `scripts/agent/startup.py:139`).
2. Keep the existing exception handling, the fatal message, and the unconfirmed-server reporting unchanged.

### Method
- One argument added to one call; the rollback's ownership of its own reporting does not move.

### Details
- When no budget exists on the path (a startup that never armed one), nothing is passed and the implementations fall back to their own defaults.

### Companion test files
- `tests/agent/test_startup_rollback.py`
  - Procedure: assert the rollback `shutdown_all()` call receives the remaining deadline and keeps the exit-status-0 behavior.
  - Validation: `uv run pytest tests/agent/test_startup_rollback.py -q` (REQ-001, REQ-010; AC-1).

## Compatibility considerations

- Tests that assert the rollback call must accept the new argument (companion row 41).

## Security considerations

- N/A: no new output; the existing fatal message is unchanged.

## Rollback considerations

- Revert this row's commit with row 41: the rollback call expectation is asserted there.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/startup.py` | Unit | `uv run pytest tests/agent/test_startup_rollback.py -q` | the rollback call carries the remaining budget |
| `scripts/agent/startup.py` | Unit | `uv run pytest tests/agent/test_startup_mcp_starter.py tests/agent/test_startup_mcp_lifecycle.py -q` | the startup-path lifecycle expectations still hold |

## Completion criteria

- A startup rollback terminates servers within the remaining deadline and still reports every server it could not stop.

## Out of Scope

- Clamping inside the lifecycle implementations, and the shutdown report.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-122329 | 20261125-122329 | StartupOrchestrator.__init__ gained the optional keyword-only budget (:50-56, stored at :66); _rollback_servers() (:138) calls shutdown_all(budget=self._budget) at :147; scripts/agent/repl.py passes the same budget object |
| 2 | Add or update tests per Validation plan | Completed | 20261125-122329 | 20261125-122329 | companion row 41 tests/agent/test_startup_rollback.py: _make_rollback_startup(budget=None), assert_awaited_once_with(budget=None), test_rollback_carries_the_budget_the_repl_supplied |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-122329 | 20261125-122329 | ruff format/check, mypy, lint-imports, pytest Pass; rollback keeps its own console reporting and no ShutdownReport |

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
- **Related target files**: `scripts/agent/startup.py`, `tests/agent/test_startup_rollback.py`