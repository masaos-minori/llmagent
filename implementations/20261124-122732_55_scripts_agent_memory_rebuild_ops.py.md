## Goal

Run the FTS and vector index rebuilds inside one transaction with a cancellation boundary, so an interrupted rebuild does not leave a partially populated index (REQ-002, REQ-006; AC-2, AC-6).

## Scope
**Release unit**: R5-memory-layering (Phase 5)

- In scope: `rebuild_fts`, `rebuild_vec`, the `reindex` dispatch.

## Assumptions

- The delete-then-row-by-row insert shape stays; what changes is that the whole sequence runs inside one transaction boundary owned by the `MemoryStore` accessor (row 12).
- The vector table here is the Memory vector index (`memories_vec`), not the RAG `chunks_vec`; the RAG side is row 22.

## Design decisions

- The transaction boundary is owned by the store accessor, not by this module, so the store remains the single owner of the write path (REQ-005); this module supplies the statements inside that boundary.
- An interrupted run rolls back, so the reported count is zero rather than a partial count; that is what makes the outcome verifiable.

## Alternatives considered

- Committing per row and reporting the number of rows inserted — rejected: the requirement is that an interruption leaves a consistent index, which per-row commits cannot provide.

## Implementation
### Target file
`scripts/agent/memory/rebuild_ops.py`

### Procedure
1. Run `rebuild_fts` (`rebuild_ops.py:8-20`) and `rebuild_vec` (`:23-35`) inside the transaction boundary the store accessor opens.
2. Take the job's cancellation event and pass it to `db.interrupt_when` inside that boundary.
3. Report the verified row count measured after the commit (row 12's result shape), not the number of inserts attempted.

### Method

- `reindex` dispatch (`:38-43`) keeps its shape; it calls the store accessor rather than opening its own connection.

### Details

- The `DELETE` and the insert loop must be in the same transaction; a `DELETE` outside it would leave an empty index after an interrupted run.

### Companion test files

- `tests/agent/commands/test_memory_rebuild_guard.py` (row 56 is this row's companion test, covered by this document)
  - Procedure: the guard case asserts the transaction boundary and the verified count returned by the accessor; the `--confirm` replacement is described in row 5 and is not repeated here.
  - Validation: `uv run pytest tests/agent/commands/test_memory_rebuild_guard.py -q` (REQ-002, REQ-006; AC-2, AC-6).

## Compatibility considerations

- `tests/agent/memory/test_memory_vec_session.py` (row 57) asserts the interrupted vector table stays consistent; it runs in the same phase.

## Security considerations

- The rebuild is a write against `session.sqlite`; the run is recorded so the one-writer guard sees it.

## Rollback considerations

- N/A: revert the Phase 5 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `scripts/agent/memory/rebuild_ops.py` | Unit | `uv run pytest tests/agent/memory/test_memory_store.py tests/agent/memory/test_memory_vec_session.py tests/agent/commands/test_memory_rebuild_guard.py -q` | One transaction, cancellation honored, verified row count |
| Same file | Quality gates | `uv run ruff check scripts/agent/memory/rebuild_ops.py`, `uv run mypy scripts/agent/memory/rebuild_ops.py` | No finding |

## Completion criteria

- An interrupted rebuild leaves the index as it was before the run, and the reported count is the committed count.

## Out of Scope

- The store accessors, the RAG vector path (row 22), the command handler.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the rebuilds inside one transaction with the cancellation event | Pending | — | — | Phase 5 |
| 2 | Report the verified row count | Pending | — | — | Phase 5 |
| 3 | Update the companion test per Validation plan | Pending | — | — | Row 56 is covered by this document; `tests/agent/memory/test_memory_store.py` (row 44) keeps its own document |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `scripts/agent/memory/rebuild_ops.py`, `tests/agent/commands/test_memory_rebuild_guard.py`
