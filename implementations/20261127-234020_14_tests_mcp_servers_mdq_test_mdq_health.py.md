# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_health.py

## Goal

Move the fixture DDLs onto the new canonical shape so the health tests build the shape the
canonical DDL defines (REQ-001, REQ-002, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-002. Acceptance criterion: AC-4.

## Assumptions
- Lightweight fill: the change is confined to the fixture DDL strings, with no public-contract,
  persistence, or security impact.
- The column names come from seq 01 in `scripts/mcp_servers/mdq/db_schema.py`.
- Cross-plan overlap: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md` and
  `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md` also target this file. Compatible
  ordering overlap — this plan owns the fixture shape, 006 adds the FTS5 identity assertions, and
  010 adds only the characterization marker; this plan executes first per the dependency bullets.

## Design decisions
- Only the column lists change; the fixture tables stay minimal so the negative cases (missing
  table, probe column) keep testing the same conditions.

## Alternatives considered
- N/A: fixture alignment only.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_health.py`

### Procedure
- Add the new columns to the `documents` fixture DDL at line 30 and the `chunks` fixture DDL at
  line 52.
- The `chunks_fts` fixture DDL at line 66 keeps `content_hash` and gains no new column: the FTS5
  identity is mdqmcp006's scope.

### Method
- The fixture DDL strings are the shape the health check reads, so they must match the canonical
  constants from seq 01 exactly.

### Details
- No assertion changes: this file pins table and column presence only.

## Compatibility considerations
- N/A: test fixture only.

## Security considerations
- N/A: test fixture only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_health.py`

## Completion criteria
- The fixture shape matches the canonical DDL with the new columns (AC-4).

## Out of Scope
- The canonical DDL itself (seq 01); the FTS5 definition comparison (mdqmcp006).

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
- **Requirement ID**: REQ-001, REQ-002 (fixture DDL must move with the canonical shape)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_health.py`
