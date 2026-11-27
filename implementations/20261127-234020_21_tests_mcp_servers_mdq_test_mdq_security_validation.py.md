# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_security_validation.py

## Goal

Move the fixture DDL onto the new canonical shape so the minimal documents shape this file builds
still satisfies the redesigned stale SQL after the documents column rename (REQ-001, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirement: REQ-001. Acceptance criterion: AC-4.

## Assumptions
- Lightweight fill: the change is confined to the fixture DDL strings, with no public-contract,
  persistence, or security impact.
- The column names come from seq 01 in `scripts/mcp_servers/mdq/db_schema.py`; the redesigned stale
  SQL comes from seq 03.
- Cross-plan overlap: `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md` also targets this
  file. Compatible ordering overlap — this plan owns the fixture shape and 010 adds only the
  characterization marker; this plan executes first.

## Design decisions
- The fixture stays the smallest shape `check_health()` accepts, so only the column names change;
  the posture assertions are unchanged.

## Alternatives considered
- N/A: fixture alignment only.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_security_validation.py`

### Procedure
- Rename `content_hash` to `path_mtime_fingerprint` (new) in the `documents` fixture DDL at lines
  66-67 and add `source_content_hash` (new).
- Add `section_content_hash` (new), `is_truncated` (new), and `original_char_count` (new) to the
  `chunks` fixture DDL at line 71.

### Method
- The fixture is the shape the health path reads through `check_health()` at lines 381, 394, and
  406, so it must match the canonical shape the redesigned stale SQL queries.

### Details
- No assertion changes: this file pins the posture, not the hash semantics.

## Compatibility considerations
- N/A: test fixture only.

## Security considerations
- N/A: test fixture only; the posture assertions are unchanged.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_security_validation.py`

## Completion criteria
- The fixture matches the canonical shape and the health calls through it still return the posture
  (AC-4).

## Out of Scope
- The canonical DDL itself (seq 01); the stale-state definitions (seq 03).

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
- **Requirement ID**: REQ-001 (fixture DDL must move with the canonical shape)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_security_validation.py`
