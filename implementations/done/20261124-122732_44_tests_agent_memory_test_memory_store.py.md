## Goal

Test the new `MemoryStore` maintenance accessors for existence, transaction boundaries, and cancellation, so the Memory write path's single owner is verified (REQ-002, REQ-005, REQ-008; AC-2, AC-5).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: accessor tests, transaction-boundary tests, cancellation tests.

## Assumptions

- The accessors are those row 12 adds; this row asserts them, it does not define them.
- Cancellation is asserted through a progress callback: the test sets the event and asserts the run stops at the next callback, which is what `interrupt_when` can do.

## Design decisions

- Assert the transaction boundary by observing partial state: an interrupted run must leave no partially populated index and no partial delete. A test that only checks the return value cannot show atomicity.

## Alternatives considered

- Asserting only the returned counts — rejected: AC-5 and REQ-008 are about the committed state, not the reported number.

## Implementation
### Target file
`tests/agent/memory/test_memory_store.py`

### Procedure
1. Add tests for the rebuild, reindex, prune, and pinned-count accessors.
2. Add a transaction-boundary test for the prune select-and-delete and the index rebuilds.
3. Add a cancellation test that sets the event and asserts the interrupted outcome is reported.

### Method

- Use the existing Memory test fixture that constructs the store through the service facade, so the test exercises the same path the command mixins use.

### Details

- The reported count must equal the committed count; the test reads the committed state after the run.

### Companion test files

- None; this row is its own document. It is named by rows 12 and 55.

## Compatibility considerations

- Runs with rows 12, 13, 55 in the same phase; `tests/agent/memory/test_memory_vec_session.py` (row 57) covers the interrupted vector table.

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/memory/test_memory_store.py` | Unit | `uv run pytest tests/agent/memory/test_memory_store.py -q` | Accessors exist, transaction boundaries honored, cancellation honored |
| Same area | Layering | `PYTHONPATH=scripts uv run lint-imports` | 6 contracts kept, 0 broken |

## Completion criteria

- The test fails if a command mixin can reach SQLite directly, if an interrupted run leaves partial state, or if the reported count differs from the committed count.

## Out of Scope

- The accessor implementations, the command mixins.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add accessor, transaction-boundary, and cancellation tests | Completed | — | 20261124-234217 | Phase 5. The transaction-boundary assertions read committed state rather than return values, and the interrupted cases use a helper that refuses the next statement once the stop event is set because `interrupt_when` cannot stop a single short statement. |
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
- **Requirement ID**: REQ-002 (cancellation), REQ-005 (Memory service-layer boundary), REQ-008 (atomic limits and destructive maintenance)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/memory/test_memory_store.py`
