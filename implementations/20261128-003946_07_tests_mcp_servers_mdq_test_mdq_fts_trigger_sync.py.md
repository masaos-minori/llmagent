# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py

## Goal

Prove the trigger synchronization functionally with insert, update, and delete probes against a
scratch apply of the canonical DDL (REQ-002, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-002 (functional probes prove the trigger logic). Acceptance criterion: AC-2.

## Assumptions
- Full form: this is a new test file that defines the probe design, so it is not a companion.
- The probes run against an in-memory apply of the canonical statements from
  `scripts/shared/mdq_schema.py` (new) (row 19); the live store is never written, which is the rule
  row 4 follows as well.
- The existing FTS trigger-sync tests in `tests/rag/test_fts_sync.py` use the rag schema and cannot be
  reused, so this file builds the mdq shape from the canonical text.

## Design decisions
- One probe per trigger: insert, update, and delete, each asserting the FTS row for the same rowid
  follows the `chunks` row, so a no-op trigger body fails.
- The probe asserts both the row count and a match query result, because a trigger that inserts the
  wrong column values would pass a count-only assertion.

## Alternatives considered
- Reuse the rag trigger tests with a different schema constant: rejected, because the mdq trigger
  bodies and column list differ, and copying the schema would duplicate the canonical source.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py` (new)

### Procedure
- Apply the canonical mdq statements to an in-memory connection through `apply_ddl_in_memory`.
- Add three probes: insert a `chunks` row and assert the FTS row appears; update the row and assert the
  FTS row is replaced with the new values; delete the row and assert the FTS row is gone.
- Add the negative case: the same probes against a schema whose trigger bodies are no-op statements
  must fail, which is what readiness refuses.

### Method
- Each probe uses its own connection so the probes do not share trigger state; the connection is closed
  in the fixture.

### Details
- The probes read `rowid` from the `chunks` row, which is the implicit rowid of the `TEXT` primary key
  table the trigger bodies use.

## Compatibility considerations
- N/A: new test file; no existing assertion changes.

## Security considerations
- N/A: in-memory fixtures only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The three probes pass against the canonical statements and fail against no-op triggers (AC-2); no
  probe writes to a database under `/opt/llm/`.

## Out of Scope
- The readiness wiring of the probe (row 4); the definition comparison (row 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 2 |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document is the test row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: the guarantee is documented by row 15 |

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
- **Requirement ID**: REQ-002 (functional insert, update, and delete synchronization probes)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_fts_trigger_sync.py`
