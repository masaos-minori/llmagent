## Goal

Replace the direct `SQLiteHelper` mocks in the status tests with the `MemoryStore` accessor path, so the test asserts the service-layer boundary rather than the removed construction (REQ-005; AC-5).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: the mocked direct-construction path that stands in for `memory_status.py:85-87`.

## Assumptions

- The status output itself is unchanged for the same data; only the source of the counts changes, so the expected output assertions stay as they are.

## Design decisions

- Mock the accessor, not the connection, so the test fails if the command mixin opens its own connection again — that is the AC-5 condition.

## Alternatives considered

- Keeping the connection mock and adding a separate grep gate only — rejected: the grep gate is run by the validation sequence, but the test that used the mock would no longer describe the implemented path.

## Implementation
### Target file
`tests/agent/commands/test_memory_status.py`

### Procedure
1. Replace the direct `SQLiteHelper` mock with the `MemoryServices` → `MemoryStore` path.
2. Keep the rendered-table expectations unchanged.
3. Assert the pinned count comes from the pinned-count accessor.

### Method

- No new fixture; the existing status fixture is repointed at the facade.

### Details

- N/A: no other assertion changes.

## Compatibility considerations

- Runs with row 8 in the same phase.

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/commands/test_memory_status.py` | Unit | `uv run pytest tests/agent/commands/test_memory_status.py -q` | Status reads go through `MemoryStore` |
| Same area | Static grep gate (AC-5) | `rg -n "SQLiteHelper" scripts/agent/commands/` | No Memory maintenance construction remains |

## Completion criteria

- The test passes only when the status path reads through the store, and the rendered output is unchanged for the same data.

## Out of Scope

- The status implementation, the store accessors.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Repoint the mock at the service-layer path | Completed | — | 20261124-234217 | Phase 5. The accessor is the mock, so the test fails if the status path builds its own connection again (AC-5); the rendered-table expectations are unchanged. |
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
- **Requirement ID**: REQ-005 (Memory service-layer boundary)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/commands/test_memory_status.py`
