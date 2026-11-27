# Implementation Procedure — scripts/mcp_servers/mdq/indexer.py

## Goal

Refresh decides skip or re-index from current mtime, size, and source hash, not from the stored
mtime alone (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirement: REQ-003 (three-factor refresh decision). Acceptance criterion: AC-1.

## Assumptions
- Full form: this row changes the refresh decision, which is observable through the tool result.
- The per-file DTO, the status vocabulary, and the post-commit rule are defined by the archived
  mdqmcp003 plan; this row changes only the skip decision and does not redefine them.
- The source hash is produced by the writer path described in seq 02.
- `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` is this row's companion.

## Design decisions
- The `index_state` key stays `mtime:{path}` (line 316); the decision at line 318 adds the size and
  the stored source hash to the comparison, so a same-mtime content change re-indexes.
- The comparison reads the stored `documents` row for the path, so no new table or key is added.

## Alternatives considered
- Store a combined fingerprint in `index_state` instead of comparing the stored row: rejected,
  because the stored row already holds the three values and a second copy would drift.

## Implementation
### Target file
`scripts/mcp_servers/mdq/indexer.py`

### Procedure
- At line 318, extend the skip test from the stored mtime alone to current mtime, size, and the
  stored `source_content_hash` (new).
- Keep the post-commit update of `index_state` and `current_state` unchanged.

### Method
- The stored row is fetched once per file before the decision; when the row is absent the file is
  re-indexed, which also closes the missing-state gap for a file that was deleted and recreated.

### Details
- A timestamp rollback is detected because the current mtime no longer equals the stored value; a
  same-mtime content change is detected through the source hash.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
  - Procedure: move the mtime-only skip characterization onto the three-factor decision and add the
    same-mtime content change and rollback cases; `test_failed_reindex_does_not_record_the_new_mtime`
    (line 357) stays as the post-commit characterization.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` — a
    same-mtime content change is re-indexed.

## Compatibility considerations
- `index_scan.py` is a reference file only: discovery stays free of hashing and database access, so
  the scan path is unaffected.

## Security considerations
- N/A: the path is already allowlist-checked before the refresh decision.

## Rollback considerations
- N/A: revert the commit; the decision depends on the seq 01 columns.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- A same-mtime content change and a timestamp rollback both cause a re-index (AC-1), and the skip
  decision is no longer mtime-only.

## Out of Scope
- The writer hash computation (seq 02); transaction atomicity (mdqmcp005); the per-file DTO
  statuses defined by the archived mdqmcp003 plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/22_mcp/mcp_04_04_mdq.md` (seq 18) |

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
- **Requirement ID**: REQ-003 (refresh decides from mtime, size, and source hash)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `scripts/mcp_servers/mdq/indexer.py`, `tests/mcp_servers/mdq/test_mdq_incremental_refresh.py`
