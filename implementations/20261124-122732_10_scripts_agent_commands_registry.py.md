## Goal

Add the job command handler path to the dispatcher without changing the registry's mixin composition, so the pinned MRO counts stay 10 and 8 (REQ-002: `/jobs cancel <id>` dispatches to a real handler; REQ-010: every registered command has a handler in the registry).

## Scope
**Release unit**: R2-job-commands (Phase 2)

- In scope: the `_cmd_jobs` handler path inside an existing mixin.
- Out of scope: the `CommandDef` registration (row 9), the completion set (row 11), the test assertions (row 41).

## Assumptions

- The handler is placed in an existing mixin rather than a new `*Mixin` class, per the plan decision recorded 2026-11-24.
- `test_command_def_sync.py` (row 49) requires the handler name to exist on the registry, so the handler name must match the `CommandDef.handler` value exactly.

## Design decisions

- No new mixin: adding one would change the counts asserted at `tests/agent/commands/test_command_registry_consistency.py:155-164` (10 `*Mixin` classes in the MRO) and `:166-173` (8 direct `*Mixin` bases), so the handler belongs to an existing mixin.

## Alternatives considered

- A `JobMixin` (new) — rejected for the reason above; the counts are a contract pinned by tests, not an accident.

## Implementation
### Target file
`scripts/agent/commands/registry.py`

### Procedure
1. Add `_cmd_jobs` (new) to an existing mixin, reachable through `CommandRegistry.dispatch` (`registry.py:171`).
2. Resolve the job by id for `status`, and call `cancel` on the registry for `cancel <id>`; state the refusal reason for a `not_cancelable` job.
3. Keep `__init__` unchanged: the registry instance is read from `self._ctx.services`.

### Method
- The handler formats nothing beyond the state lines; the outcome text comes from the job record.

### Details
- All `_cmd_*` methods operate only on `AgentContext` per the module contract (`registry.py:7,64`); the job handler must not reach `AgentREPL`.

### Companion test files
- None. tests/agent/commands/test_command_registry_consistency.py keeps its own document (row 41).

## Compatibility considerations

- Handler-shape assertions in `tests/agent/commands/test_command_registry_consistency.py` and `tests/agent/commands/test_cmd_registry_ingest_removal.py` are updated in the same phase (rows 41, 53).

## Security considerations

- The handler enforces nothing itself; approval is decided at registration. The handler only reports the recorded decision.

## Rollback considerations

- N/A: revert the Phase 2 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/commands/registry.py` | Unit | `uv run pytest tests/agent/commands/test_command_registry_consistency.py tests/agent/commands/test_command_def_sync.py -q` | `/jobs` handler exists, counts unchanged |
| Same file | Quality gates | `uv run ruff check scripts/agent/commands/registry.py`, `uv run mypy scripts/agent/commands/registry.py` | No finding |

## Completion criteria

- `/jobs status <id>` and `/jobs cancel <id>` dispatch to a handler in an existing mixin, and the MRO counts remain 10 and 8.

## Out of Scope

- The registration list, the completion candidate set, the command documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_cmd_jobs` inside an existing mixin | Pending | — | — | Phase 2 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Tests updated by row 41 |

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
- **Requirement ID**: REQ-002 (`/jobs cancel <id>` dispatch target), REQ-010 (registered commands have handlers)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/commands/registry.py`
