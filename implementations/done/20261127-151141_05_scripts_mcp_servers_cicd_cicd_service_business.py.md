# Implementation Procedure — scripts/mcp_servers/cicd/cicd_service_business.py

## Goal

Return the serialized structured log result from `handle_get_workflow_logs` and return a tool error
when every job failed.

## Scope
**Release unit**: structured log result contract

Requirement implemented: REQ-004 (complete, partial, and total failure are machine-distinguishable; the
all-failed case is a tool error). Acceptance criterion: AC-4.

## Assumptions
- The handler contract stays `-> str` with the result JSON-serialized, so `dispatch_tool` and the audit
  `outcome` mapping are unchanged (Plan Assumption, `scripts/mcp_servers/dispatch.py` reference).
- The existing error-to-HTTP mapping must not change
  (`scripts/mcp_servers/cicd/exception_handlers.py`, reference — the Plan's reference row cites
  `scripts/mcp_servers/exception_handlers.py`, which does not exist; re-verified 20261127); the
  all-failed case is reported as a tool error through the existing path.
- The `trigger_workflow` handler in the same file is the mcpci002 pass's work; this document changes the
  log handler only (Plan Assumption, compatible overlap).

## Design decisions
- The all-failed branch is decided from the per-job statuses in the result, not from text inspection.
- The all-failed tool error is raised as `CicdUpstreamError` (mapped to 502 by
  `scripts/mcp_servers/cicd/exception_handlers.py`), decided by the user on 20261127: per-job failure
  is an upstream failure, and `CicdNotFoundError` would not distinguish "run not found" from "every
  job failed". No new exception type and no mapping change.

## Alternatives considered
- Returning a successful result with an empty job list: rejected per REQ-004 — total failure must be a
  tool error, distinct from a partial result.

## Implementation
### Target file
`scripts/mcp_servers/cicd/cicd_service_business.py`

### Procedure
- Change `handle_get_workflow_logs` (lines 156-168) to return the JSON-serialized structured result.
- Add the all-failed branch: when every job failed, raise `CicdUpstreamError` so the tool error is
  returned through the existing error path instead of a successful result.

### Method
- Lines 156-168 currently return the backend string unchanged with no all-failed branch
  (re-verified 20261127 against the current file; the Plan's citation of 120-132 predates the
  mcpci001 pass); keep `_validate_and_parse_repo()` and the request construction unchanged.
  Serialization follows the same `_json_dumps` pattern the mcpci002 pass introduced for
  `handle_trigger_workflow` in this file.

### Details
- Raw transport exception text never appears in the result (REQ-004).

### Companion test files
- `tests/mcp_servers/cicd/test_cicd_mcp_service.py`
  - Procedure: replace the overrun-allowing assertion at line 706 (`len(result.encode()) <= 1024 + 100`;
    the Plan's citation of line 525 predates the mcpci001 pass, re-verified 20261127) with the exact
    byte budget; replace the string-return pin at line 309
    (`backend.get_workflow_logs.return_value = "=== Job: build ==="`, which pins the handler passing
    the backend string through) with the structured result and its JSON serialization; and add the
    UTF-8-boundary, mixed-failure, and all-failed cases.
  - Validation: `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py`.

## Compatibility considerations
- The dispatch-table wiring for `get_workflow_logs` is unchanged
  (`tests/mcp_servers/cicd/test_cicd_server_endpoints.py`, reference).

## Security considerations
- No token and no raw upstream text in the result (REQ-006).

## Rollback considerations
- N/A: revert the commit (release unit: validated with the Protocol, backend, and facade rows).

## Validation plan
- Unit: handler, mixed and all-failed cases — `uv run pytest tests/mcp_servers/cicd/test_cicd_mcp_service.py`.
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Complete, partial, and total failure are machine-distinguishable and no raw exception string appears
  (AC-4); the exact byte budget is asserted.

## Out of Scope
- The response model (`cicd_models.py` row); the streaming bounds
  (`cicd_service_github_actions_job.py` row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | handler JSON-serializes the result; all-failed raises CicdUpstreamError (502 mapping unchanged) |
| 2 | Add or update tests per Validation plan (companion test file) | Completed | — | — | pins at lines 309 and 706 replaced; mixed, all-failed, and redaction cases added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy Pass; test_cicd_mcp_service.py passes |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | documentation is covered by the Plan's docs row |

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
- **Requirement ID**: REQ-004 (structured log result from the handler, all-failed tool error)
- **Source issue**: issues/20261119-141110_mcpci003_cicd-log-streaming-bounds.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-065519_mcpci003_cicd-log-streaming-bounds.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-151141
- **Related target files**: `scripts/mcp_servers/cicd/cicd_service_business.py`, `tests/mcp_servers/cicd/test_cicd_mcp_service.py`