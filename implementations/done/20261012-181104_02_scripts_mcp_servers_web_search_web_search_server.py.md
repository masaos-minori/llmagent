## Goal
- Opt the web-search server in to the loopback health admission so its startup health poll succeeds when the browser token differs from the main token (`REQ-001`, `REQ-004`).

## Scope
- The single call of `attach_auth_middleware` in `scripts/mcp_servers/web_search/web_search_server.py`. Nothing else in the file changes.

## Assumptions
- Procedure 01 has added the keyword-only parameter exempt_health_on_loopback (new) to `attach_auth_middleware`.
- The browser allowlist and the authorization handling are independent of the middleware and stay untouched.

## Design decisions
- Pass the switch as an explicit keyword argument at the one call site; do not change which token the middleware validates (the browser token stays).

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_server.py`

### Procedure
1. After procedure 01 is applied, add the keyword argument exempt_health_on_loopback set to true to the existing `attach_auth_middleware` call that passes the browser token, keeping the first two arguments as they are.

### Method
- A one-argument edit; keep the call formatted by the repository formatter.

### Details
- Do not touch the health endpoint, the exception handlers, or `_cfg`.

## Compatibility considerations
- Only the health path from a loopback client is affected; every other endpoint still requires the browser token.

## Security considerations
- See procedure 01: the admission is limited to loopback clients on the exact health path.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/ -q` (the opt-in test from procedure 04 reads this call).
- `uv run ruff format --check scripts/mcp_servers/web_search/web_search_server.py`, `uv run ruff check` and `uv run mypy` on the same file.
- Execution order for the whole plan: procedures 03 and 04 (tests) first, then 01 and 02 (code), then 05 and 06 (documentation); the new tests must be seen failing before the code is edited.

## Completion criteria
- The call passes the switch as true and the web-search tests pass.

## Out of scope
- The middleware itself, the other servers, and the tool-call authentication gap.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pass the opt-in switch from the web-search server | Completed | 20261012-182000 | 20261012-182000 | stale_detector clean; changed: scripts/mcp_servers/web_search/web_search_server.py (attach_auth_middleware call passes exempt_health_on_loopback=True) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-182000 | 20261012-182000 | ruff, mypy, bandit pass; AST opt-in test passes; not deployed |

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
- **Requirement ID**: `REQ-001`, `REQ-004`
- **Source issue**: issues/done/20261012-173750_mcp004_web_search-mcp-server-startup-health-check-fails-due-to-browser_auth_token-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-175600_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-181104
- **Related target files**: scripts/mcp_servers/web_search/web_search_server.py