## Goal
- Validate the shared auth_token in the web-search middleware wiring (`REQ-001, REQ-003`)

## Scope
- The single call of `attach_auth_middleware` in `scripts/mcp_servers/web_search/web_search_server.py`.

## Assumptions
- Procedure 02 has added the auth_token field to the config.
- The loopback health opt-in added by mcp004 stays.

## Design decisions
- Change only the token argument; keep the opt-in keyword and the surrounding code.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure
1. In the existing `attach_auth_middleware` call, replace the browser token argument with the auth_token field of the module's config object, keeping the empty-string fallback expression.

### Method
- A one-argument edit; keep the repository formatter's layout.

### Details
- Do not touch the health endpoint, the exception handlers, or the opt-in keyword.

## Compatibility considerations
Protected routes now require the shared token the agent sends; the health path from a loopback client is still admitted.

## Security considerations
Authentication now matches the credential the agent presents; every other route and a non-loopback health request still require the token.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search -q`, including the real-application test from procedure 07.
- `uv run ruff format --check`, `uv run ruff check`, `uv run mypy --no-namespace-packages` on the file.
- Execution order for the whole plan: tests first (procedures 05, 06, 07, 08, 09, 04), then the code (01, 02, 03), then the documentation (10 to 15); the new tests must be seen failing before the code is edited.

## Completion criteria
- The call uses the shared token and the web-search tests pass.

## Out of scope
- The middleware itself and the other servers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pass the shared token to the middleware | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: scripts/mcp_servers/web_search/web_search_server.py (middleware validates auth_token) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-184531 | 20261012-184531 | tests/mcp_servers and tests/agent: 5118 passed; real-app reproduction: tools and call_tool 200 with the shared token, 401 with another; not deployed |

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
- **Requirement ID**: `REQ-001, REQ-003`
- **Source issue**: issues/done/20261012-182600_mcp005_web-search-tool-calls-return-401-when-browser_auth_token-differs-from-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183712
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py