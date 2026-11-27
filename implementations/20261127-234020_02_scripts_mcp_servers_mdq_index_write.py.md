# Implementation Procedure — scripts/mcp_servers/mdq/index_write.py

## Goal

Make the writer record what it actually read: the source hash computed from file bytes, the
path/mtime fingerprint stored under its own name, and per chunk the pre-truncation section hash,
the truncation flag, and the original and stored character counts (REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001 (source hash from bytes), REQ-002 (section hash and truncation metadata).
Acceptance criteria: AC-1, AC-2, AC-4.

## Assumptions
- Full form: this row changes what the production write path persists.
- The new column names are defined by seq 01 in `scripts/mcp_servers/mdq/db_schema.py`; this
  document uses them and does not redefine them.
- The size gate is applied before hashing, so the source hash is computed only for files that
  pass it (the Plan's default for UNK-01).
- `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` is this row's companion and is
  created by this pass.

## Design decisions
- `doc_id` stays `sha256(str(path))` (line 65): identity is not part of this change, only the
  hash columns.
- The section hash is computed from the full section text before truncation and the stored hash
  from the stored text, so the two values differ exactly when truncation happened.

## Alternatives considered
- Compute the source hash from the stored (possibly truncated) document text: rejected, because
  REQ-001 requires the hash of the source bytes.

## Implementation
### Target file
`scripts/mcp_servers/mdq/index_write.py`

### Procedure
- At line 69, keep the path-plus-mtime value but store it as `path_mtime_fingerprint` (new), and
  add `source_content_hash` (new) computed from the bytes that were read.
- In the chunk loop, compute `section_content_hash` (new) before the truncation at lines 87-89,
  keep the stored `content_hash` as the hash of the stored text, and set `is_truncated` (new),
  `original_char_count` (new), and `char_count` from the same read.

### Method
- The insert column lists gain the new columns; the values come from the same read, so no second
  file read or second query is added.

### Details
- `is_truncated` is 1 when the stored text is shorter than the original section text;
  `original_char_count` equals `char_count` when nothing was truncated.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` (new)
  - Procedure: real-file tests for the writer — same mtime with different content, mtime
    rollback, deletion, a change after the stored truncation boundary, and the
    section-hash-versus-stored-hash distinction.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` — the
    stored source hash changes with content at the same mtime, and the two chunk hashes are
    distinct values when truncation occurred.

## Compatibility considerations
- The persisted shape changes, so every fixture that inserts into `documents` or `chunks` moves
  with it; those files are rows of this Plan (seq 11, 13, 14, 15, 16, 21).

## Security considerations
- N/A: hashing and character counts only; no path, permission, or redaction behavior changes.

## Rollback considerations
- N/A: revert the commit; the database written by the new writer must be recreated because the
  fingerprint gate refuses the old shape.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- A same-mtime content change and a timestamp rollback produce a different stored source hash
  (AC-1).
- The original section hash and the stored chunk hash are distinct stored values, and the
  truncation flag and both counts are recorded (AC-2).

## Out of Scope
- The refresh skip decision (`scripts/mcp_servers/mdq/indexer.py`, seq 06); transaction
  atomicity (mdqmcp005); FTS5 identity (mdqmcp006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py` (new) |
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
- **Requirement ID**: REQ-001 (source hash from bytes), REQ-002 (section hash and truncation metadata)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `scripts/mcp_servers/mdq/index_write.py`, `tests/mcp_servers/mdq/test_mdq_content_hash_semantics.py`
