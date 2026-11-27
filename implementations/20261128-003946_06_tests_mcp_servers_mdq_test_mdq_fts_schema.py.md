# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_fts_schema.py

## Goal

Pin that readiness refuses a plain table named `chunks_fts`, tokenizer, column, and option drift, and
no-op trigger bodies (REQ-001, AC-1, AC-2).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001 (definition comparison, not names). Acceptance criteria: AC-1, AC-2.

## Assumptions
- Full form: this is a new test file that defines the drift-case design, so it is not a companion of
  row 4 even though row 4 names it in `Related Tests`.
- The behavior pinned here is defined by row 4 (`scripts/mcp_servers/mdq/health_check.py`) and row 2;
  this document writes tests only and does not change production code.
- Phase 1 pins the current name-only comparison in `tests/shared/test_schema_fingerprint.py` and
  `tests/mcp_servers/mdq/test_mdq_health_endpoint.py`; this file is the Phase 2 refusal cases.
- The canonical DDL text is read from `scripts/shared/mdq_schema.py` (new) (row 19), so the fixtures
  apply the same text the identity is computed from.

## Design decisions
- Each drift case is one fixture that applies the canonical statements to an in-memory database and
  then replaces one statement with the drifted variant, so the cases are independent and no file is
  written to disk.
- Readiness is asserted through `check_health` rather than through an internal helper, so the pin
  covers the published contract.

## Alternatives considered
- Assert the comparison helper directly: rejected, because AC-1 states that readiness cannot pass,
  which is the endpoint contract.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_fts_schema.py` (new)

### Procedure
- Build a fixture that applies the canonical mdq statements to an in-memory connection.
- Add cases: a plain table named `chunks_fts` with a `chunks_fts` column; tokenizer drift; column
  count and order drift; option drift through an external-content declaration; a no-op trigger body on
  `chunks`.
- Assert each case refuses readiness and that the refusal names the differing object.

### Method
- The drifted statements are written as constants in the file so a failure shows which statement
  drifted; the canonical statements come from the shared module, not from a copy.

### Details
- The no-op trigger case keeps the trigger names `chunks_ai`, `chunks_ad`, and `chunks_au` and changes
  only the body, which is the case the name-only comparison cannot detect.

## Compatibility considerations
- N/A: new test file; no existing assertion changes.

## Security considerations
- N/A: in-memory fixtures only; no path or permission handling.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_fts_schema.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- Every drift case refuses readiness and the plain-table case is refused even though the name matches
  (AC-1, AC-2).

## Out of Scope
- The functional synchronization probes (row 7); the comparison implementation itself (row 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 2 |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document is the test row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: the readiness guarantee is documented by row 15 |

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
- **Requirement ID**: REQ-001 (readiness compares the stored FTS5 definition and trigger SQL)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_fts_schema.py`
