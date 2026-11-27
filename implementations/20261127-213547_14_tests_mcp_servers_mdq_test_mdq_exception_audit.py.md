## Goal

Create the exactly-one-audit tests for success and for every error class, including the `ExecutionContextError` path that emits nothing today (REQ-005 single audit boundary).

## Scope
**Release unit**: boundary-characterization-tests (Plan step 1 cites this row; the unit covers Phases 1, 3, 4, 5, 6)

## Assumptions
- This row keeps its own document because the counting method is a test-design decision of its own: the assertion is one record per authenticated call, which no code row's document defines.
- Written in Phase 1 before the production change; the tests fail first because `scripts/mcp_servers/mdq/mdq_server.py` emits from two sites (lines 426 and 444) and from the handler (line 125).
- `tests/mcp_servers/_auth_headers.py` is the HTTP fixture reused here; it is not a target row.

## Design decisions
- The test counts emitted records rather than asserting a call to `_audit_log()`, so the single `AuditEmission` boundary in seq 01 is what is verified.
- Every error class in the plan's Tests section is covered, including the malformed-execution-context path.

## Alternatives considered
- N/A: the row is a test file.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_exception_audit.py` (new)

### Procedure
- Add a success-path test asserting exactly one record.
- Add one test per error class: validation, authorization, not found, index not ready, database, consistency, service.
- Add the `ExecutionContextError` case, which emits nothing today.

### Method
- Records are read from the audit sink the emission boundary writes to, not from a patched `_audit_log()` mock, so the double-emission is observable.

### Details
- The refused-tool path must also emit exactly one record, so the refusal is covered by the same counting assertion.

## Compatibility considerations
- `tests/mcp_servers/mdq/test_mdq_exception_handlers.py` (companion of seq 01) asserts the handler no longer emits; the two files must not duplicate the same assertion.

## Security considerations
- N/A: redaction assertions are in seq 15.

## Rollback considerations
- N/A: revert the commit; the file stays as the characterization record.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_exception_audit.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Every authenticated call emits exactly one audit record, including the malformed-execution-context path (AC-3).

## Out of Scope
- The emission boundary implementation (seq 01) and the redacted target values (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-005 (exactly one audit record per authenticated call)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142123_mdqmcp001_mdq-server-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-213547
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_exception_audit.py`
