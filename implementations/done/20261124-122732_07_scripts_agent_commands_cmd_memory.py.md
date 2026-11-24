## Goal

Route the Memory maintenance subcommands through the job registry and the Memory service layer so this mixin holds no second job reference (REQ-005: command mixins reach SQLite only through `MemoryStore`).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: `_MemoryMixin` dispatch and the audit path.
- Out of scope: the handler implementations in `memory_data_ops.py` and `memory_status.py`, the registry itself.

## Assumptions

- The mixin receives the registry through `AgentContext.services`, so the one-writer-per-store guard stays process-global.
- `MemoryOpResult` (`cmd_memory.py:40`) is the Memory write result type; the job result types in `maintenance_jobs.py` are separate and must not be merged with it.

## Design decisions

- The mixin does not construct or hold a registry: it calls the one carried on `AppServices`, otherwise a per-mixin registry would not see a run started from another mixin.

## Alternatives considered

- N/A: no other ownership choice is open; a second reference would break the single-owner rule in REQ-005.

## Implementation
### Target file
`scripts/agent/commands/cmd_memory.py`

### Procedure
1. Resolve the job through the registry carried on `AppServices` for every Memory maintenance subcommand handled here.
2. Remove the direct service construction path so the mixin uses the injected `MemoryServices` instance only.

### Method
- `_MemoryMixin` keeps its dispatch shape; only the source of the service and the registry changes.

### Details
- `_emit_memory_audit` (`cmd_memory.py:51`) reports the job id alongside the operation result so the audit line and the job record agree.

### Companion test files
- None. tests/agent/commands/test_cmd_memory.py is named by several rows and keeps its own document (row 43).

## Compatibility considerations

- The mixin is constructed by `CommandRegistry`; no signature change, so no other test changes.

## Security considerations

- Routing through the registry is what makes the one-writer-per-store guard visible to Memory runs (REQ-005).

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/commands/cmd_memory.py` | Unit | `uv run pytest tests/agent/commands/test_cmd_memory.py -q` | Service-layer routing, approval flow through the registry |
| Same file | Static grep gate (AC-5) | `rg -n "SQLiteHelper" scripts/agent/commands/` | No Memory maintenance construction remains |

## Completion criteria

- Every Memory maintenance subcommand reached through this mixin is recorded as a job against the same registry instance the other mixins use.

## Out of Scope

- The handlers themselves, the documentation rows, the registry module.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Resolve the registry through `AppServices` and route through `MemoryServices` | Completed | — | 20261124-234217 | Phase 5. The mixin holds no registry of its own; `_emit_memory_audit` reports the job id alongside the result, so `MemoryOpResult` gained a `job_id` field. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-234217 |  |

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
- **Requirement ID**: REQ-005 (Memory service-layer boundary and one registry owner)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/commands/cmd_memory.py`
