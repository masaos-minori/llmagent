## Goal

Read Memory store state through `MemoryStore` instead of opening a `SQLiteHelper` connection in the status path (REQ-005: command mixins reach SQLite only through the Memory service layer).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: `build_memory_status()`.
- Out of scope: the `MemoryStore` accessors it calls (row 12), the `MemoryStatus` dataclass shape.

## Assumptions

- `MemoryStatus` (`memory_status.py:14`) keeps its fields; only the source of the counts changes.
- The counts come from the new store accessors defined in row 12.

## Design decisions

- Status is a read path and registers with `ApprovalLevel.NONE`; it is still recorded because the plan requires every maintenance run to have a record.

## Alternatives considered

- N/A: no alternative keeps the AC-5 grep gate passing.

## Implementation
### Target file
`scripts/agent/commands/memory_status.py`

### Procedure
1. Replace the direct `SQLiteHelper("session", ...)` construction at `memory_status.py:85-87` with `MemoryStore` accessors reached through `MemoryServices`.
2. Keep `build_status_table` (`memory_status.py:35`) unchanged; it renders whatever the status object carries.

### Method
- No new field in `MemoryStatus`; the accessor results map onto the existing fields.

### Details
- The pinned count uses the pinned-count accessor added in row 12, so the status figure and the pin limit read the same source.

### Companion test files
- None. tests/agent/commands/test_memory_status.py keeps its own document (row 48).

## Compatibility considerations

- `tests/agent/commands/test_memory_status.py` mocks the direct construction; that mock is replaced in the same phase.

## Security considerations

- N/A: read-only path; the trust boundary is unchanged.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/commands/memory_status.py` | Unit | `uv run pytest tests/agent/commands/test_memory_status.py -q` | Status reads go through `MemoryStore` |
| Same file | Static grep gate (AC-5) | `rg -n "SQLiteHelper" scripts/agent/commands/` | No Memory maintenance construction remains |

## Completion criteria

- The status output is identical to today's for the same data, and the file contains no direct `SQLiteHelper` construction.

## Out of Scope

- The store accessors (row 12), the registry module.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read status through `MemoryStore` accessors | Completed | — | 20261124-234217 | Phase 5. `build_memory_status()` reads the pinned count through the store accessor; `MemoryStatus` fields and `build_status_table` are unchanged, and status registers with `ApprovalLevel.NONE`. |
| 2 | Update tests per Validation plan | Completed | — | 20261124-234217 | Row 48 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-234217 |  |

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
- **Requirement ID**: REQ-005 (Memory service-layer boundary)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/commands/memory_status.py`
