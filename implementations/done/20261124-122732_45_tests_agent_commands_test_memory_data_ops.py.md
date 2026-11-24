## Goal

Test the Memory data operations for single-transaction prune with re-validated candidates, service-layer routing, registry approval, atomic pin limit, and delete consistency under interruption (REQ-003, REQ-005, REQ-006, REQ-008; AC-3, AC-5, AC-6).

## Scope
**Release unit**: R5-memory-layering (Phase 5); the approval assertions are R3-memory-approval (Phase 3)

- In scope: the prune path, the pin path, the delete path, the approval path.

## Assumptions

- This is the single test row for the file; the frozen table previously listed it twice and both responsibilities are covered here.
- The store accessors and the transaction boundaries are those rows 12, 14, 15 implement; this row asserts them from the command layer.

## Design decisions

- The pin-limit test must run two concurrent jobs, because the requirement is about a limit exceeded under concurrency; a single-job test cannot show it.
- The prune test asserts the count reported equals the rows deleted inside the transaction, not a count read on a second connection.

## Alternatives considered

- Asserting the pin limit with a mocked count — rejected: a mock cannot show that the check is evaluated inside the transaction.

## Implementation
### Target file
`tests/agent/commands/test_memory_data_ops.py`

### Procedure
1. Replace the direct `SQLiteHelper` mocks with the `MemoryStore` accessor path through `MemoryServices`.
2. Add a single-transaction prune test with a concurrent writer that changes the candidate set between the count and the delete, and assert the reported count is the deleted count.
3. Add an atomic pin-limit test with two concurrent jobs against `memory_max_pinned`.
4. Add a delete-consistency test under interruption: no change event is emitted for a row that was not removed.
5. Assert a destructive run without registry approval is refused before any write.

### Method

- Use the factory-built context so the test exercises the single registry instance; run the concurrent jobs through the same store.

### Details

- The append-only event contract itself is asserted in `tests/agent/memory/test_jsonl_store.py` (row 58, its own document).

### Companion test files

- None; this row is its own document. It is named by rows 6, 14, 15.

## Compatibility considerations

- Runs with rows 6, 12, 14, 15 in the same phase.

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 5 commit; the approval assertions are a Phase 3 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/agent/commands/test_memory_data_ops.py` | Unit | `uv run pytest tests/agent/commands/test_memory_data_ops.py tests/agent/commands/test_memory_status.py -q` | Single-transaction prune, atomic pin limit, delete consistency, service routing, registry approval |
| Same area | Static grep gate (AC-5) | `rg -n "SQLiteHelper" scripts/agent/commands/` | No Memory maintenance construction remains |

## Completion criteria

- The test fails if the reported count differs from the committed count, if the limit can be exceeded under concurrency, or if a change event is emitted for a row that was not deleted.

## Out of Scope

- The store accessors, the pin implementation, the jsonl append-only contract.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace direct-SQLite mocks with the service-layer path | Completed | — | 20261124-234217 | Phase 5 |
| 2 | Add the single-transaction prune and atomic pin-limit tests | Completed | — | 20261124-234217 | Phase 5 |
| 3 | Add the delete-consistency-under-interruption test | Completed | — | 20261124-234217 | Phase 5 |
| 4 | Assert registry approval for destructive runs | Completed | — | 20261124-234217 | Phase 3 |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-234217 |  |

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
- **Requirement ID**: REQ-003 (approval levels), REQ-005 (Memory service-layer boundary), REQ-006 (tracked Memory work), REQ-008 (atomic limits and destructive maintenance)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/agent/commands/test_memory_data_ops.py`
