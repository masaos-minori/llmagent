## Goal

Assert that an interrupted index rebuild leaves the vector table consistent, so the transaction boundary added in row 55 is verified against a real database (REQ-002, REQ-006; AC-2, AC-6).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: the real-database tests for `memories_vec` on the session connection.

## Assumptions

- The file's premise stays: unit tests elsewhere model `memories_vec` as a plain table and hide vec0 behavior, so the consistency assertion has to run against a real database.
- The transaction boundary and the cancellation event come from row 55 and row 12; this row asserts them, it does not define them.

## Design decisions

- Assert the post-state: after an interrupted run the vector table matches the state before the run. A test that only checks the returned count cannot show that the rollback happened.

## Alternatives considered

- Modeling the transaction boundary with a fake connection — rejected: this file exists precisely because a model hides vec0 behavior.

## Implementation
### Target file
`tests/agent/memory/test_memory_vec_session.py`

### Procedure
1. Add a case that starts the rebuild through the store accessor, sets the cancellation event during the insert loop, and asserts the vector table is unchanged after the rollback.
2. Keep the existing vec0 behavior assertions unchanged.

### Method

- Use the existing real-database fixture that opens the session connection through the store.

### Details

- The reported count must be zero for the interrupted run, matching the store accessor's result shape (row 12).

## Compatibility considerations

- Runs with rows 12, 55 in the same phase; the accessors themselves are asserted in `tests/agent/memory/test_memory_store.py` (row 44).

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/memory/test_memory_vec_session.py` | Unit | `uv run pytest tests/agent/memory/test_memory_vec_session.py -q` | Interrupted rebuild leaves a consistent vector table |

## Completion criteria

- The test fails if an interrupted run leaves a partially populated vector table or reports a partial count.

## Out of Scope

- The store accessors, the rebuild implementation, the RAG vector path (row 22).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the interrupted-rebuild consistency case | Pending | — | — | Phase 5 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (cancellation through the progress handler), REQ-006 (tracked long-running Memory work)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/memory/test_memory_vec_session.py`
