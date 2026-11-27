# Implementation Procedure — scripts/mcp_servers/mdq/db_schema.py

## Goal

Make the canonical `mdq` DDL state what was actually indexed: `documents` gains a true
source-content hash and a separately named path/mtime fingerprint, and `chunks` gains the
pre-truncation section hash, the truncation flag, and the original character count
(REQ-001, REQ-002).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001 (documents columns), REQ-002 (chunks columns). Acceptance criteria:
AC-1, AC-2, AC-4.

## Assumptions
- Full form: this row changes the persisted schema, so the persistence contract changes.
- `mdq.sqlite` is a derived store and recreation without data carry-over is acceptable
  (ADR-008 Decision Detail 22), so the rename needs no compatibility shim or migration path.
- `scripts/shared/schema_fingerprint.py` reads the DDL constants, so the fingerprint inputs
  change with them; that file is a reference and is not modified.
- `tests/mcp_servers/mdq/test_db_schema.py` is this row's companion and asserts the shape.

## Design decisions
- `documents.content_hash` is renamed to `path_mtime_fingerprint` (new) and
  `source_content_hash` (new) is added, so no column named `content_hash` holds a non-content
  hash (REQ-001).
- `chunks` keeps `content_hash` as the stored-content hash and gains `section_content_hash` (new),
  `is_truncated` (new), and `original_char_count` (new); `char_count` stays the stored count.
- New columns follow the existing DDL style: `TEXT NOT NULL` for hashes,
  `INTEGER NOT NULL DEFAULT 0` for `is_truncated` (new) and `original_char_count` (new).

## Alternatives considered
- Keep `content_hash` as the content hash and add a separate fingerprint column: rejected by
  the Plan's column-naming decision, because recreation is forced anyway and the misleading
  name would remain.

## Implementation
### Target file
`scripts/mcp_servers/mdq/db_schema.py`

### Procedure
- Edit `_DOCUMENTS_DDL` (line 26): rename `content_hash` to `path_mtime_fingerprint` (new) and
  add `source_content_hash` (new).
- Edit `_CHUNKS_DDL` (line 37): add `section_content_hash` (new), `is_truncated` (new), and
  `original_char_count` (new).
- Leave `_CHUNKS_FTS_DDL` (line 58) unchanged: the FTS5 identity is mdqmcp006's scope.

### Method
- The DDL constants are the single source of the canonical shape: they are the entries of the
  fingerprint tuple at lines 104-106, so `create_production_tables()` (line 112) validates the
  new shape with no separate change.

### Details
- `documents` column order keeps `doc_id`, `source_path`, `mtime_ns`, `size_bytes`, then the two
  hash columns, then `indexed_at`, so the existing read-path `SELECT` shapes keep working.

### Companion test files
- `tests/mcp_servers/mdq/test_db_schema.py`
  - Procedure: move the canonical-shape assertions and the fingerprint-mismatch case onto the new
    columns; `test_drifted_documents_table_is_refused` (line 124) drops `source_content_hash` (new)
    instead of `content_hash` to prove the refusal, and the table-name assertions at lines
    41 and 82 stay unchanged.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_db_schema.py` — the new shape is
    accepted and a drifted shape is refused with the archive-and-recreate message.

## Compatibility considerations
- The rename breaks any reader that selects `documents.content_hash`; the Plan's consumer scan
  found only the mdq writer, the health and outline read paths, and the fixture-embedding test
  files, all of which are rows of this Plan.
- `tests/mcp_servers/mdq/test_mdq_service.py` asserts `content_hash` against the truncated
  content; `chunks` keeps that column, so it is unaffected.

## Security considerations
- N/A: schema shape only; no path or permission handling changes.

## Rollback considerations
- Reverting the DDL requires recreating `mdq.sqlite` again: a database built with the new shape
  is refused by the fingerprint gate, so rollback is archive-and-recreate per
  `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md` section 8e.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_db_schema.py`
- Scratch-database recreation run per `rules/persisted-schema-change.md` (never against a
  database under `/opt/llm/`).
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The canonical DDL contains the five new columns and no `documents` column named
  `content_hash`.
- The fingerprint gate accepts the new shape and refuses a drifted one (AC-4).

## Out of Scope
- The production writer (`scripts/mcp_servers/mdq/index_write.py`, seq 02); FTS5 DDL identity
  and readiness (mdqmcp006); transaction atomicity (mdqmcp005).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_db_schema.py` |
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
- **Requirement ID**: REQ-001 (true content fingerprint), REQ-002 (per-chunk truncation metadata)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `scripts/mcp_servers/mdq/db_schema.py`, `tests/mcp_servers/mdq/test_db_schema.py`
