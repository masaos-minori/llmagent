## Goal
- Carry session, request, and logical-call identifiers in delete audit records via the shared audit-record contract (REQ-005, audit identifiers).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `_emit_call_tool_audit()` — `extract_request_context(request)[:2]` at line 194 drops the third element (the logical-call id); the companion test updates.
- Out of scope: the service-layer audit order and fail-closed behavior (seq 09).

## Assumptions
- Verified in Step 3a: `extract_request_context()` in `scripts/mcp_servers/server.py` (line 263) returns `(session_id, request_id, logical_call_id)`; the delete server slices only the first two (the Plan cited line 196; corrected to 194).
- `_audit_log_safe` (lines 178-185) swallows audit failures; per REQ-005 the server layer must surface audit failure as `applied_audit_failed` rather than counting it silently.

## Design decisions
- Use all three elements of `extract_request_context()` so the audit record matches the shared audit-record contract already pinned by the companion test for the write server.
- Audit failure at the server layer maps to the `applied_audit_failed` outcome from `scripts/shared/write_outcome.py`; the swallow-and-count behavior is replaced for call_tool audit records.

## Alternatives considered
- Keeping the local failure counter — rejected: REQ-005 requires the failure to be observable in the outcome.

## Implementation
### Target file
`scripts/mcp_servers/file/delete_server.py`

### Procedure
1. Change `extract_request_context(request)[:2]` (line 194) to unpack all three identifiers and pass the logical-call id to `_audit_log`.
2. On audit failure in the call_tool path, report the `applied_audit_failed` outcome instead of only incrementing `_audit_failure_count`.

### Method
- The shared audit-record record shape (session_id, request_id, and the logical-call field) follows the contract the companion test already asserts for write; delete is brought to parity.

### Details
- The companion test's helper compares `request_id` with the `X-Request-Id` response header because the auth middleware stores the generated id on `request.state`; the logical-call assertion extends the same helper.

### Companion test files
- `tests/mcp_servers/file/test_file_server_audit_records.py`
  - Procedure: assert the logical-call id in the delete call_tool audit record and the `applied_audit_failed` outcome when the audit write fails; extend the helper at lines 90-93.
  - Validation: the delete audit record carries all three identifiers; audit failure surfaces in the outcome.

## Compatibility considerations
- Audit consumers gain the logical-call field; existing session/request fields are unchanged.

## Security considerations
- N/A: no secrets; the change closes an audit-completeness gap.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Companion tests: assert the logical-call id in the delete call_tool audit record and the `applied_audit_failed` outcome when the audit write fails.
- `uv run pytest tests/mcp_servers/file/test_file_server_audit_records.py -v`; full `rules/toolchain.md` sequence.

## Completion criteria
- Delete audit records carry all three identifiers; audit failure surfaces as `applied_audit_failed`; tests pass (AC-4).

## Out of Scope
- Service-layer audit order and fail-closed intent audit (seq 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-005` (audit identifiers and observable audit failure)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/delete_server.py`, `tests/mcp_servers/file/test_file_server_audit_records.py`
