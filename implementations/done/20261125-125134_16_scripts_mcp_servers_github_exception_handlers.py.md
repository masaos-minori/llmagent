## Goal

Map the ambiguous-outcome error to an explicit HTTP 504 and name the outcome in the audit-error bodies (REQ-003).

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- Status 502, 503, and 504 on a write are treated by the Agent transport as an ambiguous outcome and are never retried for write tools, so 504 reaches `outcome_unknown` on the Agent side.
- The new error classes exist after the config-models document (earlier `seq`).

## Design decisions

- The 504 body is `{"detail": ..., "outcome": "outcome_unknown"}`; the audit handler adds `"outcome": "audit_failed"` for a pre-write failure and keeps 500.

## Alternatives considered

Using 502 was rejected: it is also returned for definite upstream failures, so it cannot carry the no-retry meaning.

## Implementation
### Target file
`scripts/mcp_servers/github/exception_handlers.py`

### Procedure
Register a handler for `GitHubOutcomeUnknownError` and extend the audit handler's body.

### Method
- Import `GitHubOutcomeUnknownError`.
- Add an exception handler returning `JSONResponse(status_code=504, content={...})` with the outcome field.
- Add the `outcome` field to `_handle_audit`'s content.

### Details
- Keep every other handler unchanged.

### Companion test files
- `tests/mcp_servers/github/test_github_exception_handlers.py`
  - Procedure: Add a 504 case for GitHubOutcomeUnknownError asserting the outcome field, and extend the audit case to assert its outcome field.
  - Validation: `uv run pytest tests/mcp_servers/github/test_github_exception_handlers.py`

## Compatibility considerations

Additive body field; status codes of existing errors unchanged.

## Security considerations

The body names the outcome and never echoes arguments.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_exception_handlers.py`
- `uv run mypy scripts/mcp_servers/github/exception_handlers.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- An ambiguous write failure returns 504 with `outcome_unknown`.

## Out of Scope

- Raising the errors (service documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-185946 | 20261125-185946 | changed: exception_handlers.py (504 handler + outcome field in the audit body); note: GitHubAppliedAuditError is a GitHubAuditError subclass but the dispatcher converts it before the handler, so the audit body stays audit_failed |
| 2 | Add or update tests per Validation plan | Completed | 20261125-185946 | 20261125-185946 | 504 case added, audit case extended for the outcome field |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-185946 | 20261125-185946 | ruff/mypy/bandit/lint-imports pass; 7 tests pass, tests/mcp_servers/github 595 passed |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `scripts/mcp_servers/github/exception_handlers.py`, `tests/mcp_servers/github/test_github_exception_handlers.py`