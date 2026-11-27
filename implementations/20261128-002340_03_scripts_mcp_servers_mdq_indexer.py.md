# Implementation Procedure — scripts/mcp_servers/mdq/indexer.py

## Goal

Make the mdq indexer entry points the single owner of the connection and transaction for one
file operation, write `index_state` inside that transaction after the postcondition check, and
record state during forced refresh (REQ-001, REQ-002, REQ-004, REQ-006).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-002, REQ-004, REQ-006. Acceptance criteria: AC-1, AC-2.

## Assumptions
- Full form: this row moves transaction ownership across the writer and delete helpers and adds a
  postcondition check that every write path depends on.
- Plan default for UNK-01: one transaction covers a single file only; directory deletion keeps the
  current structured partial success (`_delete_stale_entries()`, line 232). Confirm with the owner
  before widening it.
- Plan default for UNK-02: the existing indexer entry points own the connection; no new repository
  module is created.
- The canonical key string is the one `scripts/mcp_servers/mdq/indexer.py` already builds (line 316),
  so the state write and the exact-key delete use the same value.
- The `chunks_ad` trigger fires inside the same transaction as the `chunks` statements, so the FTS5
  effect needs no separate handling.
- Overlap: `scripts/mcp_servers/mdq/indexer.py` is also targeted by plan 007 (`plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`); compatible ordering overlap, this Plan executes first.
- `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` is this row's companion.

## Design decisions
- One owner per file operation: the entry point opens the connection, begins the transaction, runs
  the statement executors, checks postconditions, then commits.
- The postcondition check runs before the commit, so a failed operation never records state and
  never commits partial rows.
- Forced refresh records `index_state` for each file it indexes, using the same key and value form as
  incremental mode, so a forced run followed by an incremental run does not re-index.

## Alternatives considered
- Keep the writer's own transaction and make the state write part of it: rejected by the Plan,
  because the state write and the row writes currently sit on two connections.

## Implementation
### Target file
`scripts/mcp_servers/mdq/indexer.py`

### Procedure
- In `_index_single_file()` (lines 75-110): open the connection, begin the transaction, call
  `write_document_chunks()` as a statement executor, write `index_state`, check postconditions, then
  commit; keep `_rollback_quietly()` on the failure branch.
- Move the state insert and commit that are currently separate from the write (lines 321-325) into the
  same transaction.
- In `_reindex_forced()` (lines 274-290): record `index_state` for each indexable file it processes.

### Method
- Postconditions are the row counts for the document, its chunks, the FTS5 rows, and the state row;
  the check is a small helper that keeps radon grade A.
- A failed postcondition check rolls back and reports failure to the caller, so the per-file outcome
  stays distinguishable (the boundary mdqmcp003's per-file DTO consumes).

### Details
- The connection is opened once per file operation and closed in the existing `finally` block
  (line 109); no connection is shared across files.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
  - Procedure: move the transaction-shape pin in `test_successful_write_brackets_its_row_statements`
    (lines 667-685) from the helper to the caller, and add the forced-then-incremental state case for
    REQ-004; keep the `_rollback_quietly` tests (lines 639-657).
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` — forced refresh
    leaves correct incremental state (AC-2).

## Compatibility considerations
- Call sites of `write_document_chunks()` are only this file (line 105), so the signature change is
  internal to the mdq module.
- `_index_lock` serialization behavior is unchanged; the serialization test (this Plan's row 8) runs
  against the single caller-owned transaction.

## Security considerations
- N/A: transaction ownership only; path allowlist checks stay in the existing entry points.

## Rollback considerations
- N/A: revert the commit. This row and rows 1 and 2 must roll back together, since the statement
  executors only work under a caller that commits.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_incremental_refresh.py tests/mcp_servers/mdq/test_mdq_index_state_consistency.py tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- One file operation commits once, `index_state` is written only after the postcondition check, and a
  forced refresh records state for the files it indexes (AC-1, AC-2).

## Out of Scope
- Directory-level transactions (UNK-01); the writer and delete helper bodies (rows 1, 2); the retry
  classification (rows 4, 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/22_mcp/mcp_04_04_mdq.md` (row 13) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-004, REQ-006
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `scripts/mcp_servers/mdq/indexer.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
