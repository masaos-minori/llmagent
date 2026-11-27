# Implementation Procedure — scripts/mcp_servers/mdq/index_write.py

## Goal

Make the writer a statement executor on a connection it does not own, so one file operation
commits once under its caller (REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-002, REQ-006. Acceptance criterion: AC-1.

## Assumptions
- Full form: this row changes the writer's transaction contract, which every call site depends on.
- The caller that owns the transaction is `scripts/mcp_servers/mdq/indexer.py` (this Plan's row 3);
  this document does not define its commit point.
- The writer already propagates `sqlite3.Error`; the failure-swallowing is the caller's
  (`indexer.py` lines 106-108), so no error handling is added here.
- The insert column list is the shape plan 004 defines: `source_content_hash` (new), the renamed
  fingerprint, and the chunk truncation fields. That plan executes first per the dependency bullet, so
  this row changes only transaction ownership, not the columns.
- `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` is this row's companion test but keeps
  its own document because two rows name it in `Related Tests`.

## Design decisions
- The writer executes statements and returns; it never begins or commits a transaction. The single
  commit is the caller's, after the postcondition check.
- Failure stays an exception: the caller must be able to distinguish a failed operation from a
  successful one, so the writer does not log-and-return.

## Alternatives considered
- Keep the writer's own transaction and make the `index_state` write part of it: rejected by the
  Plan, because the state write and the row writes sit on two connections, so a failure between
  them still leaves partial state.

## Implementation
### Target file
`scripts/mcp_servers/mdq/index_write.py`

### Procedure
- Remove `conn.execute("BEGIN IMMEDIATE")` (line 71) and `conn.execute("COMMIT")` (line 123).
- Keep the statement sequence unchanged: delete the old chunks, upsert the document, insert the
  chunks.

### Method
- The caller's transaction is already open when the writer runs, so the statements join it without
  an explicit begin; the caller commits after the postcondition check.

### Details
- The docstring must state that the caller owns the transaction and the commit, since the current
  docstring says the writer runs a `BEGIN IMMEDIATE` transaction.

## Compatibility considerations
- Every call site is `scripts/mcp_servers/mdq/indexer.py` (line 105), a row of this Plan; no other
  caller exists.
- `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` pins the transaction shape through a
  recording connection; that pin moves with the change (this Plan's row 7).

## Security considerations
- N/A: transaction ownership only; no path or permission handling changes.

## Rollback considerations
- N/A: revert the commit; a writer without its own transaction only works with the caller that
  commits, so rollback is together with this Plan's row 3.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The writer contains no `BEGIN IMMEDIATE` or `COMMIT`, and a failed operation leaves no partial
  state (AC-1).

## Out of Scope
- The caller's transaction ownership and postcondition check (row 3); the persisted columns (plan
  004); the retry classification (rows 4, 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_mdq_transaction_atomicity.py` has its own document (row 9) |
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
- **Requirement ID**: REQ-001 (caller-owned transaction), REQ-002 (one transaction per file), REQ-006 (postconditions before success)
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `scripts/mcp_servers/mdq/index_write.py`
