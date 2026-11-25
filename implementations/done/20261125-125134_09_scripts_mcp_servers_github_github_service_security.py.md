## Goal

Provide the shared write plumbing: the intent audit, the completion audit that reports applied_audit_failed, the ambiguous-failure translation for writes, the call identity, and the audit-failure counter (REQ-003 to REQ-006, REQ-008).

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- `_write_github_audit_log` stays the single record writer; the two new helpers wrap it and add the phase and identifiers.
- `_run_github` is also used by reads, so the translation applies only when the caller passes `write=True`.
- The service is one object per process, so a plain integer counter on the instance is sufficient; thread safety is not needed because audits run on the event loop thread.
- Code docstrings and comments must not carry REQ markers (the repository checks that); cite behavior, not Plan ids.

## Design decisions

- The intent audit raises `GitHubAuditError` before the API call (fail closed, nothing applied). The completion audit converts a failure into `GitHubAppliedAuditError`, increments `audit_failure_count` (new), and chains the cause.
- Ambiguous failures of a write become `GitHubOutcomeUnknownError`: `requests` timeouts and connection errors, urllib3 errors, `TimeoutError`, and a `GithubException` with status 500 or above; definite 4xx outcomes keep their existing mapping.
- Adversarial verification finding (20261125): `requests` is not a declared project dependency (PyGithub brings it in transitively), so the translation must not import `requests`. Verified against the installed packages: `requests.RequestException` and its timeout/connection subclasses are `OSError` subclasses, and requests wraps urllib3 errors into `RequestException`, so catching `OSError` plus `TimeoutError` covers the listed ambiguous transport failures without a direct `requests` import.

## Alternatives considered

Translating inside every service method was rejected: one place in `_run_github` covers all nine writes.

## Implementation
### Target file
`scripts/mcp_servers/github/github_service_security.py`

### Procedure
Add the call-identity context variable and helpers, extend `_write_github_audit_log` with the identifiers, add the write flag to `_run_github`, and add the counter.

### Method
- Add a `ContextVar` holding `(session_id, request_id, call_id)` and `bind_call_identity` (new) as a context manager that sets and resets it.
- Extend `_write_github_audit_log` to prepend the fields from `build_write_audit_fields` (phase and identifiers) to the record; no payload field is added.
- Add `_write_intent_audit` (new) taking `(op, **fields)`: writes a record with phase `intent`; a `GitHubAuditError` propagates.
- Add `_complete_write_audit` (new) taking `(op, **fields)`: writes phase `completion`; on `GitHubAuditError` increment audit_failure_count (new, an instance integer initialised to 0) and raise `GitHubAppliedAuditError` from it.
- Add a keyword `write: bool = False` to `_run_github`; when true, translate the ambiguous failures listed in Design to `GitHubOutcomeUnknownError`, otherwise behave as today.

### Details
- Do not log argument values or titles in the new records.
- An empty `audit_log_path` keeps the documented skip for both phases.

## Compatibility considerations

`_write_github_audit_log` keeps its signature; callers that pass extra keyword fields keep working.

## Security considerations

Fail-closed intent audit and a typed applied-audit outcome prevent both silent unaudited writes and duplicate retries after an applied write.

## Rollback considerations

Revert the release unit together.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_mcp_service.py tests/mcp_servers/github/test_service_security.py tests/mcp_servers/github/test_github_write_outcomes.py`
- `uv run mypy scripts/mcp_servers/github/github_service_security.py`
- `uv run ruff check`, `uv run ruff format`, `uv run bandit scripts/mcp_servers/github/github_service_security.py -c pyproject.toml`

## Completion criteria

- The two audit helpers, the identity binding, the write flag, and the counter exist.
- A write timeout raises `GitHubOutcomeUnknownError`; a failed completion audit raises `GitHubAppliedAuditError`.

## Out of Scope

- Calling the helpers from the write methods (their own documents).
- Handler and health wiring (server documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-184522 | 20261125-184522 | changed: github_service_security.py; adversarial finding applied: ambiguous failures caught as OSError/TimeoutError without importing requests (requests is not a declared dependency); direct calls without phase default to intent |
| 2 | Add or update tests per Validation plan | Completed | 20261125-184522 | 20261125-184522 | added tests/mcp_servers/github/test_github_write_outcomes.py (14 tests) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-184522 | 20261125-184522 | ruff/mypy/bandit/lint-imports pass; 120 targeted tests pass module size: 24548 B, under the 24576 gate after trimming the added docstrings/comments |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-005, REQ-006, REQ-008
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `scripts/mcp_servers/github/github_service_security.py`