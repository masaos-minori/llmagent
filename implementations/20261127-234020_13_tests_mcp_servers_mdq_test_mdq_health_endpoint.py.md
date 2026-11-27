# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_health_endpoint.py

## Goal

Move the fixture DDLs onto the new canonical shape and keep the `stale_document_count` key-presence
assertion (REQ-004, AC-4).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001, REQ-002, REQ-004. Acceptance criteria: AC-3, AC-4.

## Assumptions
- Lightweight fill: the change is confined to the fixture builders and the in-test schemas, with no
  public-contract, persistence, or security impact.
- The column names come from seq 01; the per-state counts come from seq 05.
- Cross-plan overlap: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md` and
  `plans/20261127-203046_mdqmcp010_mdq-release-readiness.md` also target this file. Compatible
  ordering overlap — this plan owns the fixture shape, 006 adds the readiness-condition assertions,
  and 010 adds only the characterization marker; this plan executes first per the dependency bullets.

## Design decisions
- The fixture builders keep their "smallest schema" shape and gain only the new columns, so the
  negative fixtures (no documents, no chunks, no FTS, corrupt FTS) keep testing the same conditions.

## Alternatives considered
- N/A: fixture alignment only.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_health_endpoint.py`

### Procedure
- Add the new columns to each fixture DDL: the documents blocks at lines 39, 158, 195, 235, 432, and
  494, and the chunks blocks at lines 61, 134, 171, and 520.
- Keep the key-presence assertion at line 340 unchanged.

### Method
- The negative fixtures that omit the `documents` table keep their expectation that the stale count
  returns `None`, so only the column list changes.

### Details
- No assertion is added here for the per-state counts; that is the companion of seq 05.

## Compatibility considerations
- N/A: test fixture only.

## Security considerations
- N/A: test fixture only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_health_endpoint.py`

## Completion criteria
- Every fixture matches the new canonical shape, and `stale_document_count` remains a published key
  (AC-3, AC-4).

## Out of Scope
- The per-state count assertions (seq 05's companion); the readiness-condition mapping (mdqmcp006).

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
- **Requirement ID**: REQ-004 (health state reporting), REQ-001, REQ-002 (fixture shape)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`
