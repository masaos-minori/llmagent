## Goal

Create the outcome test module for GitHub writes (REQ-009): store failure, intent and completion audit failure, timeouts, no-retry, and client construction.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Stub services and a fake API object are used; no network. The durable-store failure uses the injection style of `tests/mcp_servers/test_mcp_dispatch_concurrency.py` (a store whose acquisition raises), copied locally.

## Design decisions

- Test-only change; behavior under test is defined by the code documents of the release unit.

## Alternatives considered

N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_write_outcomes.py` (new)

### Procedure
Create the module with six groups of cases.

### Method
- Store failure: for each of the nine writes, with the store unavailable the dispatcher refuses the call (`dedup_store_error`) and the API stub is not called.
- Intent audit: with an unwritable audit path a write raises `GitHubAuditError` and the API stub is not called.
- Applied audit failure: the API stub succeeds and the completion audit fails for issue create, comment, merge, and file update; the result is applied_audit_failed, mentions the write was applied, and the counter increments.
- Timeouts: a read timeout, a connection error, and an upstream 5xx during a write raise `GitHubOutcomeUnknownError`; a second dispatch with the same key does not call the API again.
- Identifiers: audit records contain the session, request, and call ids and no payload text.
- Client: patch the PyGithub constructor and assert it receives the configured timeout tuple and `retry=None`; `/health` reports the counter.

### Details
- Follow the existing fixture style of the file.

## Compatibility considerations

Test-only.

## Security considerations

N/A: test code.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_github_write_outcomes.py`
- `uv run ruff check`, `uv run ruff format`, `uv run mypy tests/mcp_servers/github/test_github_write_outcomes.py`

## Completion criteria

- Every group passes after the release unit lands.

## Out of Scope

- Production code (other documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test file described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-008, REQ-009
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `tests/mcp_servers/github/test_github_write_outcomes.py`
