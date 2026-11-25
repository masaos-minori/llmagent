## Goal

Convert an applied-audit failure into the explicit applied_audit_failed result, bind the call identity for the audit records, and report the audit-failure count in `/health` (REQ-005, REQ-006, REQ-008).

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- The context Plan's procedures change `_dispatch_github_tool` to take an execution context and are executed first (Plan UNK-01); this document re-reads that function at execution time and adds to it.
- The dispatcher records a terminal `failed` row when the handler raises, so the applied write can never be replayed; the wrapper only changes what the caller sees.

## Design decisions

- `_dispatch_github_tool` binds the call identity (session, request, key) around `dispatch_tool`, catches `GitHubAppliedAuditError`, and returns an error `DispatchResult` with `error_type="applied_audit_failed"` whose text states the write was applied and must not be retried.
- Health: the details dict gains the audit-failure count read from the service.

## Alternatives considered

Letting the exception reach the global handler was rejected: it would hide that the write was applied behind a bare 500.

## Implementation
### Target file
`scripts/mcp_servers/github/github_server.py`

### Procedure
Wrap the dispatch call, bind the identity, and extend the health details.

### Method
- Import `bind_call_identity` from the security module and `GitHubAppliedAuditError` from the models config.
- In `_dispatch_github_tool`, run `dispatch_tool` inside `bind_call_identity(...)` with the session id, request id, and key taken from the request context; catch `GitHubAppliedAuditError` and return `DispatchResult(output=..., is_error=True, error_type="applied_audit_failed")`.
- Make `call_tool` pass the session and request ids it already extracts into the wrapper.
- In `/health`, add `audit_failure_count` from `_service` to the `details` mapping.

### Details
- The output text names the operation and says applied_audit_failed; it never echoes arguments.

## Compatibility considerations

The programmatic `dispatch` override keeps working: it passes no request ids, so its records show `-` for them.

## Security considerations

Prevents a duplicate manual retry after an applied write whose audit failed.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_write_outcomes.py tests/mcp_servers/github/test_github_server_endpoints.py`
- `uv run mypy scripts/mcp_servers/github/github_server.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- An applied write with a failed completion audit returns applied_audit_failed.
- `/health` shows the audit-failure count.

## Out of Scope

- Exception-handler mapping.
- Dedup behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-005, REQ-006, REQ-008
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `scripts/mcp_servers/github/github_server.py`
