## Goal
- Remove the redundant `patch("db.helper.SQLiteHelper", ...)` from the `store` fixture (`REQ-002`).

## Scope
- Only line 147 of the `store` fixture.

## Assumptions
- The fixture already patches `agent.memory.write_ops`, `agent.memory.store`, and `agent.memory.count_ops`; `MemoryStore` does not use `import_ops` (Plan `UNK-02`).

## Design decisions
- Delete the one patch line; keep the other three.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/memory/test_memory_store.py`

### Procedure
1. Remove `patch("db.helper.SQLiteHelper", return_value=fake),` from the `with (...)` block in the `store` fixture.

### Method
- Run the file; if a test fails, restore the line and add `# mock-patch-ok: redundant origin patch; the three importers are patched explicitly` to it instead.

### Details
- The `patch` import stays in use (other patches in this file).

## Compatibility considerations
N/A: test-only change; no runtime or public interface is affected.

## Security considerations
N/A: no input handling, credentials, or I/O boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/memory/test_memory_store.py -v`; `uv run ruff check tests/agent/memory/test_memory_store.py`.

## Completion criteria
- The file passes with the line removed (or marked, per the fallback) and ruff clean.

## Out of scope
- Any other fixture or test in this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the redundant origin patch from the `store` fixture | Completed | 20261012-130046 | 20261012-130059 | changed: tests/agent/memory/test_memory_store.py (redundant db.helper patch removed from store fixture) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched files | Completed | 20261012-130059 | 20261012-130059 | ruff format/check pass; 40 tests pass; no fallback marker needed (UNK-02 resolved) |

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
- **Requirement ID**: `REQ-002` (remove the dead fixture and the redundant origin patches)
- **Source issue**: issues/20261012-120426_mock001_fix-ineffective-mock-patch-targets-in-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-120856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-121424
- **Related target files**: tests/agent/memory/test_memory_store.py