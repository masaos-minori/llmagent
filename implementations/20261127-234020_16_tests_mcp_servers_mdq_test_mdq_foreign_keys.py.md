# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_foreign_keys.py

## Goal

Move the fixture insert onto the new canonical shape so the foreign-key tests insert the columns the
canonical DDL defines (REQ-001, REQ-002, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-002. Acceptance criterion: AC-4.

## Assumptions
- Lightweight fill: the change is confined to one insert statement, with no public-contract,
  persistence, or security impact.
- The file builds no fixture DDL of its own: it uses the service connection, so the schema comes
  from the canonical constants of seq 01.
- The column names come from seq 01 in `scripts/mcp_servers/mdq/db_schema.py`.
- Cross-plan overlap: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md` also targets this
  file. Compatible ordering overlap — this plan owns the insert shape and 010 adds only the
  characterization marker; this plan executes first.

## Design decisions
- The insert gains the new columns with placeholder values; the `IntegrityError` expectation stays,
  because the refusal is caused by the missing `doc_id`, not by the column list.

## Alternatives considered
- N/A: fixture alignment only.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_foreign_keys.py`

### Procedure
- Extend the `chunks` insert column list at line 107 with `section_content_hash` (new),
  `is_truncated` (new), and `original_char_count` (new), and add the matching values.

### Method
- The insert is the only place this file writes the fixture shape.

### Details
- The added values are placeholder strings and 0, so the row shape is the only change.

## Compatibility considerations
- N/A: test fixture only.

## Security considerations
- N/A: test fixture only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_foreign_keys.py`

## Completion criteria
- The insert matches the canonical shape with the new columns and the orphan-row refusal still
  holds (AC-4).

## Out of Scope
- The canonical DDL itself (seq 01); the inconsistent-state classification for orphan chunks
  (seq 03 and seq 04).

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
- **Requirement ID**: REQ-001, REQ-002 (fixture insert must move with the canonical shape)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_foreign_keys.py`
