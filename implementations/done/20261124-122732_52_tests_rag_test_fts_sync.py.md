## Goal

Assert the FTS rebuild postcondition: the reported result reflects the row count measured after the insert, not the number of statements attempted (REQ-004; AC-4).

## Scope
**Release unit**: R4-verified-results (Phase 4)

- In scope: the FTS rebuild behavior tests that consume `RagMaintenanceService`.

## Assumptions

- The rebuild logic itself is unchanged; the change is that the method returns a result object with the measured postcondition (row 22), so the test reads that result instead of `None`.

## Design decisions

- Assert the count against the committed state after the run, so the test cannot pass on a run that stopped mid-loop.

## Alternatives considered

- Asserting the FTS contents only — rejected: the requirement is about the reported outcome matching the measured postcondition, which a contents-only assertion does not cover.

## Implementation
### Target file
`tests/rag/test_fts_sync.py`

### Procedure
1. Read the result object the service returns instead of `None`.
2. Assert the postcondition is measured after the insert loop and reported in the result.
3. Add a case where the postcondition does not hold and the result reports it.

### Method

- Use the existing RAG test fixture; no new fixture.

### Details

- The cancellation path is asserted in `tests/agent/services/test_rag_maintenance_persistence.py` (row 46, covered by row 22); this row does not duplicate it.

## Compatibility considerations

- Runs with row 22 in the same release unit. `tools/check_chunks_fts_invariant.py` is not a target row: it whitelists the service file by path (`:36-41`), so neither this test nor the rename reaches it.

## Security considerations

- N/A: test.

## Rollback considerations

- N/A: revert the Phase 4 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/rag/test_fts_sync.py` | Unit | `uv run pytest tests/rag/test_fts_sync.py -q` | FTS rebuild postcondition asserted from the returned result |

## Completion criteria

- The test fails if the result reports success without the postcondition, or reports a count that was not committed.

## Out of Scope

- The service implementation, the cancellation assertions.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read the result object and assert the postcondition | Completed | — | 20261124-192923 | Phase 4 Phase 4 part done: TestRebuildFtsPostcondition reads the result object and asserts the counts are the state after the commit, read through chunks_fts_docsize, and that a run whose postcondition does not agree is reported unverified. 8 tests pass. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261124-192923 | ruff, ruff format and mypy clean on this file; targeted pytest passes. tools/check_chunks_fts_invariant.py reports no violation, so no docs row or tool-description entry changes for this row. |

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
- **Requirement ID**: REQ-004 (verified result before the success line)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `tests/rag/test_fts_sync.py`