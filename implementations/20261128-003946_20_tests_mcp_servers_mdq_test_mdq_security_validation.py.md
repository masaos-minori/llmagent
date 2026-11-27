# Implementation Procedure — tests/mcp_servers/mdq/test_mdq_security_validation.py

## Goal

Move the empty-FTS-index assertion from WARNING to FAILED, since only FAILED blocks Ready (REQ-005,
AC-4).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-005 (an unexpectedly empty FTS index is not ready). Acceptance criterion: AC-4.

## Assumptions
- Full form: this row is the assertion that pins the current outcome, so its change is the record of the
  new contract rather than a mechanical fix of a broken test.
- The status change itself is implemented by row 5 (`scripts/mcp_servers/mdq/mdq_security_validation.py`);
  this document changes only the test file.
- `scripts/shared/security/result_dto.py` line 98 states that only FAILED blocks Ready, so the assertion
  change is what pins AC-4.
- The reason code stays `REASON_DEPENDENCY_UNREACHABLE`, which is already in the closed vocabulary, so no
  code is added.

## Design decisions
- The test name `test_empty_index_over_documents_is_a_warning` (line 275) no longer describes the
  outcome, so it is renamed to `test_empty_index_over_documents_is_not_ready` (new).
- The reason-code assertion is kept, so the pin covers both the status and the code.

## Alternatives considered
- Keep the name and change only the assertion: rejected, because the name would state an outcome the
  check no longer produces.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_security_validation.py`

### Procedure
- Change the assertion at line 279 from `SecurityCheckStatus.WARNING` to `SecurityCheckStatus.FAILED` and
  rename the test as stated in Design decisions.
- Keep the check-id tuple entry at line 51, the `NOT_APPLICABLE` case (lines 271-273), and the OK cases at
  lines 282-285 and 287-290.

### Method
- The fixture stats (`EMPTY_INDEX_STATS`) are unchanged, so only the expected status changes.

### Details
- No message assertion exists in this file for the check, so nothing else changes.

## Compatibility considerations
- The other checks in the file assert OK or NOT_APPLICABLE and are unaffected.

## Security considerations
- N/A: test file only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_security_validation.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The empty-index-over-rows case asserts FAILED (AC-4); the not-applicable and OK cases still pass.

## Out of Scope
- The status change in the check itself (row 5); the bind-gate case, which is in
  `tests/mcp_servers/mdq/test_mdq_health_posture.py` (row 13, companion of row 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Phase 5 |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document is the test row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: the condition is documented by row 15 |

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
- **Requirement ID**: REQ-005 (an unexpectedly empty FTS index is not ready)
- **Source issue**: `issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-172305_mdqmcp006_mdq-fts5-schema-identity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-003946
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_security_validation.py`
