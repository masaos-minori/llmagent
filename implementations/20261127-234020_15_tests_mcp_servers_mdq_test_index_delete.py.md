# Implementation Procedure — tests/mcp_servers/mdq/test_index_delete.py

## Goal

Move the fixture inserts onto the new canonical shape so the delete tests insert the columns the
canonical DDL defines (REQ-001, REQ-002, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-002. Acceptance criterion: AC-4.

## Assumptions
- Lightweight fill: the change is confined to the fixture insert statements, with no
  public-contract, persistence, or security impact.
- The column names come from seq 01 in `scripts/mcp_servers/mdq/db_schema.py`.
- Cross-plan overlap: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md` and
  `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md` also target this file. Compatible
  ordering overlap — this plan owns the fixture shape, 005 adds the delete-path atomicity cases,
  and 010 adds only the characterization marker; this plan executes first per the dependency bullets.

## Design decisions
- The fixture helper inserts keep their placeholder values and gain the new columns with values
  that satisfy `NOT NULL`, so the delete assertions are unchanged.

## Alternatives considered
- N/A: fixture alignment only.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_index_delete.py`

### Procedure
- Extend the `documents` insert at line 42 with `path_mtime_fingerprint` (new) and
  `source_content_hash` (new).
- Extend the `chunks` insert at line 52 with `section_content_hash` (new), `is_truncated` (new),
  and `original_char_count` (new).
- Keep the FTS assertion at line 109 unchanged: `chunks_fts` keeps `content_hash`.

### Method
- The insert helpers are the only place the fixture shape is written, so one change per helper
  covers every test in the file.

### Details
- The placeholder hash values stay single-character strings; the new columns are hashes and counts,
  so the added values are placeholder strings and 0.

## Compatibility considerations
- N/A: test fixture only.

## Security considerations
- N/A: test fixture only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_index_delete.py`

## Completion criteria
- The fixture inserts match the canonical shape with the new columns (AC-4).

## Out of Scope
- The canonical DDL itself (seq 01); delete-path transaction atomicity (mdqmcp005).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002 (fixture inserts must move with the canonical shape)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `tests/mcp_servers/mdq/test_index_delete.py`
