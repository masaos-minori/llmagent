## Goal

Make the RAG service surface match what it does: rename the vector method to the operation it performs, give the FTS rebuild a postcondition and a result object, and accept the cancellation event (REQ-007: name matches behavior; REQ-004: success only after the postcondition; REQ-002: cooperative interruption).

## Scope
**Release unit**: R1-registry-core (Phase 1, cancellation); the postcondition is R4-verified-results (Phase 4); the rename is R6-rag-vector-contract (Phase 6)

- In scope: `rebuild_fts`, `rebuild_vec`, `consistency`.
- Out of scope: the subcommand spec (`command_defs_list.py`, row 9), the guidance text (`rag_consistency.py`, row 20). `tools/check_chunks_fts_invariant.py` is not in scope: it sanctions this whole file through `SANCTIONED_PATHS` (`:36-41`) and the function-name check it defines is not called, so the rename does not reach it.

## Assumptions

- The rename decision is `prune_orphan_vectors()` and `/session rag-prune-vec` (plan decision OD-01, 2026-11-24); the old name is not kept as an alias.
- Vector rows cannot be regenerated from `chunks`: the embeddings live only in `chunks_vec`, so the method cannot be made a true rebuild.

## Design decisions

- The method returns the pruned and remaining counts as a result object rather than an `int`, so the caller can report a verified outcome (REQ-004).
- `rebuild_fts` measures the postcondition after the insert loop before returning, so a run that did not verify cannot report success.

## Alternatives considered

- Keeping `rebuild_vec` and documenting that it only prunes — rejected: the name is the thing the requirement removes.

## Implementation
### Target file
`scripts/agent/services/rag_maintenance_service.py`

### Procedure
1. Rename `rebuild_vec()` (`rag_maintenance_service.py:92-109`) to `prune_orphan_vectors()` and return the pruned and remaining counts in a result object.
2. Give `rebuild_fts()` (`:44-57`) a postcondition — re-measure the FTS row count against `chunks` after the insert — and return a result object instead of `None`.
3. Keep the existing `stop` parameter on `consistency()` (`:59-69`) and add it to the two write methods, passing it to `db.interrupt_when`.

### Method
- `stats_rag` (`:35`) and `reconcile_url` (`:111`) are unchanged; they are read and per-URL paths, not job-registered writes.

### Details
- The service instance must be the injected one so the registry carries the job; `cmd_session.py:156-158` currently builds it per call (row 3).

### Companion test files
- `tests/agent/services/test_rag_maintenance_persistence.py`
  - Procedure: assert the renamed method reports pruned and remaining counts, the FTS postcondition runs before the result, and cancellation is honored.
  - Validation: `uv run pytest tests/agent/services/test_rag_maintenance_persistence.py -q` (REQ-002, REQ-004, REQ-007; AC-2, AC-4, AC-8).

## Compatibility considerations

- The method name is referenced by `tests/rag/test_fts_sync.py` (row 52) and the generated API tables (rows 36, 37, 38). `tools/check_chunks_fts_invariant.py` whitelists this file by path, not by method name, so it is unaffected by the rename.

## Security considerations

- Both methods write against `rag.sqlite`; the run must be recorded so the one-writer guard sees it.

## Rollback considerations

- Revert the Phase 6 commit for the rename and the Phase 4 commit for the postcondition separately.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/services/rag_maintenance_service.py` | Unit | `uv run pytest tests/agent/services/test_rag_maintenance_persistence.py tests/rag/test_fts_sync.py -q` | Name, behavior, counts, postcondition agree |
| Same file | Checker (regression) | `uv run python tools/check_chunks_fts_invariant.py` | No finding; the checker whitelists this file by path (`:36-41`), so the rename does not affect it |
| Same file | Quality gates | `uv run ruff check scripts/agent/services/rag_maintenance_service.py`, `uv run mypy scripts/agent/services/rag_maintenance_service.py` | No finding |

## Completion criteria

- The service method name states what it does, each write returns a verified result, and an interrupted run reports `cancelled` rather than success.

## Out of Scope

- The command spec, the guidance text, the tool description, the generated tables.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Accept the cancellation event | Completed | — | 20261124-192923 | Phase 1 Phase 4 part: stop is accepted by rebuild_fts() and rebuild_vec() and passed to db.interrupt_when; a non-interruption sqlite3.OperationalError is re-raised rather than reported as an interrupted run. |
| 2 | Add the FTS postcondition and the result object | Completed | — | 20261124-192923 | Phase 4 Phase 4 part done: rebuild_fts() returns RagFtsRebuildResult and measures the postcondition after the commit, reading the index row count from chunks_fts_docsize against chunks, so verified is the measured agreement; the counts are chunks and fts_rows, not an attempt flag. |
| 3 | Rename `rebuild_vec` to `prune_orphan_vectors` (new) | Pending | — | — | Phase 6 |
| 4 | Update the companion test per Validation plan | In Progress | — | — | Covered by this document Phase 4 part done in tests/agent/services/test_rag_maintenance_persistence.py (row 46): TestRebuildFtsPostcondition asserts the postcondition counts, that a run stopped by the event reports interrupted and not a measured count, and that both write paths accept the event. 17 tests pass. The renamed-operation assertion is the Phase 6 part. |
| 5 | Run the validation sequence (`rules/toolchain.md`) | In Progress | — | — | Phase 4 part: ruff, ruff format, mypy, bandit (0 Medium/High), module-size gate and radon pass on this file; tools/check_chunks_fts_invariant.py reports no violation; the targeted tests pass (tests/rag/test_fts_sync.py 8, tests/agent/services/test_rag_maintenance_persistence.py 17). The rename gates are the Phase 6 part. |

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
- **Requirement ID**: REQ-002 (cancellation), REQ-004 (verified result before the success line), REQ-007 (name matching behavior)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `scripts/agent/services/rag_maintenance_service.py`, `tests/agent/services/test_rag_maintenance_persistence.py`