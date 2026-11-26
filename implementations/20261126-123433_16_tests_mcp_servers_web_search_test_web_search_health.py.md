## Goal
- Pin that rejected calls (disabled tool, envelope validation error, validation error, authorization error) leave the search and browser health counters unchanged (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `tests/mcp_servers/web_search/test_web_search_health.py`.
- Out of scope: the audit assertions (the server companions) and any change to `health.py`.

## Assumptions
- No code row of the Plan names this test in its Related Tests, so it keeps its own document.
- Implemented after the server procedure (seq 07), which moves the disabled gate and adds the envelope handler.
- Verified in Step 3a: health is recorded only in the service (`web_search_service.py`), and validation and authorization failures are metrics-only; no test currently pins health isolation for the disabled and envelope paths.

## Design decisions
- Drive the real ASGI app with an authenticated test client, and compare `health.health_details()` and `health.browser_health_details()` before and after each rejected call.

## Alternatives considered
- N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/web_search/test_web_search_health.py`

### Procedure
1. Add a test class for rejection isolation using the existing health reset helper and the authenticated client headers used by the other web search server tests.
2. Cases: a disabled `browser_fetch` call (empty allowlist), a malformed `/v1/call_tool` body, a `search_web` call with an invalid argument, and a `browser_fetch` call to a non-allowlisted host; for each, assert the consecutive-failure counters and last error type of both singletons are unchanged and no degraded dependency appears in `/health`.

### Method
- Reset the health singletons before each case and read both detail dicts directly.

### Details
- Keep every existing health test unchanged.

## Compatibility considerations
- Test-only.

## Security considerations
- N/A: no secrets involved; tests use the test authorization header only.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_health.py`; `uv run ruff format` and `uv run ruff check` on the file; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- All four rejection cases leave both health states unchanged; existing tests pass; all validation commands pass.

## Out of Scope
- Audit assertions, `health.py` changes, and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the tests described in Implementation > Procedure | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (rejected calls do not change health counts)
- **Source issue**: issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-114838_mcpws002_websearch-config-audit-redaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-123433
- **Related target files**: `tests/mcp_servers/web_search/test_web_search_health.py`
