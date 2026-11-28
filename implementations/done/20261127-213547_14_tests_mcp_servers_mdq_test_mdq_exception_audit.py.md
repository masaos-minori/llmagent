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
- Step 3b correction (20261128): the sink is the server module's `logger` replaced with a recorder, and non-record info lines are skipped, because `call_tool()` also logs a non-JSON `fmt_kvlog` line; counting every info call would count that line as a record.
- Step 3b correction (20261128): the `ExecutionContextError` trigger is a header claim that disagrees with the resolved mode — `X-Execution-Mode: preview` for `search_docs`, which resolves to `applied` (`scripts/mcp_servers/execution_context.py` lines 111-118). A claim equal to the resolved mode raises nothing.

### Details
- The refused-tool path must also emit exactly one record, so the refusal is covered by the same counting assertion.
- Step 3b correction (20261128): the count assertion alone passes for the wrong reason today, because no refusal happens at all and the executed handler emits one record. The test also asserts `is_error=true`, which is what makes the missing refusal observable. The refusal itself (code `tool_disabled`, `outcome` `rejected`) is pinned by seq 13, so this file does not restate it.
- Step 3b correction (20261128): "the tests fail first because the module emits from two sites" is not a per-call observation. Per call only one site executes today, so 8 of the 10 tests already pass and serve as the behavior lock; the failures today are the two paths that emit nothing — the malformed-execution-context path and the refused-tool path. The handler-emission assertion is seq 01's companion's, not this file's.
- Step 3b correction: the transport statuses asserted per class are the ones the handlers return today (`mdq_server.py` lines 139-190): 400 validation, 403 authorization, 404 not found, 503 index-not-ready, 503 database, 500 consistency, 500 service. The four classes caught inside `call_tool()` stay tool-level with HTTP 200, so the test branches on that.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261128 | 20261128 | `tests/mcp_servers/mdq/test_mdq_exception_audit.py` created (10 tests: success, 7 error classes, malformed context, refusal) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-093658 | 20261128-093658 | Targeted run 20261128: 2 failed as designed (the paths that emit nothing today), 8 passed as the behavior lock. ruff format/check Pass. Validation completes at the end of the release unit, after seq 01 lands end-of-unit gate 20261128 as recorded in seq 01's gates row; the two failing-first assertions pass after seq 01 landed |

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