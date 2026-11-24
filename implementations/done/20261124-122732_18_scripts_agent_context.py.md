## Goal

Carry the job registry on `AppServices` so the command registry can reach the single registry instance through the injected service surface (REQ-005: the registry has one owner; REQ-001: one record per maintenance run).

## Scope
**Release unit**: R1-registry-core (Phase 1)

- In scope: the `AppServices` field and its required-service handling.
- Out of scope: the construction point (`factory.py`, row 17), the registry module (row 1).

## Assumptions

- `AppServices` already enforces a required-service invariant loop in `__init__`; the registry joins that set rather than becoming an optional field.
- Step 2 overlap: `scripts/agent/context.py` is also a target row of `plans/20261124-110935_cliplc005_staged-reload-transaction.md`, which adds a `PendingConfigState` field to the same container. The two fields are independent, so the changes are compatible; this plan is ordered first by `tools/plan_dependency_order.py`. The companion test file is shared with that plan for the same reason.

## Design decisions

- Required rather than optional: an optional field would let a command mixin fall back to constructing its own registry, which is the failure mode REQ-005 removes.

## Alternatives considered

- Passing the registry to each mixin in `__init__` — rejected: the mixins already reach services through `AgentContext`; a per-mixin parameter would create per-command guards.

## Implementation
### Target file
`scripts/agent/context.py`

### Procedure
1. Add the registry to `AppServices.__init__` as a required service, consistent with the existing required-service invariant loop.
2. Add no behavior beyond carrying the instance.

### Method
- The field is typed as `MaintenanceJobRegistry` (row 1); no protocol or duck-typed attribute.

### Details
- `skills/DESIGN.md` import-layer contract: `agent.context` may reference the service module it carries; the service module must not import `agent.commands`.

### Companion test files
- `tests/agent/test_context.py`
  - Procedure: assert the required-service handling rejects a missing registry and preserves the invariant with the new field.
  - Validation: `uv run pytest tests/agent/test_context.py -q` (REQ-005; AC-1, AC-7).

## Compatibility considerations

- Existing `AppServices` construction sites must pass the new required service; the factory is the only one (`scripts/agent/factory.py`, row 17).

## Security considerations

- The guard's correctness depends on one instance; a second field would allow a run to be recorded against a different guard.

## Rollback considerations

- N/A: revert the Phase 1 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/context.py` | Unit | `uv run pytest tests/agent/test_context.py tests/agent/test_agent_factory.py -q` | Required-service handling with the new field |
| Same file | Quality gates | `uv run ruff check scripts/agent/context.py`, `uv run mypy scripts/agent/context.py` | No finding |

## Completion criteria

- `AppServices` carries exactly one registry instance, and a context built without it fails the existing required-service invariant.

## Out of Scope

- Construction, registry internals, command handlers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Carry the registry on `AppServices` as a required service | Completed | — | 20261124-160811 | Phase 1 job_registry added as a required service on AppServices. |
| 2 | Update the companion test per Validation plan | Completed | — | 20261124-160811 | Covered by this document tests/agent/test_context.py updated; passes. |
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
- **Requirement ID**: REQ-005 (single registry owner reached through `AppServices`)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/context.py`, `tests/agent/test_context.py`