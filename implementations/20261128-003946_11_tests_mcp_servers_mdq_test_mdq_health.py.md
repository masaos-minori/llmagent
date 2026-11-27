# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_health.py

## Goal

Move the health fixture from a plain table named `chunks_fts` to the real FTS5 definition so the
fixture satisfies the definition comparison, and pin readiness for the aligned fixture (REQ-001,
AC-1).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-001 (readiness compares the stored FTS5 definition). Acceptance criterion: AC-1.

## Assumptions
- Full form: the fixture shape is the condition the row pins, so the fixture change is the design, not
  a mechanical alignment.
- The behavior is defined by row 4 (`scripts/mcp_servers/mdq/health_check.py`); this document changes
  only the test file.
- The plan 004 procedure pass (`implementations/20261127-234020_14_tests_mcp_servers_mdq_test_mdq_health.py.md`)
  already moves the `documents` and `chunks` fixture DDLs onto the renamed canonical shape, so this row
  changes only the FTS5 table form.
- The FTS5 definition in the fixture is the canonical text from `scripts/shared/mdq_schema.py` (new)
  (row 19), not a copy.
- `docs/22_mcp/mcp_04_04_mdq.md` and this file are also target rows of the mdqmcp010 plan; the Plan's
  dependency bullets order this Plan before it, so the overlap is compatible.

## Design decisions
- The fixture applies the canonical statements to the test database instead of writing a plain-table
  `CREATE TABLE`, so the fixture and the canonical source cannot drift.
- Readiness is asserted on the aligned fixture, which is the assertion AC-1 requires; the existing
  `details` assertions are not rewritten.

## Alternatives considered
- Keep the plain-table fixture and assert the refusal instead: rejected, because the file's purpose is
  the health fields, and a fixture that cannot pass readiness would make the readiness outcome
  accidental rather than pinned.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_health.py`

### Procedure
- Replace the plain-table `CREATE TABLE chunks_fts` statement in `_create_test_db` (line 60, with the
  `chunks_fts` column at line 68) with the canonical FTS5 definition read from
  `scripts/shared/mdq_schema.py` (new) and executed on the fixture connection.
- Add the readiness assertion for the aligned fixture in each test that already reads the response
  body, so the fixture is pinned as definition-compliant.

### Method
- The fixture keeps its current shape for `documents`, `chunks`, and `index_state`; only the FTS5 table
  form changes, so the trigger stubs and the existing `details` assertions stay valid.

### Details
- The trigger stubs the fixture creates are replaced by the canonical trigger statements, which is what
  makes the fixture pass the trigger-SQL comparison as well.

## Compatibility considerations
- The four tests assert `details` keys only, so the response shape is unchanged; the added readiness
  assertion is new coverage, not a change to an existing assertion.

## Security considerations
- N/A: test fixture only; no path, permission, or secret handling.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_health.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The fixture builds the real FTS5 definition and readiness reports ready for it (AC-1); the existing
  `details` assertions still pass.

## Out of Scope
- The readiness implementation (row 4); the definition comparison (row 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 1 |
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
- **Requirement ID**: REQ-001 (readiness compares the stored FTS5 definition)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_health.py`
