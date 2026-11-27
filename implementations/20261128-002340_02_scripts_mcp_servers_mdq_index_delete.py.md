# Implementation Procedure — scripts/mcp_servers/mdq/index_delete.py

## Goal

Delete `index_state` by the exact canonical key and stop committing inside the helper, so a file
operation commits once under its caller (REQ-001, REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-003. Acceptance criterion: AC-2.

## Assumptions
- Full form: this row changes key semantics for existing `index_state` rows and the helper's
  transaction behavior.
- The canonical key string is `mtime:{path}` as produced by `scripts/mcp_servers/mdq/indexer.py`
  (line 316); the helper uses the same string the writer stores, so no key-format change is
  introduced (the Plan's Assumptions).
- The FTS5 effect stays inside the caller's transaction: the `chunks_ad` trigger fires on the
  `chunks` statements (line 27 comment), so no separate FTS handling is added.
- `tests/mcp_servers/mdq/test_index_delete.py` is this row's companion.

## Design decisions
- `key = ?` replaces the prefix `LIKE`: a prefix match is not the intended identity, and escaping
  `%` and `_` in the pattern would keep the over-match risk for shared filenames.
- The helper executes statements only; the caller owns the transaction and the commit.

## Alternatives considered
- Escape `%` and `_` in the `LIKE` pattern: rejected by the Plan, because the over-match on a
  shared prefix remains.

## Implementation
### Target file
`scripts/mcp_servers/mdq/index_delete.py`

### Procedure
- Replace the `LIKE` delete at line 31 with `DELETE FROM index_state WHERE key = ?` and bind the
  canonical `mtime:{path}` string.
- Remove `conn.commit()` (line 34).

### Method
- The key is built from the same path string the writer stores, so existing rows keep the same form
  and no row rewrite is needed.

### Details
- The `chunks` and `documents` deletes stay in the same statement sequence, so the trigger effect
  remains inside the caller's transaction.

### Companion test files
- `tests/mcp_servers/mdq/test_index_delete.py`
  - Procedure: flip `TestIndexStateWildcardMatchIsCharacterizedAsIs` (lines 181-206) to the exact
    key — deleting `a.md` leaves `a.md.bak` state — and move `TestCommitsTheTransaction` (line 209)
    from pinning the helper commit to pinning caller-owned behavior; add the `%` and `_` filename
    cases against the exact key.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_index_delete.py` — the shared-prefix row
    survives the delete of the shorter path (AC-2).

## Compatibility considerations
- Key semantics change for existing `index_state` rows written by the prefix path; the Plan's Risk
  records that the same writer line produces the key, so existing rows keep the form, with the
  derived-store recreation path as the fallback.

## Security considerations
- N/A: key matching only; the path is already allowlist-checked by the caller.

## Rollback considerations
- N/A: revert the commit; the helper only works with a caller that commits, so rollback is together
  with this Plan's row 3.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_index_state_consistency.py tests/mcp_servers/mdq/test_index_delete.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- Deleting `a.md` cannot delete `a.md.bak` state (AC-2), and the helper contains no commit.

## Out of Scope
- Directory-deletion transaction shape (the Plan's UNK-01, kept as structured partial success);
  the caller's transaction ownership (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_index_delete.py` |
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
- **Requirement ID**: REQ-001 (no commit inside the helper), REQ-003 (exact canonical key)
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `scripts/mcp_servers/mdq/index_delete.py`, `tests/mcp_servers/mdq/test_index_delete.py`
