# Implementation Procedure — tests/mcp_servers/mdq/test_db_schema.py

## Goal

Extend the canonical-shape and mismatch-refusal pins so they cover the FTS5 definition comparison
(REQ-001, REQ-003, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001 (definition comparison), REQ-003 (identity from the single canonical DDL
source). Acceptance criterion: AC-2.

## Assumptions
- Full form: this row pins the refusal outcome for a shape that passes today, so the assertion design is
  the deliverable.
- The behavior is defined by rows 1 and 2; this document changes only the test file.
- Plan 004's row for this file has no generated procedure document, and its column rename is not
  implemented at current HEAD: `documents` still declares `content_hash`
  (`scripts/mcp_servers/mdq/db_schema.py:32`), and the drift case in
  `tests/mcp_servers/mdq/test_db_schema.py` (line 124) still drops `content_hash`. So this row adds the
  FTS5 definition case on top of the test as it stands, not after a rename.
- The refusal message for an FTS5 entry is the one row 2 defines: `mdq.sqlite.chunks_fts: definition
  differ from the canonical schema`.
- This file is also a target row of the mdqmcp010 plan; the Plan's dependency bullets order this Plan
  before it, so the overlap is compatible.

## Design decisions
- The case is asserted through `create_production_tables()`, the public entry point, so the pin covers
  the startup path an operator runs, not the comparison helper.
- The drifted shape is built by executing a plain-table `CREATE TABLE chunks_fts` on a database created
  from the canonical statements, which is the exact condition AC-1 describes.

## Alternatives considered
- Assert `expected_fingerprint` directly: rejected, because the plan's acceptance criterion is the
  refusal, and the entry point is what produces it.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_db_schema.py`

### Procedure
- Keep the table-name pins at lines 41 and 82 and the drifted-`documents` refusal test at line 124.
- Add the FTS5 definition case: create a database from the canonical statements, replace the FTS5 table
  with a plain table named `chunks_fts`, and assert `create_production_tables()` raises with the
  definition-differ message.
- Add the trigger-drift case: a no-op trigger body on `chunks` is refused with the triggers part of the
  message.

### Method
- Each case builds its own database in `tmp_path` and closes the connection in the existing `finally`
  pattern, so no case shares state with another.

### Details
- The canonical statements come from `scripts/shared/mdq_schema.py` (new) (row 19), so the test does not
  hold a second copy of the DDL text.

## Compatibility considerations
- The existing assertions are unchanged, so the only new behavior is the added cases.

## Security considerations
- N/A: test file only; the refusal message quotes schema structure, never row content.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_db_schema.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- A plain table named `chunks_fts` and a no-op trigger body are refused by the entry point with the
  message naming the differing object (AC-2); the existing pins still pass.

## Out of Scope
- The comparison implementation (row 2); the canonical DDL text (row 19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 5 |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document is the test row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: the comparison is documented by row 17 |

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
- **Requirement ID**: REQ-001 (definition comparison), REQ-003 (canonical identity)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `tests/mcp_servers/mdq/test_db_schema.py`
