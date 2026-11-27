# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_schema_migration.py

## Goal

Move the fixture DDLs onto the new canonical shape so the schema-recreation and production-writer
contract tests assert the new columns (REQ-001, REQ-002, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-002. Acceptance criterion: AC-4.

## Assumptions
- Lightweight fill: the change is confined to the fixture functions and the fixture inserts, with
  no public-contract, persistence, or security impact.
- The column names come from seq 01 in `scripts/mcp_servers/mdq/db_schema.py`.
- Cross-plan overlap: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md` also targets this
  file. Compatible ordering overlap — that plan adds only the `pytestmark` characterization marker
  here, and this plan owns the fixture shape; this plan executes first.

## Design decisions
- The fixture DDL is written from the canonical constants rather than hand-copied, so the fixture
  cannot drift from the canonical shape.

## Alternatives considered
- N/A: fixture alignment only.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_schema_migration.py`

### Procedure
- Add the new columns to the `documents` fixture DDL at line 27 and the `chunks` fixture DDL at
  line 46.
- Extend the fixture inserts at lines 107 and 113 with the new columns.

### Method
- The writer contract test keeps computing the stored hash from the content it inserts and adds the
  source hash and section hash values, so the two hash columns are asserted as distinct values.

### Details
- The FTS trigger fixtures are unchanged: the FTS5 identity is mdqmcp006's scope.

## Compatibility considerations
- N/A: test fixture only.

## Security considerations
- N/A: test fixture only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_schema_migration.py`

## Completion criteria
- The fixture shape matches the canonical DDL, and the writer contract test records a source hash
  from bytes plus a distinct section hash (AC-4).

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
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_schema_migration.py`
