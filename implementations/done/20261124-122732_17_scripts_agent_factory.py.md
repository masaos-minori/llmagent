## Goal

Construct the job registry in the service factory and inject it into `AppServices`, so the registry has exactly one owner in the process (REQ-005: the registry has one owner reachable by the command mixins; REQ-001: one record per maintenance run).

## Scope
**Release unit**: R1-registry-core (Phase 1)

- In scope: the construction and injection point.
- Out of scope: the `AppServices` field itself (row 18), the registry module (row 1).

## Assumptions

- Services are built only in `factory.py`; this row does not introduce a second construction path.
- `scripts/agent/factory.py` is a shared row: `plans/20261124-095950_cliplc004_bounded-shutdown-machine.md` changes the lifecycle surface the factory assembles, and `plans/20261124-110935_cliplc005_staged-reload-transaction.md` constructs `PendingConfigState` here. Each plan adds a different service or signature, so no symbol is shared and the changes are compatible; `tools/plan_dependency_order.py` places this plan first, so the registry wiring lands before those rows. The companion test file is shared with both plans for the same reason.

## Design decisions

- The registry is built in the factory and carried on `AppServices` rather than created per command mixin, so the one-writer-per-store guard is process-global (Plan Design, framework decision).

## Alternatives considered

- Lazy construction on first use — rejected: two mixins would then hold different instances and the guard would be per-command.

## Implementation
### Target file
`scripts/agent/factory.py`

### Procedure
1. Construct `MaintenanceJobRegistry` in the factory and pass it to `AppServices` as a required service.
2. Keep the existing service construction order unchanged; the registry takes no database connection.

### Method
- No new configuration key; the registry is constructed with no arguments.

### Details
- The factory does not import `agent.commands`; the registry module does not import `agent.commands` either (`skills/DESIGN.md` import-layer contract).

### Companion test files
- `tests/agent/test_agent_factory.py`
  - Procedure: assert the registry is constructed once and is the instance the context receives.
  - Validation: `uv run pytest tests/agent/test_agent_factory.py -q` (REQ-001, REQ-005; AC-1, AC-7).

## Compatibility considerations

- `AppServices` required-service handling is covered by row 18 and its test row 59 in the same phase.

## Security considerations

- The single owner is what makes the approval guard enforceable; two owners would let a run bypass the guard.

## Rollback considerations

- Remove the constructed service and the `AppServices` argument; no persisted state depends on it.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/factory.py` | Unit | `uv run pytest tests/agent/test_agent_factory.py -q` | Registry constructed and injected |
| Same file | Quality gates | `uv run ruff check scripts/agent/factory.py`, `uv run mypy scripts/agent/factory.py` | No finding |

## Completion criteria

- A single `MaintenanceJobRegistry` instance exists per process, and every command mixin reaches that instance through `AppServices`.

## Out of Scope

- The `AppServices` field, the registry internals, the command handlers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Construct the registry and inject it into `AppServices` | Completed | — | 20261124-160811 | Phase 1 Registry constructed in factory.py and injected into AppServices. |
| 2 | Update the companion test per Validation plan | Completed | — | 20261124-160811 | Covered by this document tests/agent/test_agent_factory.py updated; passes. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-160811 | Quality gates and targeted pytest pass. |

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
- **Requirement ID**: REQ-001 (one record per maintenance run), REQ-005 (single registry owner)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/factory.py`, `tests/agent/test_agent_factory.py`