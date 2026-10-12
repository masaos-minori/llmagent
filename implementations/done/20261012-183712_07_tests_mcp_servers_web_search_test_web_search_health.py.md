## Goal
- Add a real-application test with a configured shared token and update the wiring test (`REQ-001, REQ-003, REQ-004`)

## Scope
- `TestHealthExemptionOptIn` and a new test class in `tests/mcp_servers/web_search/test_web_search_health.py`.

## Assumptions
- The real application reads its token from the configuration at import time, so the real-application test runs a separate interpreter with the environment variable set.
- The interpreter needs the scripts directory on its import path; the test passes it through the environment.
- `browser_fetch` is disabled when the allowlist is empty, so a call to it returns a disabled-tool result without any network access.

## Design decisions
- Use the standard `subprocess` module with the current interpreter, a short script, and a timeout; the script prints one JSON object of status codes.
- Add an AST check that the server passes the shared token (an attribute named auth_token of the config object, with the empty fallback) next to the existing opt-in check.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/mcp_servers/web_search/test_web_search_health.py`

### Procedure
1. Add a new test class whose test builds a script string that imports the web-search server module, wraps its application in the framework test client with a loopback client address, and requests the tools route with the shared token, with no token, and with another token, requests the health route with no token, and posts a call to the disabled browser tool with the shared token; the script prints the status codes as JSON.
2. Run the script with `subprocess.run` using the current interpreter, an environment copied from the test's environment plus the variable MCP_WEB_SEARCH_AUTH_TOKEN set to a fixed test value and PYTHONPATH set to the repository's scripts directory, capturing output with a timeout of 60 seconds; parse the JSON.
3. Assert: the tools route returns 200 with the shared token and 401 with no token and with another token; the health route returns 200 without a token (loopback); the call with the shared token returns 200.
4. In the wiring class, add test_web_search_server_uses_the_shared_token: parse the server file as the existing test does and assert the second argument of its middleware call is an or-expression whose first operand is an attribute named auth_token.
5. Run the new tests against the unmodified code and confirm the real-application test and the wiring test fail before procedures 01 to 03.

### Method
- Reuse the module's existing path constants and helpers; keep the new test self-contained.

### Details
- Do not print or log the token value on failure beyond the status codes.
- Do not modify existing tests.

## Compatibility considerations
Test-only change.

## Security considerations
Uses fixed dummy test tokens only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_health.py -q`; `uv run ruff format --check tests/mcp_servers/web_search/test_web_search_health.py` and `uv run ruff check tests/mcp_servers/web_search/test_web_search_health.py`.
- Confirm the new tests fail before procedures 01 to 03 and pass after.
- Execution order for the whole plan: tests first (procedures 05, 06, 07, 08, 09, 04), then the code (01, 02, 03), then the documentation (10 to 15); the new tests must be seen failing before the code is edited.

## Completion criteria
- The real-application test and the wiring test fail before the code change and pass after it; existing tests pass.

## Out of scope
- Other test files and the shared middleware tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the real-application test and the wiring assertion | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: tests/mcp_servers/web_search/test_web_search_health.py (TestRealAppSharedToken via a separate interpreter, wiring test for the shared token); both failed before the code change (token-less calls returned 200) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-184531 | 20261012-184531 | ruff pass; file passes |

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
- **Requirement ID**: `REQ-001, REQ-003, REQ-004`
- **Source issue**: issues/done/20261012-182600_mcp005_web-search-tool-calls-return-401-when-browser_auth_token-differs-from-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183712
- **Related target files**: tests/mcp_servers/web_search/test_web_search_health.py